from __future__ import annotations
import json
from pathlib import Path
from benchmarks.hard_oos_f.generator import generate as gen_f
from benchmarks.hard_oos_f.runner import crc_predict,fixed_basis_predict
from benchmarks.hard_oos_f.scorer import score as score_f
from benchmarks.memory_m5.generator import generate as gen_mem
from benchmarks.memory_m5.runner import hierarchical_predict,flat_predict
from benchmarks.memory_m5.scorer import score as score_mem
from benchmarks.future_m5.generator import generate as gen_future
from benchmarks.future_m5.runner import first_action_accuracy
from benchmarks.credit_m6.run import run as run_credit
from nexus_gllm.unified_v3.cognitive.meta_controller import MetaController
from nexus_gllm.unified_v3.cognitive.state import ComputeBudget

def _program(seed=101,n=20):
    b=gen_f(seed=seed,n_per_stratum=n)
    fixed=score_f(b.runtime,b.gold,tuple(fixed_basis_predict(c) for c in b.runtime))
    crc=score_f(b.runtime,b.gold,tuple(crc_predict(c) for c in b.runtime))
    return {'fixed_basis':fixed,'crc':crc,'delta_strict_accuracy':crc['strict_accuracy']-fixed['strict_accuracy'],'delta_representation_failure':crc['representation_failure_rate']-fixed['representation_failure_rate']}

def _memory(seed=102,n=80,distractors=80):
    cases=gen_mem(seed=seed,n=n,distractors=distractors)
    flat=score_mem(cases,tuple(flat_predict(c,32) for c in cases))
    hier=score_mem(cases,tuple(hierarchical_predict(c) for c in cases))
    return {'flat_window':flat,'hierarchical':hier,'delta_value_accuracy':hier['current_value_accuracy']-flat['current_value_accuracy'],'delta_provenance':hier['raw_provenance_success']-flat['raw_provenance_success']}

def _future(seed=103,n=100):
    envs=gen_future(seed=seed,n=n)
    d1=first_action_accuracy(envs,1);d3=first_action_accuracy(envs,3)
    return {'depth1_accuracy':d1,'depth3_accuracy':d3,'delta_accuracy':d3-d1}

def _credit():
    x=run_credit(episodes=200)
    return {**x,'causal_minus_spurious_trust':x['causal_trust']-x['spurious_trust']}

def _meta():
    m=MetaController();b=ComputeBudget(1,3,4,4,16)
    easy=m.decide(novelty=.1,uncertainty=.1,budget=b)
    hard=m.decide(novelty=.9,uncertainty=.85,budget=b)
    return {'easy':easy.__dict__,'hard':hard.__dict__,'depth_delta':hard.branch_depth-easy.branch_depth,'expert_delta':hard.expert_top_k-easy.expert_top_k,'memory_delta':hard.memory_limit-easy.memory_limit}

def run_all():
    return {'program':_program(),'memory':_memory(),'future':_future(),'credit':_credit(),'meta':_meta(),'scientific_boundary':'Component ablations on internal synthetic/controlled benchmarks; not an end-to-end AGI score.'}

def main():
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--out');a=ap.parse_args()
    result=run_all();text=json.dumps(result,indent=2,sort_keys=True)
    if a.out:
        p=Path(a.out);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8')
    print(text)
if __name__=='__main__':main()
