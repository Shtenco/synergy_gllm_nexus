from collections import defaultdict
from dataclasses import dataclass
from .generator import EXPERTS
@dataclass(frozen=True)
class Route: selected:tuple[str,...];probabilities:tuple[tuple[str,float],...]=();abstain:bool=False
def _oracle(gold,k=3):
    order=sorted(range(len(EXPERTS)),key=lambda j:(-gold.utility[j],j));return Route(tuple(EXPERTS[j] for j in order[:k]),(),gold.should_abstain)
def score(runtime,gold,routes):
    gm={g.case_id:g for g in gold};rm={c.case_id:r for c,r in zip(runtime,routes)};agg=defaultdict(lambda:{'n':0,'useful_hit':0,'useful_total':0,'harmful':0,'selected':0,'strict':0,'abstain_correct':0,'regret':0.0})
    for c in runtime:
        g=gm[c.case_id];r=rm[c.case_id];a=agg[c.stratum];a['n']+=1;ss=set(r.selected);uu=set(g.useful);hh=set(g.harmful);a['useful_hit']+=len(ss&uu);a['useful_total']+=len(uu);a['harmful']+=len(ss&hh);a['selected']+=len(ss);a['strict']+=int(uu.issubset(ss) and not(ss&hh)) if uu else int(r.abstain);a['abstain_correct']+=int(bool(r.abstain)==bool(g.should_abstain));chosen=max((g.utility[EXPERTS.index(e)] for e in r.selected if e in EXPERTS),default=0.0);a['regret']+=max(g.utility)-chosen if not g.should_abstain else max(0.0,chosen)
    def finish(a):
        n=max(1,a['n']);return {'n':a['n'],'useful_recall':a['useful_hit']/max(1,a['useful_total']),'harmful_selection_rate':a['harmful']/max(1,a['selected']),'strict_success':a['strict']/n,'abstention_accuracy':a['abstain_correct']/n,'mean_routing_regret':a['regret']/n}
    keys=next(iter(agg.values()));overall={k:sum(v[k] for v in agg.values()) for k in keys};return {'overall':finish(overall),'by_stratum':{s:finish(a) for s,a in sorted(agg.items())}}
def random_routes(runtime,seed=41,k=3):
    import random;rng=random.Random(seed);return tuple(Route(tuple(rng.sample(list(EXPERTS),k))) for _ in runtime)
def oracle_routes(runtime,gold,k=3):
    gm={g.case_id:g for g in gold};return tuple(_oracle(gm[c.case_id],k) for c in runtime)
