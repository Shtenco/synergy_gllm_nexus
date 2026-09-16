from __future__ import annotations
from dataclasses import dataclass
import hashlib
import re
from typing import Any

from .bus import OrganBus
from .config import UnifiedV2Config
from .contracts import AnswerGraph, ClaimProposal, EntityRef, ExecutionTrace, TextTurn
from .guard import SemanticConsistencyGuard
from .workspace import GraphWorkspace
from .organs.context_cortex import ContextCortexV2
from .organs.donor_adapters import FormalAuthorityAdapter, EvidenceSemanticAdapter, Omega15R2RoleAdapter, UnifiedRebuildAdapter
from .organs.evidence_governor import EvidenceGovernor
from .organs.morpholex import MorpholexAdapter
from .organs.r72_operator_adapter import R72OperatorAdapter
from .organs.recurrent_reasoner import R717RecurrentReasonerAdapter
from .organs.research_cortex import Omega16ResearchAdapter
from .organs.surface_decoder import NativeRussianSurfaceDecoderV2
from .organs.unseen_operator import R7LUnseenOperatorAdapter

R78_SHA='0c01a766e7aa49e5f7320149e2c1ee6251b1bd25846a31c08251936783768251'
R718_SHA='b0daffbeaba457ee61576ee3eecb42fa245f433382135a4fb20d90e019f7d524'

@dataclass(frozen=True)
class UnifiedV2Response:
    text: str
    answer_graph: AnswerGraph
    guard_ok: bool
    trace: ExecutionTrace

class UnifiedNexusV2Preblind:
    """Twelve-slot sovereign PREBLIND runtime.

    Donor organs are loaded fail-closed. Proposal/reasoning/research organs have
    no authority to commit factual claims. Context recall is promoted only via
    the Evidence Governor authority path before rendering.
    """
    ORGAN_IDS=(
        'graph_workspace','formal_authority','russian_binder','morpholex','semantic_operator','role_binder',
        'unseen_operator','recurrent_reasoner','evidence_governor','context_cortex','research_cortex','surface_decoder'
    )

    def __init__(self, config: UnifiedV2Config, *, ablations: set[str]|None=None):
        self.config=config
        self.ablations=frozenset(ablations or ())
        unknown=self.ablations-set(self.ORGAN_IDS)
        if unknown: raise ValueError(f'unknown organ ablations: {sorted(unknown)}')
        self.bus=OrganBus()
        self.guard=SemanticConsistencyGuard()
        self.workspace=GraphWorkspace() if self._enabled('graph_workspace') else None
        self.formal=FormalAuthorityAdapter(config.r78_module,expected_sha256=R78_SHA) if self._enabled('formal_authority') else None
        self.russian_binder=R72OperatorAdapter(config.r72_root) if self._enabled('russian_binder') else None
        self.morpholex=MorpholexAdapter(config.r714_root) if self._enabled('morpholex') else None
        # Ω-1.5R2 carries both frozen semantic relation and relation-conditioned roles.
        role_stack=Omega15R2RoleAdapter(config.omega15r2_root,unified_rebuild_root=config.unified_v1_root) if (self._enabled('semantic_operator') or self._enabled('role_binder')) else None
        self.semantic=role_stack if self._enabled('semantic_operator') else None
        self.role=role_stack if self._enabled('role_binder') else None
        self.unseen=R7LUnseenOperatorAdapter(config.r7l_root) if self._enabled('unseen_operator') else None
        self.recurrent=R717RecurrentReasonerAdapter(config.r717_root) if self._enabled('recurrent_reasoner') else None
        self.evidence=EvidenceSemanticAdapter(config.r718_module,expected_sha256=R718_SHA) if self._enabled('evidence_governor') else None
        self.governor=EvidenceGovernor() if self._enabled('evidence_governor') else None
        self.context=ContextCortexV2() if self._enabled('context_cortex') else None
        self.research=Omega16ResearchAdapter(config.omega16_root) if self._enabled('research_cortex') else None
        self.decoder=NativeRussianSurfaceDecoderV2() if self._enabled('surface_decoder') else None
        self.unified=UnifiedRebuildAdapter(config.unified_v1_root) if self._enabled('graph_workspace') else None
        self.organ_status={organ:self._enabled(organ) for organ in self.ORGAN_IDS}

    def _enabled(self, organ: str) -> bool:
        return organ not in self.ablations

    def _require(self, organ: str, value: Any):
        if value is None:
            self.bus.record_bypass(organ,'ablated')
            raise RuntimeError(f'organ is ablated: {organ}')
        self.bus.record_call(organ,'ok')
        return value

    def answer_formal_mcq(self,item: dict):
        return self._require('formal_authority',self.formal).answer_mcq(item)

    def answer_semantic_mcq(self,item: dict):
        return self._require('evidence_governor',self.evidence).answer_mcq(item)

    def solve_operator_case(self,case: dict):
        return self._require('russian_binder',self.russian_binder).solve_case(case)

    def parse_relation_roles(self,text: str):
        stack=self._require('semantic_operator',self.semantic)
        self.bus.record_call('role_binder','relation-conditioned')
        return stack.parse(text)

    def canonicalize(self,text: str):
        return self._require('morpholex',self.morpholex).canonicalize(text)

    def recurrent_advice(self,item: dict):
        return self._require('recurrent_reasoner',self.recurrent).advise_mcq(item)

    def research_query(self,text: str, *, sealed=False, no_web=False):
        return self._require('research_cortex',self.research).build_query(text,sealed=sealed,no_web=no_web)

    def resolve_graph_case(self, item: dict) -> dict:
        unified=self._require('graph_workspace',self.unified)
        return unified.resolve_graph(item['facts'],item['query'])

    def resolve_context_case(self, item: dict) -> str|None:
        context=self._require('context_cortex',self.context)
        key=f"{item['relation']}:{item['subject']}"
        context.remember(key,item['old_object'],topic='ub1')
        context.remember(key,item['new_object'],topic='ub1',revision=True)
        return context.recall(key,topic='ub1')

    def resolve_evidence_case(self, item: dict) -> str|None:
        governor=self._require('evidence_governor',self.governor)
        best=None; best_support=-1.0
        from .contracts import EvidenceItem
        for idx,row in enumerate(item['claims']):
            cid=f"ub1-evidence-{item['id']}-{idx}"
            proposal=ClaimProposal(
                claim_id=cid,
                subject=EntityRef(f"entity:{item['subject']}",item['subject'],(item['subject'],)),
                relation=item['relation'],
                object=row['object'],
                confidence=float(row['trust']),
                provenance=(row['source'],),
            )
            ev=(EvidenceItem(f"ev-{idx}",row['source'],supports=(cid,),trust=float(row['trust']),content_hash=f"{item['id']}:{idx}"),)
            decision=governor.decide(proposal,ev)
            if decision.status=='accepted' and decision.support>best_support:
                best=row['object']; best_support=decision.support
        return best

    def _context_query(self,text: str, *, topic: str) -> tuple[str,str,str]|None:
        # Minimal deterministic context contract used by PREBLIND baseline.
        m=re.search(r'(?iu)кто\s+хранит\s+([^?!.]+)',text)
        if m:
            obj=m.group(1).strip().casefold()
            value=self.context.recall(f'owner:{obj}',topic=topic) if self.context else None
            return ('owner',obj,value) if value is not None else None
        return None

    def respond(self,turn: TextTurn, *, topic: str='default') -> UnifiedV2Response:
        if self.context is None or self.workspace is None or self.decoder is None or self.governor is None:
            raise RuntimeError('respond requires context/workspace/evidence/surface organs enabled')
        self.bus.record_call('context_cortex',turn.turn_id)
        found=self._context_query(turn.text_ru,topic=topic)
        if found is None:
            graph=AnswerGraph((),(),(),('Недостаточно данных',))
            text=self.decoder.render(graph)
            self.bus.record_call('surface_decoder','abstain')
            checked=self.guard.check(graph,text)
            return UnifiedV2Response(text,graph,checked.ok,self.bus.trace())
        _,obj,value=found
        claim_id='ctx-'+hashlib.sha256(f'{topic}:{obj}:{value}'.encode()).hexdigest()[:16]
        proposal=ClaimProposal(
            claim_id=claim_id,
            subject=EntityRef(f'entity:{value}',str(value),(str(value),)),
            relation='хранит',
            object=obj,
            confidence=1.0,
            provenance=(f'context:{topic}:owner:{obj}',),
        )
        self.workspace.add_candidate(proposal)
        # Context memory is a user-provided, revision-aware local source. The
        # governor remains the sole authority that promotes it to committed truth.
        from .contracts import EvidenceItem
        evidence=(EvidenceItem('ctx-evidence',proposal.provenance[0],supports=(claim_id,),trust=1.0,content_hash=claim_id),)
        self.bus.record_call('evidence_governor',claim_id)
        decision=self.governor.decide(proposal,evidence)
        if decision.status!='accepted':
            self.bus.record_reject('evidence_governor',decision.status)
            graph=AnswerGraph((),(),(),('Недостаточно подтверждений',))
        else:
            claim=self.workspace.commit_proposal(proposal,authority='evidence_governor')
            self.bus.record_commit('evidence_governor',claim_id)
            graph=AnswerGraph((claim,),(),(),())
        text=self.decoder.render(graph)
        self.bus.record_call('surface_decoder','faithful')
        checked=self.guard.check(graph,text)
        if not checked.ok:
            self.bus.record_reject('surface_guard',','.join(checked.violations))
        return UnifiedV2Response(text,graph,checked.ok,self.bus.trace())
