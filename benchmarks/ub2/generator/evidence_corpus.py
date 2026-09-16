from benchmarks.ub2.schema import EvidenceDocument

def build_corpus() -> tuple[EvidenceDocument, ...]:
    docs = []
    for i in range(120):
        fact = i % 20
        stance = 'подтверждает' if i % 5 != 0 else 'оспаривает'
        docs.append(EvidenceDocument(
            doc_id=f'doc-{i:03d}',
            source_family=f'Источник {i % 12 + 1}',
            text=f'Документ {i} {stance} утверждение F{fact}.',
            independent_group=f'g{i % 24:02d}',
        ))
    return tuple(docs)
