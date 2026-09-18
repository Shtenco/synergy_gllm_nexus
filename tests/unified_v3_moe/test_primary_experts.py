from nexus_gllm.unified_v3.moe.contracts import ExpertContext
from nexus_gllm.unified_v3.moe.experts.r72_language import R72LanguageExpert
from nexus_gllm.unified_v3.moe.experts.r718_evidence import R718EvidenceExpert
from nexus_gllm.unified_v3.moe.experts.r744_context import R744ContextExpert
from nexus_gllm.unified_v3.moe.experts.omega15r2_graph import Omega15R2GraphExpert

def test_r72_binds_russian_transfer_form():
    p=R72LanguageExpert().propose(ExpertContext(metadata={'text':'Борис получил от Анны ключ.'}))
    assert ('анна','передать','ключ','борис') in p.semantic_facts

def test_r718_preserves_conflict():
    p=R718EvidenceExpert().propose(ExpertContext(metadata={'evidence':[('s1','q',True),('s2','q',False)]}))
    assert 'CONFLICTED' in p.failure_flags

def test_context_revision_supersedes_old_value():
    p=R744ContextExpert().propose(ExpertContext(metadata={'events':[('owner','car','anna',10),('owner','car','boris',40)]}))
    assert ('owner','car','boris') in p.semantic_facts
    assert ('owner','car','anna') not in p.semantic_facts

def test_graph_expert_emits_role_fact():
    p=Omega15R2GraphExpert().propose(ExpertContext(metadata={'subject':'anna','relation':'located_in','object':'omsk'}))
    assert ('anna','located_in','omsk') in p.semantic_facts
