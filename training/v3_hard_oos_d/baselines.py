import random
def _acc(rows,pick): return sum(int(pick(r)==r.gold_index) for r in rows)/len(rows)
def random_accuracy(rows):
    rng=random.Random(991); return _acc(rows,lambda r:rng.randrange(len(r.candidates)))
def simplicity_accuracy(rows): return _acc(rows,lambda r:min(range(len(r.candidates)),key=lambda i:r.candidates[i].complexity))
def explained_accuracy(rows): return _acc(rows,lambda r:max(range(len(r.candidates)),key=lambda i:r.candidates[i].explained))
def contradiction_accuracy(rows): return _acc(rows,lambda r:min(range(len(r.candidates)),key=lambda i:r.candidates[i].contradictions))
def always_transitive_accuracy(rows): return _acc(rows,lambda r:0)
