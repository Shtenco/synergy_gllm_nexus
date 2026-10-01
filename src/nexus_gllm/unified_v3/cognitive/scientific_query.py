from __future__ import annotations
from dataclasses import dataclass
from .information_gain import ActiveInformationSelector,HypothesisMass,InformationQuery
from .action_boundary import ActionProposal,ActionRisk

@dataclass(frozen=True)
class QueryActionSpec:
    query:InformationQuery
    action_type:str
    target:str
    scope:str
    intervention:bool=False
    arguments:tuple[tuple[str,str],...]=()
    evidence_ids:tuple[str,...]=()

@dataclass(frozen=True)
class ScientificQueryPlan:
    selected_query_id:str|None
    action_proposal:ActionProposal|None
    utility:float|None
    reason:str

class ScientificQueryPlanner:
    """Information-gain selection produces a proposal, never a side effect."""
    def __init__(self,selector=None):
        self.selector=selector or ActiveInformationSelector()

    def plan(self,prior,query_specs):
        if not query_specs:return ScientificQueryPlan(None,None,None,'no_candidate_queries')
        queries=tuple(x.query for x in query_specs)
        best,scores=self.selector.choose(prior,queries)
        if best is None:return ScientificQueryPlan(None,None,None,'no_information_gain')
        spec=next(x for x in query_specs if x.query.query_id==best.query_id)
        risk=ActionRisk.MEDIUM if spec.intervention else ActionRisk.READ_ONLY
        proposal=ActionProposal(
            spec.action_type,spec.target,spec.arguments,
            reason=f'information_gain:{best.information_gain:.6f};utility:{best.utility:.6f}',
            evidence_ids=spec.evidence_ids,risk=risk,
            estimated_cost=max(0.0,spec.query.cost),requested_scope=spec.scope,
        )
        return ScientificQueryPlan(best.query_id,proposal,best.utility,'selected_by_expected_information_gain')
