from nexus_gllm.unified_v3.cognitive.language_cortex import *
from nexus_gllm.unified_v3.cognitive.semantic_authority import *
from nexus_gllm.unified_v3.contracts import Entity,OperatorSymbol,SemanticAtom,SemanticObservation,WorldHypothesis
import hashlib

def parse():
    text='Анна передала ключ Борису'
    h=hashlib.sha256(text.encode()).hexdigest()
    atom=SemanticAtom(OperatorSymbol('op:transfer',3),(Entity('анна'),Entity('ключ'),Entity('борис')),True)
    p=LanguageParseResult(SemanticObservation((atom,)),'fake',h,(SourceSpanRef(0,len(text),h),),LanguageAdmission(True,()),True)
    return p,atom

def att(atom,kind,lineage='L1',trust=.9,supports=True,source='s'):
    return SemanticAttestation(source,lineage,kind,trust,atom_fingerprint(atom),supports)

def test_model_proposal_alone_never_commits_world_fact():
    p,a=parse();g=SemanticCommitGate();r=g.commit(p,WorldHypothesis('w'),(att(a,AttestationKind.MODEL_PROPOSAL),))
    assert r.world.facts==() and r.decisions[0].status is SemanticFactStatus.PROPOSED

def test_user_assertion_is_context_not_verified_world():
    p,a=parse();r=SemanticCommitGate().commit(p,WorldHypothesis('w'),(att(a,AttestationKind.USER_ASSERTION),))
    assert r.world.facts==() and r.asserted_context==(a,) and r.decisions[0].status is SemanticFactStatus.ASSERTED_CONTEXT

def test_one_evidence_lineage_is_not_enough():
    p,a=parse();xs=(att(a,AttestationKind.EVIDENCE,'shared',source='e1'),att(a,AttestationKind.EVIDENCE,'shared',source='e2'))
    r=SemanticCommitGate().commit(p,WorldHypothesis('w'),xs);assert r.world.facts==()

def test_two_independent_evidence_lineages_commit_verified_fact():
    p,a=parse();xs=(att(a,AttestationKind.EVIDENCE,'A',source='e1'),att(a,AttestationKind.EVIDENCE,'B',source='e2'))
    r=SemanticCommitGate().commit(p,WorldHypothesis('w'),xs)
    assert len(r.world.facts)==1 and r.decisions[0].status is SemanticFactStatus.VERIFIED

def test_formal_proof_can_commit_with_single_authority():
    p,a=parse();r=SemanticCommitGate().commit(p,WorldHypothesis('w'),(att(a,AttestationKind.FORMAL_PROOF,'formal'),))
    assert len(r.world.facts)==1 and r.decisions[0].accepted

def test_trusted_contradiction_blocks_otherwise_valid_support():
    p,a=parse();xs=(att(a,AttestationKind.FORMAL_PROOF,'formal'),att(a,AttestationKind.EVIDENCE,'B',supports=False,source='contra'))
    r=SemanticCommitGate().commit(p,WorldHypothesis('w'),xs)
    assert r.world.facts==() and r.decisions[0].status is SemanticFactStatus.REJECTED
