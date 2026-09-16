from __future__ import annotations
from .contracts import ClaimProposal, Claim

class AuthorityError(RuntimeError): pass

AUTHORITIES={'evidence_governor','formal_authority'}

class GraphWorkspace:
    def __init__(self):
        self.candidates: dict[str,ClaimProposal]={}
        self.committed: dict[str,Claim]={}

    def add_candidate(self,p:ClaimProposal):
        self.candidates[p.claim_id]=p
        return p

    def commit_proposal(self,p:ClaimProposal,*,authority:str)->Claim:
        if authority not in AUTHORITIES:
            raise AuthorityError(f'{authority} has no commit authority')
        self.candidates[p.claim_id]=p
        c=Claim(p.claim_id,p.subject,p.relation,p.object,p.confidence,p.provenance,authority,p.polarity)
        self.committed[c.claim_id]=c
        return c

    def get(self, claim_id: str):
        return self.committed.get(claim_id)
