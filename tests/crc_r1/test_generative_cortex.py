from nexus_gllm.unified_v3.cognitive.generative import *
from nexus_gllm.unified_v3.cognitive.generative_port import CRCGenerativePort
from nexus_gllm.unified_v3.contracts import EpistemicResult,EpistemicState

class Good:
    backend_id='good'
    def generate(self,c):return f'Ответ: {c.answer_values[0]}.'
class HallucinatedNumber:
    backend_id='bad_number'
    def generate(self,c):return 'Ответ: 999.'
class NegationFlip:
    backend_id='bad_neg'
    def generate(self,c):return 'Ответ не подтверждён.'
class HallucinatedEntity:
    backend_id='bad_entity'
    def generate(self,c):return 'Москва подтверждает ответ.'

def contract():return SurfaceContract(EpistemicState.PROVED,('42',),('Альфа',),('42',),('ev1',),False)

def test_good_generation_remains_non_authoritative():
    r=AuthoritySafeGenerativeCortex(Good()).realize(contract());assert not r.used_fallback and r.backend_id=='good' and r.authoritative is False

def test_unlicensed_number_falls_back():
    r=AuthoritySafeGenerativeCortex(HallucinatedNumber()).realize(contract());assert r.used_fallback and 'unlicensed_number' in r.guard.violations or r.backend_id=='deterministic_v3'

def test_negation_flip_falls_back():
    r=AuthoritySafeGenerativeCortex(NegationFlip()).realize(contract());assert r.used_fallback

def test_unlicensed_named_entity_falls_back():
    r=AuthoritySafeGenerativeCortex(HallucinatedEntity()).realize(contract());assert r.used_fallback

def test_epistemic_bridge_never_grants_authority():
    ep=EpistemicResult(EpistemicState.PROVED,('42',),.9)
    r=CRCGenerativePort(Good()).render(ep,numbers=('42',));assert r.text=='Ответ: 42.' and r.authoritative is False
