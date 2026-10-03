from __future__ import annotations
import hashlib
import io

import torch
import torch.nn as nn

from .types import CortexDecisionFeatures, LearnedMetaDecision


class _PolicyValueNet(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int = 64, actions: int = 27):
        super().__init__()
        self.body = nn.Sequential(nn.Linear(input_dim, hidden_dim), nn.Tanh(), nn.Linear(hidden_dim, hidden_dim), nn.Tanh())
        self.policy = nn.Linear(hidden_dim, actions)
        self.value = nn.Linear(hidden_dim, 1)
    def forward(self, x):
        h = self.body(x)
        return self.policy(h), self.value(h).squeeze(-1)


class LearnedMetaPolicy:
    """Trainable cortex/CRC bridge.

    Actions encode depth(1..3) x fanout(1..3) x top-k(1..3). RPE and recursive
    credit become the policy advantage; frozen evaluation disables all updates.
    """
    def __init__(self, *, seed: int = 7321, lr: float = 3e-3, device: str = "cpu"):
        torch.manual_seed(seed)
        self.device = torch.device(device)
        self.input_dim = 14 + 2 + 8 + 3 + 5
        self.net = _PolicyValueNet(self.input_dim).to(self.device)
        self.opt = torch.optim.Adam(self.net.parameters(), lr=lr)
        self.learning_enabled = True

    def parameter_hash(self) -> str:
        buf = io.BytesIO(); torch.save(self.net.state_dict(), buf)
        return hashlib.sha256(buf.getvalue()).hexdigest()

    def _features(self, c: CortexDecisionFeatures, *, novelty: float, self_reliability: float,
                  budget_fraction: float, calibration_pressure: float) -> torch.Tensor:
        scalars = [float(c.uncertainty), max(0., min(1., float(novelty))),
                   max(0., min(1., float(self_reliability))), max(0., min(1., float(budget_fraction))),
                   max(0., min(1., float(calibration_pressure)))]
        vals = list(c.plan_probs)+list(c.relation_probs)+list(c.role_probs)+list(c.temporal_probs)+scalars
        return torch.tensor(vals, dtype=torch.float32, device=self.device).unsqueeze(0)

    @staticmethod
    def _decode_action(index: int):
        depth=index//9+1; rem=index%9; fanout=rem//3+1; topk=rem%3+1
        return depth, fanout, topk

    def decide(self, c: CortexDecisionFeatures, *, novelty: float, self_reliability: float=.5,
               budget_fraction: float=1.0, calibration_pressure: float=0.0, sample: bool=False) -> LearnedMetaDecision:
        x=self._features(c, novelty=novelty, self_reliability=self_reliability,
                         budget_fraction=budget_fraction, calibration_pressure=calibration_pressure)
        logits,value=self.net(x); probs=torch.softmax(logits[0],dim=-1)
        action=int(torch.multinomial(probs,1).item()) if sample else int(probs.argmax().item())
        depth,fanout,topk=self._decode_action(action); u=float(c.uncertainty)
        memory_limit=16 if max(u,novelty)>.65 else 8
        verification=3 if u>.8 else (2 if u>.5 else 1)
        return LearnedMetaDecision(topk,depth,fanout,memory_limit,verification,action,
                                   tuple(float(v) for v in probs.detach().cpu()),float(value.item()),u)

    def update(self, c: CortexDecisionFeatures, *, action_index: int, observed_reward: float, credit: float,
               novelty: float, self_reliability: float=.5, budget_fraction: float=1.0,
               calibration_pressure: float=0.0) -> dict:
        if not self.learning_enabled: raise RuntimeError("learning disabled")
        x=self._features(c, novelty=novelty, self_reliability=self_reliability,
                         budget_fraction=budget_fraction, calibration_pressure=calibration_pressure)
        logits,value=self.net(x); logp=torch.log_softmax(logits,dim=-1)[0,int(action_index)]
        target=torch.tensor(float(observed_reward),dtype=torch.float32,device=self.device)
        rpe=target-value[0]; advantage=rpe.detach()*float(credit)
        policy_loss=-logp*advantage; value_loss=.5*rpe.pow(2)
        entropy=-(torch.softmax(logits,-1)*torch.log_softmax(logits,-1)).sum(-1).mean()
        loss=policy_loss+value_loss-.001*entropy
        self.opt.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(self.net.parameters(),5.0); self.opt.step()
        return {"rpe":float(rpe.detach().item()),"advantage":float(advantage.item()),"loss":float(loss.detach().item())}

    def frozen_evaluation(self): return _FrozenEvaluation(self)


class _FrozenEvaluation:
    def __init__(self, policy): self.policy=policy; self.before=None; self.prev=None
    def __enter__(self):
        self.before=self.policy.parameter_hash(); self.prev=self.policy.learning_enabled
        self.policy.learning_enabled=False; self.policy.net.eval(); return self.policy
    def __exit__(self, exc_type, exc, tb):
        after=self.policy.parameter_hash(); self.policy.learning_enabled=self.prev
        if after!=self.before: raise RuntimeError("policy parameters changed during frozen evaluation")
        return False
