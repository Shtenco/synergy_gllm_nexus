from __future__ import annotations
from dataclasses import dataclass
import uuid
from .types import CortexDecisionFeatures, LearnedMetaDecision
from .r13x_dialogue import R13XDialogueCompat, DialogueResponse

@dataclass(frozen=True)
class UnifiedRuntimeResponse:
    text:str; episode_id:str; dialogue:DialogueResponse; cortex:CortexDecisionFeatures; meta:LearnedMetaDecision; trace:tuple[str,...]
@dataclass
class _Episode:
    cortex:CortexDecisionFeatures; meta:LearnedMetaDecision; novelty:float

class NexusUnifiedCognitiveRuntime:
    def __init__(self, *, cortex, meta_policy, tokenizer, dialogue=None):
        self.cortex=cortex; self.meta_policy=meta_policy; self.tokenizer=tokenizer
        self.dialogue=dialogue or R13XDialogueCompat(); self.episodes={}
    def answer(self,text:str,session_id:str="default",*,novelty:float=.5,self_reliability:float=.5,budget_fraction:float=1.0,calibration_pressure:float=0.0):
        cf=self.cortex.infer_text(text,self.tokenizer)
        md=self.meta_policy.decide(cf,novelty=novelty,self_reliability=self_reliability,budget_fraction=budget_fraction,calibration_pressure=calibration_pressure)
        out=self.dialogue.answer(text,session_id)
        eid=str(uuid.uuid4()); self.episodes[eid]=_Episode(cf,md,float(novelty))
        trace=(f"cortex=v7.2:{cf.checkpoint_sha256[:12]}",f"meta_action={md.action_index}",f"depth={md.branch_depth}",f"fanout={md.branch_fanout}",f"topk={md.expert_top_k}",f"dialogue={out.intent}")
        return UnifiedRuntimeResponse(out.text,eid,out,cf,md,trace)
    def observe(self,episode_id:str,*,observed_reward:float,credit:float):
        ep=self.episodes.pop(episode_id)
        return self.meta_policy.update(ep.cortex,action_index=ep.meta.action_index,observed_reward=observed_reward,credit=credit,novelty=ep.novelty)
