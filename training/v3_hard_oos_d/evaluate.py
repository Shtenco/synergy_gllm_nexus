from __future__ import annotations
from pathlib import Path
import json,torch
from training.v3_meta.ranker import Net
from .adapter import compat_features
from .generator import HardOOSDGenerator
from .seal import verify_checkpoint_hash,canonical_corpus_hash
from .baselines import *
from .scorer import expected_calibration_error

def evaluate_zero_shot(manifest_path,checkpoint_path,output_dir=None):
    manifest=json.loads(Path(manifest_path).read_text(encoding='utf-8'))
    if not manifest.get('sealed_before_evaluation'): raise ValueError('D manifest is not sealed')
    verify_checkpoint_hash(checkpoint_path,manifest['model_sha256'])
    rows=HardOOSDGenerator(manifest['seed']).generate()
    if canonical_corpus_hash(rows)!=manifest['corpus_sha256']: raise ValueError('corpus hash mismatch')
    model=Net(8); model.load_state_dict(torch.load(checkpoint_path,map_location='cpu',weights_only=True)); model.eval()
    records=[]; by={}
    with torch.no_grad():
        for r in rows:
            x=torch.tensor([compat_features(r,c) for c in r.candidates],dtype=torch.float32)
            scores=model(x); probs=torch.softmax(scores,dim=0); pred=int(scores.argmax())
            correct=pred==r.gold_index
            known_topology=False
            records.append({'stratum':r.stratum,'correct':correct,'representation_failure':not known_topology,'confidence':float(probs[pred]),'gold_positive':r.answer_positive})
    for s in sorted({r.stratum for r in rows}):
        xs=[z for z in records if z['stratum']==s]; by[s]={'ranking_accuracy':sum(z['correct'] for z in xs)/len(xs),'representation_failure_rate':sum(z['representation_failure'] for z in xs)/len(xs)}
    rank=sum(z['correct'] for z in records)/len(records)
    metrics={'hypothesis_ranking_accuracy':rank,'answer_accuracy':rank,'ast_topology_exact':0.0,'ast_topology_partial':0.0,'prediction_accuracy':rank,'counterfactual_accuracy':0.0,'temporal_accuracy':0.0,'inhibitor_accuracy':0.0,'binding_resolution_accuracy':0.0,'abstention_accuracy':0.0,'rename_invariance':0.0,'hypothesis_stability':0.0,'theory_revision_score':0.0,'calibration_ece':expected_calibration_error(records),'representation_failure_rate':1.0,'by_stratum':by}
    baselines={'random':random_accuracy(rows),'simplicity':simplicity_accuracy(rows),'explained':explained_accuracy(rows),'contradiction':contradiction_accuracy(rows),'always_transitive':always_transitive_accuracy(rows)}
    if output_dir:
        out=Path(output_dir); out.mkdir(parents=True,exist_ok=True)
        (out/'zero_shot_metrics.json').write_text(json.dumps(metrics,indent=2,sort_keys=True),encoding='utf-8'); (out/'baseline_metrics.json').write_text(json.dumps(baselines,indent=2,sort_keys=True),encoding='utf-8')
    return {'metrics':metrics,'baselines':baselines}
