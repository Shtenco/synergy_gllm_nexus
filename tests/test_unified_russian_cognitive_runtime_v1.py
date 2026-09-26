from nexus_gllm.unified_russian_cognitive_runtime_v1 import UnifiedRussianCognitiveRuntimeV1

class R:
    def __init__(self, abstained=False, text='x'):
        self.abstained=abstained
        self.text=text

class FakeCore:
    def __init__(self, response): self.response=response
    def answer(self, text, session_id): return self.response

class FakeRouter:
    def __init__(self, route): self._route=route
    def route(self, text): return self._route, .9, 'test'

def bare(response, route='language', cortex=lambda q:'proposal'):
    x=object.__new__(UnifiedRussianCognitiveRuntimeV1)
    x.core=FakeCore(response); x.router=FakeRouter(route); x.cortex=cortex
    return x

def test_resolved_core_remains_sovereign():
    rt=bare(R(False))
    out=rt.answer('q')
    assert out['trace']['sovereign_authority']=='NEXUS_CORE'
    assert 'cortex_proposal' not in out

def test_cortex_cannot_override_abstention():
    rt=bare(R(True))
    out=rt.answer('q')
    assert out['cortex_proposal']=='proposal'
    assert out['trace']['sovereign_authority']=='ABSTAIN'

def test_non_language_route_does_not_call_cortex():
    called=[]
    rt=bare(R(True),route='formal',cortex=lambda q:called.append(q) or 'bad')
    out=rt.answer('q')
    assert out['cortex_proposal'] is None
    assert called==[]
