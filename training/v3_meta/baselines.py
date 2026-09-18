def simplicity_accuracy(rows):
    return sum(int(0==r.gold_index) for r in rows)/len(rows) if rows else 0.0
def explained_accuracy(rows):
    return sum(int(max(range(len(r.candidates)),key=lambda i:r.candidates[i].explained)==r.gold_index) for r in rows)/len(rows) if rows else 0.0
