from collections import Counter
def lineage_independence_weight(specs):
    c=Counter(s.lineage_group for s in specs)
    return {s.expert_id:1.0/c[s.lineage_group] for s in specs}
