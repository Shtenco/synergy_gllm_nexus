from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class GovernorDecision:
    status: str
    support: float
    contradiction: float
    reason: str

class EvidenceGovernor:
    def __init__(self,min_support=.6,contest_margin=.05):
        self.min_support=float(min_support); self.contest_margin=float(contest_margin)
    def decide(self,proposal,evidence):
        support=max((e.trust for e in evidence if proposal.claim_id in e.supports),default=0.0)
        contra=max((e.trust for e in evidence if proposal.claim_id in e.contradicts),default=0.0)
        if support>=self.min_support and contra>=self.min_support and abs(support-contra)<=self.contest_margin:
            return GovernorDecision('contested',support,contra,'balanced strong evidence')
        if support>=self.min_support and support>contra+self.contest_margin:
            return GovernorDecision('accepted',support,contra,'support clears threshold')
        if contra>=self.min_support and contra>support+self.contest_margin:
            return GovernorDecision('rejected',support,contra,'contradiction clears threshold')
        return GovernorDecision('insufficient',support,contra,'insufficient evidence')
