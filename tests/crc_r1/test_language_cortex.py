from nexus_gllm.unified_v3.cognitive.language_cortex import *
from nexus_gllm.unified_v3.semantic_ir import assert_text_quarantined

class Fake:
    backend_id='fake'
    def __init__(self,proposal_fn):self.fn=proposal_fn
    def propose(self,text):return self.fn(text)

def good(text):
    h=LanguageCortexPort.text_sha256(text)
    return LanguageParseProposal(h,'fake',(ProposedAtom('op:transfer',('Анна','ключ','Борис'),True,.95,h),))

def test_language_result_contains_hash_not_raw_text():
    text='Анна передала Борису ключ'
    r=LanguageCortexPort(Fake(good)).parse(text)
    assert r.admission.accepted and r.proposal_only
    assert r.input_sha256==LanguageCortexPort.text_sha256(text)
    assert not hasattr(r,'text')
    assert_text_quarantined(r.observation)

def test_hash_mismatch_fails_closed():
    def bad(text):return LanguageParseProposal('0'*64,'fake',(ProposedAtom('op:x',('a','b'),True,.9,'a'*64),))
    r=LanguageCortexPort(Fake(bad)).parse('hello');assert not r.admission.accepted and r.observation.atoms==()

def test_low_confidence_parse_fails_closed():
    def low(text):
        h=LanguageCortexPort.text_sha256(text);return LanguageParseProposal(h,'fake',(ProposedAtom('op:x',('a','b'),True,.2,h),))
    assert not LanguageCortexPort(Fake(low)).parse('x').admission.accepted

def test_controlled_baseline_maps_existing_surface_into_proposal_only_ir():
    r=LanguageCortexPort(ControlledLanguageBackend()).parse('Анна передала Борис ключ.')
    assert r.admission.accepted and r.proposal_only and r.observation.atoms[0].operator.operator_id=='op:transfer'
