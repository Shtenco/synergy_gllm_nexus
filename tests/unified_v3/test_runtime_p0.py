from nexus_gllm.unified_v3.contracts import EpistemicState
from nexus_gllm.unified_v3.rule_induction import RuleDemonstration
from nexus_gllm.unified_v3.runtime import UnifiedNexusV3P0
from nexus_gllm.unified_v3.surface import SurfaceRequest
from nexus_gllm.unified_v3.task_induction import TaskExample

def demos(op,positive=True):
    return (RuleDemonstration.chain(op,'анна','борис','вера',positive),RuleDemonstration.chain(op,'борис','вера','глеб',positive))

def test_end_to_end_unknown_operator_and_renamed_universe():
    rt=UnifiedNexusV3P0()
    req=SurfaceRequest.structured_relation('op:zurit',[('анна','борис'),('борис','вера'),('вера','глеб')],('анна','глеб'))
    out=rt.respond(req,demonstrations=demos('op:zurit'),task_examples=(TaskExample('op:zurit','relation_truth'),),audit_variants=(req,))
    assert out.epistemic.state is EpistemicState.PROVED
    assert out.generalization.stable
    assert out.execution.derivation.depth==3
    req2=SurfaceRequest.structured_relation('op:kema',[('u','v'),('v','w'),('w','x')],('u','x'))
    out2=rt.respond(req2,demonstrations=(RuleDemonstration.chain('op:kema','u','v','w'),RuleDemonstration.chain('op:kema','v','w','x')),task_examples=(TaskExample('op:kema','relation_truth'),),audit_variants=(req2,))
    assert out.rule_program.shape_fingerprint()==out2.rule_program.shape_fingerprint()
    assert out2.epistemic.state is EpistemicState.PROVED

def test_nontransitive_universe_does_not_derive_chain():
    rt=UnifiedNexusV3P0(); req=SurfaceRequest.structured_relation('op:q',[('a','b'),('b','c')],('a','c'))
    out=rt.respond(req,demonstrations=(RuleDemonstration.chain('op:q','a','b','c',False),),task_examples=(TaskExample('op:q','relation_truth'),))
    assert out.epistemic.state is EpistemicState.UNRESOLVED
