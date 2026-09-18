from pathlib import Path
from nexus_gllm.unified_v3.moe.contracts import ExpertProposal,ExpertSpec,ExpertMode,ExpertProvenanceKind,CapabilityTag
from nexus_gllm.unified_v3.moe.registry import ExpertRegistry
from nexus_gllm.unified_v3.moe.lineage import lineage_independence_weight

def test_proposal_has_no_final_authority_field():
    p=ExpertProposal('p','e',CapabilityTag.FAST_INDUCTION,confidence=.8)
    assert not hasattr(p,'final_answer')
    assert not hasattr(p,'commit_world')

def test_registry_disables_hash_mismatch(tmp_path:Path):
    f=tmp_path/'x.bin'; f.write_bytes(b'abc')
    spec=ExpertSpec('e','1',(CapabilityTag.PROOF,), 'g', str(f),'0'*64,'x',ExpertMode.ACTIVE,1000,.9,ExpertProvenanceKind.EXACT_HISTORICAL)
    reg=ExpertRegistry().register(spec)
    assert reg.verify_artifact('e') is False
    assert reg.get('e').active_mode is ExpertMode.DISABLED

def test_lineage_discount_related_experts():
    a=ExpertSpec('a','1',(CapabilityTag.PROOF,), 'same',None,None,'x')
    b=ExpertSpec('b','1',(CapabilityTag.EVIDENCE,), 'same',None,None,'x')
    c=ExpertSpec('c','1',(CapabilityTag.GRAPH,), 'other',None,None,'x')
    w=lineage_independence_weight((a,b,c))
    assert w['a']<1 and w['b']<1 and w['c']==1
