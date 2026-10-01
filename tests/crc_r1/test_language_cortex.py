from nexus_gllm.unified_v3.cognitive.language_cortex import *
from nexus_gllm.unified_v3.semantic_ir import assert_text_quarantined
import hashlib
class Fake:
    backend_id='fake'
    def __init__(self,fn):self.fn=fn
    def propose(self,text):return self.fn(text)
def span(text,start=0,end=None):
    end=len(text) if end is None else end
    return SourceSpanRef(start,end,hashlib.sha256(text[start:end].encode()).hexdigest())
def good(text):
    return LanguageParseProposal(LanguageCortexPort.text_sha256(text),'fake',(ProposedAtom('op:transfer',('Анна','ключ','Борис'),True,.95,span(text)),))
def test_grounded_span_is_verified_then_raw_text_is_quarantined():
    text='Анна передала Борису ключ'
    r=LanguageCortexPort(Fake(good)).parse(text)
    assert r.admission.accepted and r.admitted_spans[0].start==0
    assert not hasattr(r,'text');assert_text_quarantined(r.observation)
def test_invented_span_hash_fails_closed():
    def bad(text):
        s=SourceSpanRef(0,len(text),'0'*64)
        return LanguageParseProposal(LanguageCortexPort.text_sha256(text),'fake',(ProposedAtom('op:x',('a','b'),True,.9,s),))
    r=LanguageCortexPort(Fake(bad)).parse('hello');assert not r.admission.accepted and 'atom_0:span_hash_mismatch' in r.admission.reasons
def test_out_of_bounds_span_fails_closed():
    def bad(text):
        s=SourceSpanRef(0,len(text)+10,'a'*64)
        return LanguageParseProposal(LanguageCortexPort.text_sha256(text),'fake',(ProposedAtom('op:x',('a','b'),True,.9,s),))
    assert not LanguageCortexPort(Fake(bad)).parse('x').admission.accepted
def test_low_confidence_parse_fails_closed():
    def low(text):
        return LanguageParseProposal(LanguageCortexPort.text_sha256(text),'fake',(ProposedAtom('op:x',('a','b'),True,.2,span(text)),))
    assert not LanguageCortexPort(Fake(low)).parse('x').admission.accepted
def test_controlled_baseline_maps_existing_surface_into_grounded_proposal():
    text='Анна передала Борис ключ.'
    r=LanguageCortexPort(ControlledLanguageBackend()).parse(text)
    assert r.admission.accepted and r.proposal_only and r.admitted_spans[0].sha256==hashlib.sha256(text.encode()).hexdigest()
