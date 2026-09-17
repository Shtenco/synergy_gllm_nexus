from __future__ import annotations

import re
from collections import defaultdict

from .schema import FTXCase, FTXGold

_NAME_WORDS = {
    'анна','борис','вера','глеб','ирина','лев','марта','павел','роман','софия','тимур','юлия',
    'марина','олег','алексей','нина','дарья','сергей','лидия','артем','артём','кирилл','елена',
}
_CANON = {
    'передала':'TRANSFER','передал':'TRANSFER','вручила':'TRANSFER','вручил':'TRANSFER',
    'отдала':'TRANSFER','отдал':'TRANSFER','доставила':'TRANSFER','доставил':'TRANSFER',
    'объект':'THING','предмет':'THING','пакет':'THING','посылку':'THING','посылка':'THING',
    'после':'AFTER','вслед':'AFTER','маркером':'SIGNAL','сигнала':'SIGNAL','сигнал':'SIGNAL',
    'отчёт':'DOC','отчет':'DOC','документ':'DOC','запись':'DOC',
}


def _norm_token(tok: str) -> str:
    low = tok.casefold()
    low = re.sub(r'\d+', '#', low)
    if low in _NAME_WORDS:
        return 'PERSON'
    if re.fullmatch(r'(сигма|омега|альфа|бета)[a-zа-я#_-]*', low):
        return 'NONCE'
    if re.fullmatch(r'(объект|предмет|пакет|узел|элемент)[-_]?#*', low):
        return 'THING'
    return _CANON.get(low, low)


def normalized_skeleton(case: FTXCase) -> str:
    text = case.prompt.casefold().replace('вслед за', 'после')
    tokens = re.findall(r'[a-zа-яё0-9_-]+|[^\w\s]', text, flags=re.IGNORECASE)
    norm = [_norm_token(t) for t in tokens]
    s = ' '.join(norm)
    s = re.sub(r'\b(?:борису|павлу|олегу|марине|ирине|анну|софии|тимуру|юлии)\b', 'PERSON', s)
    s = re.sub(r'\s+([.,:;!?])', r'\1', s)
    return s


def _flatten(bundle):
    if isinstance(bundle, dict):
        for rows in bundle.values():
            yield from rows
    else:
        yield from bundle


def skeleton_overlap(a, b) -> float:
    sa = {normalized_skeleton(c) for c,_ in _flatten(a)}
    sb = {normalized_skeleton(c) for c,_ in _flatten(b)}
    if not sb:
        return 0.0
    return len(sa & sb) / len(sb)


def validate_bundle(bundle) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    pair_semantics: dict[str, set[str | None]] = defaultdict(set)
    for case, gold in _flatten(bundle):
        if case.case_id in seen:
            errors.append(f'duplicate case_id: {case.case_id}')
        seen.add(case.case_id)
        if set(case.to_runtime_dict()) != {'case_id','prompt','history','documents'}:
            errors.append(f'forbidden runtime fields: {case.case_id}')
        if len(case.history) > 100:
            errors.append(f'history too long: {case.case_id}')
        if case.pair_group:
            pair_semantics[case.pair_group].add(gold.semantic_key)
        doc_ids = [d[0] for d in case.documents]
        if len(doc_ids) != len(set(doc_ids)):
            errors.append(f'duplicate document ids: {case.case_id}')
    for group, semantics in pair_semantics.items():
        if len(semantics) > 1:
            errors.append(f'pair_group semantic mismatch: {group}')
    return errors
