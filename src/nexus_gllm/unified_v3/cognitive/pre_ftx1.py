from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import hashlib,json

@dataclass(frozen=True)
class PreFTX1Decision:
    allowed:bool
    reasons:tuple[str,...]
    evidence_sha256:str|None=None

class PreFTX1FreezeGate:
    """Hard gate: evidence readiness may freeze CRC-R1 but never opens FTX1."""
    REQUIRED_SCHEMA='nexus.crc_r1.validation.v2'
    REQUIRED_GATES=(
      'b2_beats_random_recall','b2_harmful_not_worse','b2_strict_not_worse',
      'hard_f_strict_ge_095','hard_f_representation_lt_fixed',
      'meta_g_strict_ge_090','meta_g_execution_ge_095','meta_g_planning_ge_095',
      'meta_g_memory_ge_095','meta_g_trace_complete',
      'memory_provenance_positive','future_gain_nonnegative',
      'credit_causal_gt_spurious','meta_compute_monotonic',
      'causal_accuracy_ge_095','causal_false_positive_zero','causal_beats_observation_only',
      'info_gain_selects_diagnostic','program_synthesis_selects_candidate',
    )
    def decide(self,evidence_path):
        p=Path(evidence_path)
        if not p.is_file():return PreFTX1Decision(False,('evidence_missing',),None)
        raw=p.read_bytes();sha=hashlib.sha256(raw).hexdigest()
        try:m=json.loads(raw)
        except Exception:return PreFTX1Decision(False,('evidence_invalid_json',),sha)
        reasons=[]
        if m.get('schema')!=self.REQUIRED_SCHEMA:reasons.append('validation_schema_mismatch')
        if m.get('ftx1_used') is not False:reasons.append('ftx1_boundary_violated')
        if m.get('hard_oos_d_reused_as_clean_oos') is not False:reasons.append('hard_oos_d_boundary_violated')
        gates=m.get('gates',{})
        for g in self.REQUIRED_GATES:
            if gates.get(g) is not True:reasons.append('gate_failed:'+g)
        if m.get('ready_for_pre_ftx1_freeze') is not True:reasons.append('manifest_not_ready')
        return PreFTX1Decision(not reasons,tuple(reasons),sha)
    def freeze(self,evidence_path,out_path,*,commit):
        d=self.decide(evidence_path)
        if not d.allowed:raise RuntimeError('pre-FTX1 freeze denied: '+','.join(d.reasons))
        payload={'schema':'nexus.crc_r1.pre_ftx1_freeze.v2','commit':commit,'evidence_sha256':d.evidence_sha256,'ftx1_opened':False,'status':'FROZEN_PRE_FTX1'}
        Path(out_path).write_text(json.dumps(payload,indent=2,sort_keys=True),encoding='utf-8');return payload
