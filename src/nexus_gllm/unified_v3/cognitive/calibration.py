from __future__ import annotations
from dataclasses import dataclass
from collections import defaultdict

@dataclass(frozen=True)
class CalibrationObservation:
    capability:str
    confidence:float
    correct:bool

@dataclass(frozen=True)
class CalibrationMetrics:
    capability:str
    n:int
    brier:float
    ece:float
    mean_confidence:float
    accuracy:float

class CalibrationLedger:
    def __init__(self,bins=10):
        self.bins=int(bins);self._rows=defaultdict(list)

    def observe(self,capability,confidence,correct):
        c=max(0.0,min(1.0,float(confidence)))
        self._rows[capability].append(CalibrationObservation(capability,c,bool(correct)))
        return self

    def metrics(self,capability)->CalibrationMetrics:
        rows=tuple(self._rows.get(capability,()))
        if not rows:return CalibrationMetrics(capability,0,0.0,0.0,0.0,0.0)
        n=len(rows);acc=sum(r.correct for r in rows)/n;mc=sum(r.confidence for r in rows)/n
        brier=sum((r.confidence-(1.0 if r.correct else 0.0))**2 for r in rows)/n
        ece=0.0
        for b in range(self.bins):
            lo=b/self.bins;hi=(b+1)/self.bins
            bucket=[r for r in rows if r.confidence>=lo and (r.confidence<hi or (b==self.bins-1 and r.confidence<=hi))]
            if not bucket:continue
            w=len(bucket)/n;bc=sum(r.confidence for r in bucket)/len(bucket);ba=sum(r.correct for r in bucket)/len(bucket)
            ece+=w*abs(bc-ba)
        return CalibrationMetrics(capability,n,brier,ece,mc,acc)

    def update_self_model(self,self_model,capability):
        m=self.metrics(capability)
        if m.n:
            self_model.observe(capability,success=m.accuracy>=.5,calibration_error=m.ece)
        return m

    def abstention_pressure(self,capability,*,ece_threshold=.15,min_samples=10):
        m=self.metrics(capability)
        if m.n<min_samples:return 0.0
        return max(0.0,min(1.0,m.ece/max(ece_threshold,1e-9)-1.0))
