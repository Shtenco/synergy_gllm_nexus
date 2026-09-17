from nexus_gllm.unified_v3.semantic_ir import semantic_fingerprint, assert_text_quarantined
from nexus_gllm.unified_v3.surface import ControlledSurfaceAdapter, SurfaceRequest

def test_active_passive_and_receive_forms_share_semantics():
    adapter=ControlledSurfaceAdapter()
    forms=['Анна передала ключ Борису.','Ключ был передан Борису Анной.','Борис получил от Анны ключ.']
    parsed=[adapter.parse(SurfaceRequest(x)) for x in forms]
    for x in parsed: assert_text_quarantined(x)
    assert len({semantic_fingerprint(x) for x in parsed})==1

def test_true_role_swap_changes_semantics():
    a=ControlledSurfaceAdapter().parse(SurfaceRequest('Анна передала ключ Борису.'))
    b=ControlledSurfaceAdapter().parse(SurfaceRequest('Борис передал ключ Анне.'))
    assert semantic_fingerprint(a)!=semantic_fingerprint(b)
