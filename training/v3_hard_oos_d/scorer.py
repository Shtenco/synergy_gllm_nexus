from collections import defaultdict

def _basic(rows):
    n=len(rows) or 1
    return {'answer_accuracy':sum(bool(r.get('correct')) for r in rows)/n,'representation_failure_rate':sum(bool(r.get('representation_failure')) for r in rows)/n}
def score_records(rows):
    out=_basic(rows); groups=defaultdict(list)
    for r in rows: groups[r['stratum']].append(r)
    out['by_stratum']={k:_basic(v) for k,v in groups.items()}
    return out

def expected_calibration_error(records,bins=10):
    if not records:return 0.0
    e=0.0; n=len(records)
    for b in range(bins):
        lo=b/bins; hi=(b+1)/bins
        xs=[r for r in records if lo<=r['confidence']<hi or (b==bins-1 and r['confidence']==1)]
        if xs:
            conf=sum(r['confidence'] for r in xs)/len(xs); acc=sum(r['correct'] for r in xs)/len(xs); e += len(xs)/n*abs(conf-acc)
    return e
