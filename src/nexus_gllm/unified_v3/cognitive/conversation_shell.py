from __future__ import annotations

from dataclasses import dataclass
from nexus_gllm.unified_v3.contracts import WorldHypothesis,EpistemicResult
from .language_cortex import LanguageCortexPort,ControlledLanguageBackend,LanguageParseResult
from .semantic_authority import SemanticCommitGate,SemanticCommitResult,SemanticFactStatus
from .belief_state import BeliefLedger
from .belief_bridge import ingest_semantic_commit
from .dialogue_context import DialogueContextR1,ContextValueStatus
from .generative_port import CRCGenerativePort
from .generative import SafeSurfaceResult


@dataclass(frozen=True)
class ConversationIngressResult:
    parse:LanguageParseResult
    commit:SemanticCommitResult
    belief_ids:tuple[str,...]
    world_fact_count:int
    asserted_context_count:int


@dataclass(frozen=True)
class ConversationTurn:
    ingress:ConversationIngressResult|None
    output:SafeSurfaceResult|None


class ConversationShellR1:
    """Authority-safe ingress/egress shell around CRC reasoning.

    This class coordinates language parsing, semantic authority, belief/context
    state and surface realization. It does not grant the language/generative
    backends reasoning or commit authority.
    """
    def __init__(self,session_id,*,language_backend=None,generative_backend=None,commit_gate=None):
        self.language=LanguageCortexPort(language_backend or ControlledLanguageBackend())
        self.commit_gate=commit_gate or SemanticCommitGate()
        self.beliefs=BeliefLedger()
        self.context=DialogueContextR1(session_id)
        self.world=WorldHypothesis('conversation:'+session_id)
        self.surface=CRCGenerativePort(generative_backend)

    def ingest(self,text,attestations=())->ConversationIngressResult:
        parsed=self.language.parse(text)
        committed=self.commit_gate.commit(parsed,self.world,attestations)
        self.world=committed.world
        beliefs=ingest_semantic_commit(self.beliefs,committed)
        for d in committed.decisions:
            key='semantic:'+d.atom_fingerprint
            if d.status is SemanticFactStatus.VERIFIED:
                self.context.set_value(key,'verified',status=ContextValueStatus.VERIFIED,provenance_id=';'.join(d.supporting_sources))
            elif d.status is SemanticFactStatus.ASSERTED_CONTEXT:
                self.context.set_value(key,'asserted',status=ContextValueStatus.ASSERTED,provenance_id=';'.join(d.supporting_sources))
        return ConversationIngressResult(parsed,committed,tuple(b.belief_id for b in beliefs),len(self.world.facts),len(committed.asserted_context))

    def render(self,epistemic:EpistemicResult,**surface_contract_kwargs)->SafeSurfaceResult:
        return self.surface.render(epistemic,**surface_contract_kwargs)

    def turn(self,text,*,attestations=(),epistemic=None,surface_contract_kwargs=None)->ConversationTurn:
        ingress=self.ingest(text,attestations)
        output=None if epistemic is None else self.render(epistemic,**(surface_contract_kwargs or {}))
        return ConversationTurn(ingress,output)
