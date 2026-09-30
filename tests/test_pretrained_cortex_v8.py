import json
from nexus_gllm.pretrained_cortex_v8 import StructuredQwen3CortexV8, V8AuthorityBoundary

class FakeBackend:
    def __init__(self,obj): self.obj=obj
    def generate(self,prompt,*,system,max_tokens=384,temperature=0.0):
        return {"text":json.dumps(self.obj,ensure_ascii=False)}

def proposal(**kw):
    base={"plan":"causal","answer_candidate":"сервер","subject":"датчик","relation":"causes","object":"сервер","current_state":None,"historic_states":[],"operands":[],"evidence_needed":False,"confidence":0.97}
    base.update(kw); return StructuredQwen3CortexV8(FakeBackend(base)).propose("q")

def test_qwen_proposal_is_structured():
    p=proposal()
    assert p.plan=="causal"
    assert p.answer_candidate=="сервер"
    assert p.confidence==0.97

def test_qwen_never_becomes_final_without_verification():
    p=proposal(confidence=1.0)
    out=V8AuthorityBoundary.resolve(verified=False,proposal=p)
    assert out["authority"]=="NEXUS_ABSTAIN"
    assert out["answer"] is None
    assert out["proposal"]["answer_candidate"]=="сервер"

def test_verified_answer_overrides_qwen_candidate():
    p=proposal(answer_candidate="неверно")
    out=V8AuthorityBoundary.resolve(verified=True,verified_answer="сервер",proposal=p)
    assert out["authority"]=="NEXUS_VERIFIED"
    assert out["answer"]=="сервер"
    assert out["proposal"]["answer_candidate"]=="неверно"

def test_invalid_plan_fails_closed():
    b=FakeBackend({"plan":"invent_truth","answer_candidate":"x","confidence":1.0})
    try:
        StructuredQwen3CortexV8(b).propose("q")
        assert False
    except ValueError:
        pass
