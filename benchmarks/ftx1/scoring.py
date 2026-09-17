from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping

from .schema import CaseScore, FTXCase, FTXGold, FTXPrediction, SuiteScore, TrackScore


def _canon(value: str | None) -> str | None:
    if value is None:
        return None
    return ' '.join(value.strip().casefold().split())


def score_case(gold: FTXGold, prediction: FTXPrediction) -> CaseScore:
    answer_ok = _canon(gold.answer) == _canon(prediction.answer)
    structured_ok = tuple(_canon(v) for v in gold.structured) == tuple(_canon(v) for v in prediction.structured)
    epistemic_ok = _canon(gold.epistemic) == _canon(prediction.epistemic)
    abstain_ok = gold.abstain is prediction.abstain
    citations_ok = tuple(sorted(gold.citations)) == tuple(sorted(prediction.citations))
    strict = all((answer_ok, structured_ok, epistemic_ok, abstain_ok, citations_ok))
    return CaseScore(strict, answer_ok, structured_ok, epistemic_ok, abstain_ok, citations_ok)


def score_suite(
    pairs: Iterable[tuple[FTXCase, FTXGold]],
    predictions: Mapping[str, FTXPrediction],
) -> SuiteScore:
    by_track: dict[str, list[bool]] = defaultdict(list)
    all_scores: list[bool] = []
    for case, gold in pairs:
        pred = predictions.get(case.case_id, FTXPrediction())
        strict = score_case(gold, pred).strict
        by_track[case.track].append(strict)
        all_scores.append(strict)
    tracks = tuple(
        TrackScore(track=t, correct=sum(values), total=len(values))
        for t, values in sorted(by_track.items())
    )
    full = sum(all_scores) / len(all_scores) if all_scores else 0.0
    macro = sum(t.strict for t in tracks) / len(tracks) if tracks else 0.0
    return SuiteScore(full_strict=full, macro_strict=macro, tracks=tracks)
