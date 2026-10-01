from __future__ import annotations
from dataclasses import dataclass
import hashlib,json

@dataclass(frozen=True)
class ReplayCase:
    case_id:str
    capability:str
    payload_sha256:str
    baseline_correct:bool
    baseline_confidence:float

@dataclass(frozen=True)
class ReplayOutcome:
    case_id:str
    correct:bool
    confidence:float

@dataclass(frozen=True)
class ReplayReport:
    n:int
    baseline_correct_n:int
    candidate_correct_n:int
    regression_count:int
    correction_count:int
    baseline_score:float
    candidate_score:float
    calibration_delta:float
    manifest_sha256:str

class FrozenReplayBank:
    def __init__(self,cases):
        self.cases=tuple(cases)
        if len({c.case_id for c in self.cases})!=len(self.cases):raise ValueError('duplicate replay case_id')
    def manifest(self):
        rows=[c.__dict__ for c in sorted(self.cases,key=lambda x:x.case_id)]
        body=json.dumps(rows,sort_keys=True,separators=(',',':')).encode()
        return {'cases':rows,'sha256':hashlib.sha256(body).hexdigest()}
    def verify(self,manifest):
        return self.manifest()['sha256']==manifest.get('sha256')

class AntiForgettingEvaluator:
    @staticmethod
    def _brier(rows,truth):
        if not rows:return 0.0
        return sum((max(0,min(1,float(r.confidence)))-(1.0 if truth[r.case_id] else 0.0))**2 for r in rows)/len(rows)

    def evaluate(self,bank:FrozenReplayBank,outcomes):
        om={o.case_id:o for o in outcomes}
        if set(om)!={c.case_id for c in bank.cases}:raise ValueError('replay outcome coverage mismatch')
        regress=correct=0
        baseline_correct=sum(c.baseline_correct for c in bank.cases)
        candidate_correct=0
        truth={}
        base_rows=[];cand_rows=[]
        for c in bank.cases:
            o=om[c.case_id];truth[c.case_id]=bool(o.correct);candidate_correct+=int(o.correct)
            regress+=int(c.baseline_correct and not o.correct);correct+=int((not c.baseline_correct) and o.correct)
            base_rows.append(ReplayOutcome(c.case_id,c.baseline_correct,c.baseline_confidence));cand_rows.append(o)
        n=max(1,len(bank.cases));base_brier=self._brier(base_rows,{c.case_id:c.baseline_correct for c in bank.cases});cand_brier=self._brier(cand_rows,truth)
        return ReplayReport(len(bank.cases),baseline_correct,candidate_correct,regress,correct,baseline_correct/n,candidate_correct/n,cand_brier-base_brier,bank.manifest()['sha256'])
