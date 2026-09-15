from nexus_gllm.research.reflex import ResearchReflex
from nexus_gllm.research.types import SearchHit

class Adapter:
    name='x'; networked=True
    def search(self,q): return [SearchHit('x','https://example.org/a','A','X является Y',1.0,source_type='primary')]

def test_probe_and_sealed():
    r=ResearchReflex([Adapter()])
    out=r.run('Кто такой X?',{}, {})
    assert out.mode=='PROBE' and out.sources>=1
    out2=r.run('Кто такой X?',{}, {'sealed':True})
    assert out2.mode=='SEALED' and out2.sources==0