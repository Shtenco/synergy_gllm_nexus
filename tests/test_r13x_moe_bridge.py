from nexus_gllm.r13x_moe_bridge import R13XMoEBridge
from nexus_gllm.unified_v3.moe.contracts import ExpertContext

def test_real_moe_runtime_produces_governed_execution():
    bridge=R13XMoEBridge()
    ctx=ExpertContext(metadata={"text":"test","language":"ru","expert_answers":{
        "r7l":"A","r72":"A","r718":"B","v3":"A"
    }})
    out=bridge.answer(context=ctx,query="test")
    assert out.selected
    assert out.moe_response.proposals
    assert out.r13x.replay_hash
