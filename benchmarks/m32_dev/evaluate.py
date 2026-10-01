from __future__ import annotations

from collections import defaultdict
import hashlib
import json

from nexus_gllm.unified_v3.contracts import Entity, OperatorSymbol, SemanticAtom, TaskOpcode
from nexus_gllm.unified_v3.cognitive.conversation_shell import ConversationShellR1
from nexus_gllm.unified_v3.cognitive.conversational_reasoner_r2 import ConversationalReasonerR2, ConversationalRequest
from nexus_gllm.unified_v3.cognitive.generalized_ingress import (
    GeneralizedIngressProposal, GeneralizedIngressR1, GeneralizedSemanticAtomProposal,
    GeneralizedTaskProposal, GroundedSpanRef,
)
from nexus_gllm.unified_v3.cognitive.program_proposal import ProgramProposal
from nexus_gllm.unified_v3.cognitive.semantic_authority import AttestationKind,SemanticAttestation,atom_fingerprint

from .generator import FAMILIES,DevCase,generate


class FixtureBackend:
    backend_id='m32-dev-fixture'
    def __init__(self,case:DevCase):self.case=case
    @staticmethod
    def _span(request,source_id):
        src=request.source_map.get(source_id)
        if src is None:return GroundedSpanRef(source_id,0,1,'0'*64)
        return GroundedSpanRef(source_id,0,len(src.text),hashlib.sha256(src.text.encode()).hexdigest())
    def propose(self,request):
        atoms=tuple(
            GeneralizedSemanticAtomProposal(op,(a,b),pol,.99,(self._span(request,source_id),))
            for op,a,b,pol,source_id in self.case.facts
        )
        op,a,b=self.case.task;prompt_span=self._span(request,'prompt:0')
        task=GeneralizedTaskProposal(TaskOpcode.QUERY_RELATION,op,(a,b),.99,(prompt_span,))
        program=None if self.case.program is None else ProgramProposal(self.case.program,.99,(prompt_span,))
        return GeneralizedIngressProposal(self.backend_id,atoms,task,program)


def _conflict_attestation(case):
    if not case.conflict or not case.facts:return ()
    op,a,b,pol,_=case.facts[0]
    atom=SemanticAtom(OperatorSymbol(op,2),(Entity(a),Entity(b)),pol)
    return (SemanticAttestation('dev:contradiction','dev:independent',AttestationKind.EVIDENCE,.99,atom_fingerprint(atom),False,'dev:negative'),)


def run(seed=32001,n_per_family=20):
    cases=generate(seed,n_per_family)
    admitted_expected=admitted_ok=0
    provenance_total=provenance_ok=0
    solvable=program_ok=e2e_ok=0
    unsafe_promotions=0
    family=defaultdict(lambda:{'n':0,'task_admitted':0,'program_admitted':0,'strict':0,'solvable':0})

    for case in cases:
        shell=ConversationShellR1('m32-dev:'+case.case_id)
        reasoner=ConversationalReasonerR2(shell,ingress=GeneralizedIngressR1(FixtureBackend(case)))
        out=reasoner.answer(ConversationalRequest(case.prompt,case.history,case.documents),attestations=_conflict_attestation(case))
        row=family[case.family];row['n']+=1

        if case.admission_expected:
            admitted_expected+=1
            if out.ingress.task is not None:
                admitted_ok+=1;row['task_admitted']+=1
        if out.ingress.admission.accepted:
            provenance_total+=1
            # Ingress admission proves semantic/task spans; an admitted program additionally proves program provenance.
            if out.program_admission is None or out.program_admission.accepted:
                provenance_ok+=1

        if case.solvable:
            solvable+=1;row['solvable']+=1
            if out.program_admission is not None and out.program_admission.accepted:
                program_ok+=1;row['program_admitted']+=1
            truth=None if out.decision is None else out.decision.execution.execution.truth
            if truth is case.expected_truth:
                e2e_ok+=1;row['strict']+=1

        if shell.world.facts:
            unsafe_promotions+=len(shell.world.facts)

    by_family={}
    for name in FAMILIES:
        row=family[name];den=max(1,row['n']);sden=max(1,row['solvable'])
        by_family[name]={
            'n':row['n'],
            'task_admission':row['task_admitted']/den,
            'program_admission_solvable':row['program_admitted']/sden if row['solvable'] else None,
            'e2e_strict_solvable':row['strict']/sden if row['solvable'] else None,
        }

    report={
        'benchmark':'M32-DEV','seed':seed,'cases':len(cases),'clean_oos':False,
        'neural_quality_claim':False,'ftx1_used_as_clean_oos':False,
        'task_admission':admitted_ok/max(1,admitted_expected),
        'provenance_validity':provenance_ok/max(1,provenance_total),
        'program_admission_solvable':program_ok/max(1,solvable),
        'e2e_strict_solvable':e2e_ok/max(1,solvable),
        'unsafe_authority_promotions':unsafe_promotions,
        'by_family':by_family,
    }
    return report


def main():print(json.dumps(run(),indent=2,sort_keys=True))
if __name__=='__main__':main()
