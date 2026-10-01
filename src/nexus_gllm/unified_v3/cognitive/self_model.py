from dataclasses import dataclass,replace
@dataclass(frozen=True)
class CapabilityEstimate:
    capability:str;successes:float=0.0;failures:float=0.0;credit_mass:float=0.0;latency_ms_ema:float=0.0;calibration_error_ema:float=0.0
    @property
    def reliability(self): return (self.successes+1.0)/(self.successes+self.failures+2.0)
class NexusSelfModel:
    def __init__(self): self._caps={}
    def get(self,capability): return self._caps.get(capability,CapabilityEstimate(capability))
    def observe(self,capability,*,success,credit=0.0,latency_ms=None,calibration_error=None):
        x=self.get(capability);a=.10
        x=replace(x,successes=x.successes+(1 if success else 0),failures=x.failures+(0 if success else 1),credit_mass=x.credit_mass+float(credit),latency_ms_ema=x.latency_ms_ema if latency_ms is None else (1-a)*x.latency_ms_ema+a*float(latency_ms),calibration_error_ema=x.calibration_error_ema if calibration_error is None else (1-a)*x.calibration_error_ema+a*float(calibration_error))
        self._caps[capability]=x;return x
    def snapshot(self): return tuple(sorted(self._caps.values(),key=lambda x:x.capability))
