from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import time
from collections import Counter
from pathlib import Path

import torch
import torch.nn.functional as F
from torch import nn

from nexus_gllm.graph_cortex import GraphConstructionCortex
from training.graph_cortex_dataset import CandidateVocab, enumerate_candidates
from training.train_compiler import DEFAULT_RELATIONS as _BASE_RELATIONS

RELATIONS = ("owned_by", "located_in", "is_a", "older_than", "before", "causes", "abstain")
REL2I = {relation: i for i, relation in enumerate(RELATIONS)}


def _load_rows(path: str | Path, split: str) -> list[dict]:
    import gzip
    rows: list[dict] = []
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("split") == split:
                rows.append(row)
    return rows


class CachedSplit:
    def __init__(self, rows: list[dict], vocab: CandidateVocab, max_len: int = 96, max_candidates: int = 32) -> None:
        self.rows = rows
        table = vocab.stoi
        unk = table[vocab.UNK]
        pad = table[vocab.PAD]
        n = len(rows)
        self.tokens = torch.full((n, max_len), pad, dtype=torch.long)
        self.mask = torch.zeros((n, max_len), dtype=torch.bool)
        self.morph_table = vocab.morph_table()
        self.candidates = torch.full((n, max_candidates, 2), -1, dtype=torch.long)
        self.candidate_mask = torch.zeros((n, max_candidates), dtype=torch.bool)
        self.rel = torch.empty(n, dtype=torch.long)
        self.subj = torch.full((n,), -1, dtype=torch.long)
        self.obj = torch.full((n,), -1, dtype=torch.long)
        self.abstain = torch.zeros(n, dtype=torch.bool)
        for i, row in enumerate(rows):
            text = row["input_text"][:max_len]
            target = row["compiler_target"]
            ids = [table.get(ch, unk) for ch in text]
            self.tokens[i, : len(ids)] = torch.tensor(ids)
            self.mask[i, : len(ids)] = True
            candidates = enumerate_candidates(text, max_words=2)[:max_candidates]
            if candidates:
                self.candidates[i, : len(candidates)] = torch.tensor(candidates)
                self.candidate_mask[i, : len(candidates)] = True
            self.rel[i] = REL2I[target["relation"]]
            if target["relation"] == "abstain":
                self.abstain[i] = True
            else:
                self.subj[i] = candidates.index(tuple(target["subject_span"]))
                self.obj[i] = candidates.index(tuple(target["object_span"]))


def _macro_f1(gold: torch.Tensor, pred: torch.Tensor) -> float:
    values = []
    for cls in range(len(RELATIONS)):
        tp = int(((gold == cls) & (pred == cls)).sum())
        fp = int(((gold != cls) & (pred == cls)).sum())
        fn = int(((gold == cls) & (pred != cls)).sum())
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        values.append(2 * precision * recall / (precision + recall) if precision + recall else 0.0)
    return sum(values) / len(values)


@torch.no_grad()
def evaluate(model: GraphConstructionCortex, data: CachedSplit, batch_size: int = 512) -> dict:
    model.eval()
    relation_gold = []
    relation_pred = []
    subject_ok: list[bool] = []
    object_ok: list[bool] = []
    strict: list[bool] = []
    strict_non: list[bool] = []
    abstain_tp = abstain_fp = abstain_fn = 0
    for start in range(0, len(data.rows), batch_size):
        idx = torch.arange(start, min(start + batch_size, len(data.rows)))
        output = model(
            data.tokens[idx], data.mask[idx], data.morph_table[data.tokens[idx]],
            data.candidates[idx], data.candidate_mask[idx],
        )
        rp = output["relation_logits"].argmax(-1)
        sp = output["subject_candidate_logits"].argmax(-1)
        op = output["object_candidate_logits"].argmax(-1)
        relation_gold.append(data.rel[idx]); relation_pred.append(rp)
        for local_i, source_i in enumerate(idx.tolist()):
            gold_abstain = bool(data.abstain[source_i])
            pred_abstain = int(rp[local_i]) == REL2I["abstain"]
            if pred_abstain and gold_abstain: abstain_tp += 1
            elif pred_abstain and not gold_abstain: abstain_fp += 1
            elif not pred_abstain and gold_abstain: abstain_fn += 1
            if gold_abstain:
                strict.append(pred_abstain)
                continue
            sgood = int(sp[local_i]) == int(data.subj[source_i])
            ogood = int(op[local_i]) == int(data.obj[source_i])
            rgood = int(rp[local_i]) == int(data.rel[source_i])
            subject_ok.append(sgood); object_ok.append(ogood)
            strict.append(sgood and ogood and rgood); strict_non.append(sgood and ogood and rgood)
    gold = torch.cat(relation_gold); pred = torch.cat(relation_pred)
    precision = abstain_tp / (abstain_tp + abstain_fp) if abstain_tp + abstain_fp else 0.0
    recall = abstain_tp / (abstain_tp + abstain_fn) if abstain_tp + abstain_fn else 0.0
    return {
        "relation_accuracy": float((gold == pred).float().mean()),
        "macro_f1": _macro_f1(gold, pred),
        "subject_exact": sum(subject_ok) / len(subject_ok) if subject_ok else 0.0,
        "object_exact": sum(object_ok) / len(object_ok) if object_ok else 0.0,
        "strict_graph_accuracy": sum(strict) / len(strict),
        "strict_non_abstain_graph_accuracy": sum(strict_non) / len(strict_non) if strict_non else 0.0,
        "abstention_precision": precision,
        "abstention_recall": recall,
        "abstention_f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
    }


def run_chunk(data_path: str | Path, state_path: str | Path, final_path: str | Path, *, steps: int = 20, batch_size: int = 1024, seed: int = 17, hidden: int = 32, slot_dim: int = 80, char_dim: int = 24, lr: float = 2e-4) -> dict:
    torch.set_num_threads(5)
    torch.manual_seed(seed)
    random.seed(seed)
    train_rows = _load_rows(data_path, "train")
    dev_rows = _load_rows(data_path, "dev")
    vocab = CandidateVocab.from_texts([row["input_text"] for row in train_rows])
    train = CachedSplit(train_rows, vocab)
    dev = CachedSplit(dev_rows, vocab)
    model = GraphConstructionCortex(len(vocab), len(RELATIONS), char_dim=char_dim, hidden=hidden, slot_dim=slot_dim)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    counts = Counter(row["compiler_target"]["relation"] for row in train_rows)
    weights = torch.tensor([1 / math.sqrt(max(counts[r], 1)) for r in RELATIONS], dtype=torch.float32)
    weights /= weights.mean()
    state_file = Path(state_path)
    if state_file.exists():
        saved = torch.load(state_file, map_location="cpu", weights_only=False)
        model.load_state_dict(saved["model_state"])
        optimizer.load_state_dict(saved["optimizer_state"])
        cursor = int(saved["cursor"]); global_step = int(saved["global_step"]); seen = int(saved["seen"])
        best_key = tuple(saved["best_key"]) if saved.get("best_key") else None
        best_state = saved.get("best_state"); best_dev = saved.get("best_dev"); history = list(saved.get("history", []))
    else:
        cursor = global_step = seen = 0; best_key = best_state = best_dev = None; history = []
    generator = torch.Generator().manual_seed(seed + 1)
    permutation = torch.randperm(len(train_rows), generator=generator)
    total_batches = (len(train_rows) + batch_size - 1) // batch_size
    end_cursor = min(total_batches, cursor + steps)
    sums = Counter(); chunk_seen = 0; started = time.time(); model.train()
    for batch_index in range(cursor, end_cursor):
        idx = permutation[batch_index * batch_size : min((batch_index + 1) * batch_size, len(train_rows))]
        output = model(train.tokens[idx], train.mask[idx], train.morph_table[train.tokens[idx]], train.candidates[idx], train.candidate_mask[idx])
        relation_loss = F.cross_entropy(output["relation_logits"], train.rel[idx], weight=weights)
        non = ~train.abstain[idx]
        subject_loss = F.cross_entropy(output["subject_candidate_logits"][non], train.subj[idx][non])
        object_loss = F.cross_entropy(output["object_candidate_logits"][non], train.obj[idx][non])
        confidence_loss = F.binary_cross_entropy_with_logits(output["confidence_logit"], torch.ones_like(output["confidence_logit"]))
        loss = relation_loss + subject_loss + object_loss + 0.1 * confidence_loss
        optimizer.zero_grad(set_to_none=True); loss.backward(); nn.utils.clip_grad_norm_(model.parameters(), 1.0); optimizer.step()
        size = len(idx); chunk_seen += size; seen += size; global_step += 1
        sums["loss"] += float(loss.detach()) * size
    metrics = evaluate(model, dev)
    record = {"cursor": end_cursor, "global_step": global_step, "seen": seen, "chunk_seen": chunk_seen, "chunk_seconds": time.time() - started, "train_loss": sums["loss"] / max(chunk_seen, 1), **metrics}
    history.append(record)
    key = (metrics["strict_non_abstain_graph_accuracy"], metrics["relation_accuracy"], metrics["subject_exact"] + metrics["object_exact"])
    if best_key is None or key > best_key:
        best_key = key; best_dev = metrics; best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
    payload = {"format_version": 1, "cursor": end_cursor, "global_step": global_step, "seen": seen, "model_state": {k: v.detach().cpu() for k, v in model.state_dict().items()}, "optimizer_state": optimizer.state_dict(), "best_key": best_key, "best_state": best_state, "best_dev": best_dev, "history": history, "config": model.config, "vocab": list(vocab.tokens), "relations": list(RELATIONS), "seed": seed, "batch_size": batch_size, "corpus_gzip_sha256": hashlib.sha256(Path(data_path).read_bytes()).hexdigest()}
    state_file.parent.mkdir(parents=True, exist_ok=True); torch.save(payload, state_file)
    if end_cursor >= total_batches:
        final = {"format_version": 1, "architecture": "omega13_candidate_graph_slots", "config": model.config, "vocab": list(vocab.tokens), "relations": list(RELATIONS), "seed": seed, "train_examples": len(train_rows), "dev_examples": len(dev_rows), "dev_metrics": best_dev, "state_dict": best_state, "history": history, "params": sum(p.numel() for p in model.parameters()), "corpus_gzip_sha256": payload["corpus_gzip_sha256"]}
        Path(final_path).parent.mkdir(parents=True, exist_ok=True); torch.save(final, final_path)
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("data")
    parser.add_argument("--state", required=True)
    parser.add_argument("--final", required=True)
    parser.add_argument("--steps", type=int, default=20)
    parser.add_argument("--lr", type=float, default=2e-4)
    args = parser.parse_args()
    print(json.dumps(run_chunk(args.data, args.state, args.final, steps=args.steps, lr=args.lr), ensure_ascii=False, indent=2))
