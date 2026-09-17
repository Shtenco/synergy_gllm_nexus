from __future__ import annotations

from dataclasses import dataclass, asdict
from difflib import SequenceMatcher
from collections import Counter, defaultdict
import hashlib
import re

from .schema import FTXCase, FTXGold, FTXPrediction
from .scoring import score_case
from .validators import normalized_skeleton, skeleton_overlap


def _flatten(bundle):
    for rows in bundle.values():
        yield from rows


def regex_baseline(case: FTXCase) -> FTXPrediction:
    text = case.prompt.strip()
    patterns = [
        r'^([А-ЯЁA-Z][\w-]+)\s+(?:хранит|владеет|активировал|передал|передала)\b',
        r'актуальным владельцем\s+\S+\s+является\s+([А-ЯЁA-Z][\w-]+)',
        r'отправителем\?$',
    ]
    m = re.search(patterns[0], text, re.IGNORECASE)
    if m:
        return FTXPrediction(answer=m.group(1))
    m = re.search(patterns[1], text, re.IGNORECASE)
    if m:
        return FTXPrediction(answer=m.group(1))
    if re.search(patterns[2], text, re.IGNORECASE):
        m2 = re.match(r'^([А-ЯЁA-Z][\w-]+)\s+', text)
        if m2:
            return FTXPrediction(answer=m2.group(1))
    if 'Ответь UNRESOLVED' in text:
        return FTXPrediction(answer='UNRESOLVED')
    return FTXPrediction()


def frequency_baseline(case: FTXCase, training_gold: list[FTXGold]) -> FTXPrediction:
    answers = [g.answer for g in training_gold if g.answer is not None]
    if not answers:
        return FTXPrediction()
    return FTXPrediction(answer=Counter(answers).most_common(1)[0][0])


def nearest_template_baseline(case: FTXCase, dev_pairs: list[tuple[FTXCase, FTXGold]]) -> FTXPrediction:
    target = normalized_skeleton(case)
    best = None
    best_score = -1.0
    for c,g in dev_pairs:
        score = SequenceMatcher(None, target, normalized_skeleton(c)).ratio()
        if score > best_score:
            best_score = score
            best = g
    return FTXPrediction(answer=best.answer if best else None)


def exact_template_baseline(case: FTXCase, dev_map: dict[str, str | None]) -> FTXPrediction:
    return FTXPrediction(answer=dev_map.get(normalized_skeleton(case)))


def metadata_only_baseline(case: FTXCase, answer_vocab: list[str]) -> FTXPrediction:
    if not answer_vocab:
        return FTXPrediction()
    h = int(hashlib.sha256(case.case_id.encode()).hexdigest()[:8], 16)
    return FTXPrediction(answer=answer_vocab[h % len(answer_vocab)])


def _acc(bundle, predict) -> float:
    rows = list(_flatten(bundle))
    if not rows:
        return 0.0
    return sum(score_case(g, predict(c)).strict for c,g in rows) / len(rows)


@dataclass(frozen=True)
class VetoReport:
    regex_accuracy: float
    nearest_template_accuracy: float
    exact_template_accuracy: float
    frequency_accuracy: float
    metadata_only_accuracy: float
    skeleton_overlap_dev: float
    skeleton_overlap_shadow: float
    pass_all: bool

    def to_dict(self):
        return asdict(self)


def run_veto(dev, shadow, blind) -> VetoReport:
    dev_pairs = list(_flatten(dev))
    training_gold = [g for _,g in dev_pairs]
    answer_vocab = sorted({g.answer for g in training_gold if g.answer is not None})
    by_skeleton: dict[str, list[str | None]] = defaultdict(list)
    for c,g in dev_pairs:
        by_skeleton[normalized_skeleton(c)].append(g.answer)
    dev_map = {sk: Counter(values).most_common(1)[0][0] for sk, values in by_skeleton.items()}
    regex = _acc(blind, regex_baseline)
    dev_by_track = defaultdict(list)
    for dc, dg in dev_pairs:
        dev_by_track[dc.track].append((normalized_skeleton(dc), dg.answer))

    def fast_nearest(c):
        target = normalized_skeleton(c)
        candidates = dev_by_track.get(c.track) or [(normalized_skeleton(dc), dg.answer) for dc,dg in dev_pairs]
        best_answer = None
        best_score = -1.0
        for sk, answer in candidates:
            score = SequenceMatcher(None, target, sk).ratio()
            if score > best_score:
                best_score = score
                best_answer = answer
        return FTXPrediction(answer=best_answer)

    nearest = _acc(blind, fast_nearest)
    exact = _acc(blind, lambda c: exact_template_baseline(c, dev_map))
    freq = _acc(blind, lambda c: frequency_baseline(c, training_gold))
    metadata = _acc(blind, lambda c: metadata_only_baseline(c, answer_vocab))
    ov_dev = skeleton_overlap(dev, blind)
    ov_shadow = skeleton_overlap(shadow, blind)
    passed = all((regex <= 0.40, nearest <= 0.45, exact <= 0.45, freq <= 0.30, metadata <= 0.20, ov_dev <= 0.05, ov_shadow <= 0.05))
    return VetoReport(regex, nearest, exact, freq, metadata, ov_dev, ov_shadow, passed)
