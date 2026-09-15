from __future__ import annotations

import torch
from torch import nn


class GraphConstructionCortex(nn.Module):
    """CPU-realistic Russian -> graph slot construction cortex.

    Exact argument positions remain on the original character lattice. A
    stride-4 semantic compressor feeds a two-layer bidirectional GRU for
    relation reasoning; SUBJECT/OBJECT slots score bounded candidate spans.
    """

    def __init__(
        self,
        vocab_size: int,
        relation_count: int,
        char_dim: int = 24,
        hidden: int = 32,
        slot_dim: int = 80,
        morph_dim: int = 8,
        refine_steps: int = 2,
    ) -> None:
        super().__init__()
        self.config = dict(
            vocab_size=vocab_size,
            relation_count=relation_count,
            char_dim=char_dim,
            hidden=hidden,
            slot_dim=slot_dim,
            morph_dim=morph_dim,
            refine_steps=refine_steps,
        )
        self.emb = nn.Embedding(vocab_size, char_dim, padding_idx=0)
        self.morph = nn.Linear(6, morph_dim)
        local_dim = char_dim + morph_dim
        self.local_proj = nn.Linear(local_dim, slot_dim)
        self.compress = nn.Conv1d(local_dim, hidden, kernel_size=5, stride=4, padding=2)
        self.encoder = nn.GRU(
            hidden,
            hidden,
            num_layers=2,
            batch_first=True,
            bidirectional=True,
            dropout=0.1,
        )
        self.semantic_proj = nn.Linear(hidden * 2, slot_dim)

        self.subject_seed = nn.Parameter(torch.randn(slot_dim) * 0.02)
        self.object_seed = nn.Parameter(torch.randn(slot_dim) * 0.02)
        self.relation_seed = nn.Parameter(torch.randn(slot_dim) * 0.02)
        self.subj_cell = nn.GRUCell(slot_dim * 2, slot_dim)
        self.obj_cell = nn.GRUCell(slot_dim * 2, slot_dim)
        self.rel_cell = nn.GRUCell(slot_dim * 4, slot_dim)
        self.subj_q = nn.Linear(slot_dim, slot_dim, bias=False)
        self.obj_q = nn.Linear(slot_dim, slot_dim, bias=False)
        self.rel_head = nn.Sequential(
            nn.Linear(slot_dim * 4, slot_dim * 2),
            nn.GELU(),
            nn.Linear(slot_dim * 2, relation_count),
        )
        self.conf_head = nn.Linear(slot_dim * 2, 1)
        self.refine_steps = refine_steps

    @staticmethod
    def _masked_mean(x: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        weights = mask.to(x.dtype).unsqueeze(-1)
        return (x * weights).sum(1) / weights.sum(1).clamp_min(1.0)

    @staticmethod
    def _candidate_pool_prefix(
        enc: torch.Tensor, cands: torch.Tensor, cand_mask: torch.Tensor
    ) -> torch.Tensor:
        """Exact span means using prefix sums: O(B*C*D), not O(B*C*L*D)."""
        batch_size, length, dim = enc.shape
        prefix = torch.cat(
            [
                torch.zeros((batch_size, 1, dim), dtype=enc.dtype, device=enc.device),
                enc.cumsum(dim=1),
            ],
            dim=1,
        )
        starts = cands[:, :, 0].clamp(0, length)
        ends = cands[:, :, 1].clamp(0, length)
        batch = torch.arange(batch_size, device=enc.device).unsqueeze(1).expand_as(starts)
        sums = prefix[batch, ends] - prefix[batch, starts]
        widths = (ends - starts).clamp_min(1).to(enc.dtype).unsqueeze(-1)
        return (sums / widths) * cand_mask.to(enc.dtype).unsqueeze(-1)

    @staticmethod
    def _candidate_pool(enc, cands, cand_mask):
        return GraphConstructionCortex._candidate_pool_prefix(enc, cands, cand_mask)

    def _attend(self, slot, cand_repr, cand_mask, q_layer):
        query = q_layer(slot).unsqueeze(1)
        logits = (query * cand_repr).sum(-1) / (cand_repr.shape[-1] ** 0.5)
        logits = logits.masked_fill(~cand_mask, -1e4)
        attention = torch.softmax(logits, dim=-1)
        context = torch.einsum("bc,bcd->bd", attention, cand_repr)
        return context, logits

    def forward(self, tokens, mask, morph, candidates, candidate_mask):
        local = torch.cat([self.emb(tokens), torch.tanh(self.morph(morph))], dim=-1)
        local_slots = self.local_proj(local)

        compressed = torch.nn.functional.gelu(
            self.compress(local.transpose(1, 2))
        ).transpose(1, 2)
        compressed_mask = (
            torch.nn.functional.max_pool1d(
                mask.float().unsqueeze(1), kernel_size=5, stride=4, padding=2
            ).squeeze(1)
            > 0
        )
        semantic, _ = self.encoder(compressed)
        semantic = self.semantic_proj(semantic)
        global_ctx = self._masked_mean(semantic, compressed_mask)

        candidate_repr = self._candidate_pool_prefix(
            local_slots, candidates, candidate_mask
        )
        batch_size = tokens.shape[0]
        subject = self.subject_seed.unsqueeze(0).expand(batch_size, -1) + global_ctx
        obj = self.object_seed.unsqueeze(0).expand(batch_size, -1) + global_ctx
        relation = self.relation_seed.unsqueeze(0).expand(batch_size, -1) + global_ctx
        subject_ctx = object_ctx = global_ctx

        for _ in range(self.refine_steps):
            subject_ctx, _ = self._attend(subject, candidate_repr, candidate_mask, self.subj_q)
            object_ctx, _ = self._attend(obj, candidate_repr, candidate_mask, self.obj_q)
            subject = self.subj_cell(torch.cat([subject_ctx, relation], -1), subject)
            obj = self.obj_cell(torch.cat([object_ctx, relation], -1), obj)
            relation = self.rel_cell(
                torch.cat(
                    [global_ctx, subject_ctx, object_ctx, (subject + obj) * 0.5], -1
                ),
                relation,
            )

        _, subject_logits = self._attend(subject, candidate_repr, candidate_mask, self.subj_q)
        _, object_logits = self._attend(obj, candidate_repr, candidate_mask, self.obj_q)
        relation_logits = self.rel_head(
            torch.cat([relation, global_ctx, subject_ctx, object_ctx], -1)
        )
        confidence_logit = self.conf_head(
            torch.cat([relation, global_ctx], -1)
        ).squeeze(-1)
        return {
            "relation_logits": relation_logits,
            "subject_candidate_logits": subject_logits,
            "object_candidate_logits": object_logits,
            "confidence_logit": confidence_logit,
            "candidate_repr": candidate_repr,
        }
