from nexus_gllm.unified_v3.cognitive.conversation_shell import ConversationShellR1
from nexus_gllm.unified_v3.cognitive.language_cortex import *
from nexus_gllm.unified_v3.cognitive.semantic_authority import *
from nexus_gllm.unified_v3.contracts import *
import hashlib

class Lang:
    backend_id='lang'
    def propose(self,text):
        h=hashlib.sha256(text.encode()).hexdigest()
        s=SourceSpanRef(0,len(text),h)
        return LanguageParseProposal(h,'lang',(ProposedAtom('op:likes',('alice','tea'),True,.95,s),))

class Fluent:
    backend_id='fluent'
    def generate(self,c):
        return 'Ответ: 42.' if c.answer_values==('42',) else 'Москва знает ответ.'

def fp():
    shell=ConversationShellR1('s',language_backend=Lang())
    p=shell.language.parse('Alice likes tea')
    return atom_fingerprint(p.observation.atoms[0])

def test_parser_alone_does_not_commit_world():
    s=ConversationShellR1('s',language_backend=Lang());r=s.ingest('Alice likes tea')
    assert r.world_fact_count==0 and s.world.facts==()
    assert s.beliefs.resolve(fp()).status.name=='PROPOSED'

def test_user_assertion_enters_context_but_not_verified_world():
    f=fp();a=SemanticAttestation('user','user',AttestationKind.USER_ASSERTION,.9,f,True)
    s=ConversationShellR1('s',language_backend=Lang());r=s.ingest('Alice likes tea',(a,))
    assert r.world_fact_count==0 and r.asserted_context_count==1
    assert s.context.current('semantic:'+f).value=='asserted'

def test_independent_evidence_commits_verified_world_and_context():
    f=fp();xs=(SemanticAttestation('e1','A',AttestationKind.EVIDENCE,.9,f,True),SemanticAttestation('e2','B',AttestationKind.EVIDENCE,.9,f,True))
    s=ConversationShellR1('s',language_backend=Lang());r=s.ingest('Alice likes tea',xs)
    assert r.world_fact_count==1 and s.context.current('semantic:'+f).status.name=='VERIFIED'

def test_surface_generation_is_still_guarded_and_non_authoritative():
    s=ConversationShellR1('s',language_backend=Lang(),generative_backend=Fluent())
    ep=EpistemicResult(EpistemicState.PROVED,('42',),.9)
    out=s.render(ep,numbers=('42',))
    assert out.text=='Ответ: 42.' and not out.authoritative

def test_hallucinated_surface_entity_falls_back():
    s=ConversationShellR1('s',language_backend=Lang(),generative_backend=Fluent())
    ep=EpistemicResult(EpistemicState.PROVED,(),.9)
    out=s.render(ep)
    assert out.used_fallback and out.backend_id=='deterministic_v3'
