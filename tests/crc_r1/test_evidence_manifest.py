import json
from pathlib import Path
from benchmarks.crc_m8.evidence_manifest import build
def test_evidence_manifest_requires_all_gates(tmp_path):
    (tmp_path/'b2').mkdir();(tmp_path/'hard_oos_f').mkdir()
    (tmp_path/'b2'/'one_shot_result.json').write_text(json.dumps({'learned_or_candidate':{'overall':{'useful_recall':.8,'harmful_selection_rate':.1,'strict_success':.7}},'random':{'overall':{'useful_recall':.5,'harmful_selection_rate':.3,'strict_success':.4}}}))
    (tmp_path/'hard_oos_f'/'one_shot_result.json').write_text(json.dumps({'crc_r1':{'strict_accuracy':1.0,'representation_failure_rate':0},'fixed_basis':{'representation_failure_rate':1.0}}))
    (tmp_path/'m8_ablation.json').write_text(json.dumps({'memory':{'delta_provenance':1},'future':{'delta_accuracy':.1},'credit':{'causal_minus_spurious_trust':.2},'meta':{'depth_delta':1,'expert_delta':1}}))
    (tmp_path/'p1_integrity.sha256.json').write_text(json.dumps({'sha256':{'x':'y'}}))
    m=build(tmp_path,commit='abc');assert m['ready_for_pre_ftx1_freeze'] and all(m['gates'].values()) and not m['ftx1_used']
