import json
from pathlib import Path
import pytest
from nexus_gllm.unified_v3.moe.exact_artifacts import ArtifactCatalog, ArtifactStatus
from nexus_gllm.unified_v3.moe.exact_experts import R7LExactExpert,R72ExactExpert,R76ExactExpert,R78ExactExpert,R710ExactExpert,R714ExactExpert,R718ExactExpert
ART=Path('/mnt/data')
HAS_EXTERNAL=(ART/'r7_seed711.pt').is_file() and (ART/'r72_language_binder.pt').is_file()
requires_external=pytest.mark.skipif(not HAS_EXTERNAL,reason='external exact-artifact bundle is not mounted on this host')

def test_catalog_declares_recovered_status_without_faking_mount_availability():
    c=ArtifactCatalog.default(ART)
    for e in ('r7l','r72','r76','r78','r710','r714','r718','omega15r2','v10'):
        assert c.records[e].status is ArtifactStatus.EXACT_RUNNABLE
    assert c.verify('r7443').status is ArtifactStatus.EXACT_DEPLOYED_RUNTIME
    assert c.verify('r13x_v3').status is ArtifactStatus.VERIFIED_OPERATIONAL_RUNTIME
    assert c.verify('unified_r13').status is ArtifactStatus.HISTORICAL_RELEASE_NOT_MOUNTED
    if not HAS_EXTERNAL:
        assert c.verify('r7l').status is ArtifactStatus.CHECKPOINT_NOT_MOUNTED

@requires_external
def test_r7l_exact_checkpoint_infers_missing_mapping():
    e=R7LExactExpert(ART/'r7_seed712.pt');support=[(0,2,1),(1,0,3),(2,3,0)]
    assert e.predict(support,3,'effect')==1 and e.predict(support,3,'action')==2
@requires_external
def test_r72_exact_binder_and_core_solve_blind_style_ru():
    e=R72ExactExpert(ART/'r72_language_binder.pt',ART/'r7l_core_seed712.pt');support=['Наблюдение 0: при «янтарь» появляется «юг», управление — «маяк».','Наблюдение 1: при «лазурь» появляется «север», управление — «шлюз».','Наблюдение 2: при «графит» появляется «запад», управление — «мост».'];q='Применив правило к «нефрит», что следует ожидать как результат процесса?'
    assert e.predict(support,q)=='восток'
@requires_external
def test_r76_exact_pickle_answers_known_semantic_atom():
    assert R76ExactExpert(ART/'r76_semantic_knowledge_organ.pkl.bin').answer('Все A являются B. Некоторые C являются A. Что следует обязательно?')=='Некоторые C являются B'
@requires_external
def test_r78_and_r710_execute_original_runtime_on_math_case():
    item={'id':'B1','domain':'math','q':'Чему равно 23 × 7?','options':{'A':'151','B':'161','C':'171','D':'181'}}
    assert R78ExactExpert().answer(item)=='B';r=R710ExactExpert().answer(item);assert r['answer']=='B' and r['status']=='VERIFIED'
@requires_external
def test_r714_exact_morpholex_detects_and_canonicalizes():
    lang,canon=R714ExactExpert().analyze('Борис получил от Анны ключ.');assert lang=='ru' and 'борис' in canon and 'ключ' in canon
@requires_external
def test_r718_exact_runtime_uses_real_evidence_credit_models():
    e=R718ExactExpert();item={'id':'E1','domain':'evidence','q':'Какой вариант лучше подтверждён независимыми источниками?','options':{'A':'альфа','B':'бета','C':'гамма','D':'дельта'}};out=e.answer(item,e.make_teacher_rows('C',seed=123,noise=0.10));assert out['answer']=='C'
@requires_external
def test_r7l_exact_collective_loads_all_three_frozen_checkpoints():
    from nexus_gllm.unified_v3.moe.exact_experts import R7LCollectiveExactExpert
    e=R7LCollectiveExactExpert([ART/'r7_seed711.pt',ART/'r7_seed712.pt',ART/'r7_seed713.pt']);support=[(0,2,1),(1,0,3),(2,3,0)]
    assert e.predict(support,3,'effect')==1 and e.predict(support,3,'action')==2
