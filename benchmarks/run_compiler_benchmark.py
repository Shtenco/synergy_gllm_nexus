from __future__ import annotations

import argparse
import json
from pathlib import Path

from nexus_gllm.compiler_neural import NeuralRussianGraphCompiler
from nexus_gllm.compiler_proposal import NeuralParseProposal, ProposalValidator
from training.dataset import GLLMDataset


def _same_span(pred: tuple[int, int] | None, gold) -> bool:
    if pred is None or gold is None:
        return pred is None and gold is None
    return tuple(gold) == tuple(pred)


def score_compiler_predictions(rows: list[dict], predictions: list[NeuralParseProposal]) -> dict:
    if len(rows) != len(predictions):
        raise ValueError("rows/predictions length mismatch")
    validator = ProposalValidator()
    relation_correct = 0
    subject_correct = 0
    object_correct = 0
    strict_correct = 0
    invalid_accepted = 0
    abstain_tp = abstain_fp = abstain_fn = 0

    for row, pred in zip(rows, predictions):
        gold = row["compiler_target"]
        relation_ok = pred.relation == gold["relation"]
        subject_ok = _same_span(pred.subject_span, gold.get("subject_span"))
        object_ok = _same_span(pred.object_span, gold.get("object_span"))
        relation_correct += int(relation_ok)
        subject_correct += int(subject_ok)
        object_correct += int(object_ok)
        strict_correct += int(relation_ok and subject_ok and object_ok)

        validation = validator.validate(row["input_text"], pred)
        if validation.accepted and not validation.is_abstention and not (relation_ok and subject_ok and object_ok):
            invalid_accepted += 1

        gold_abstain = gold["relation"] == "abstain"
        pred_abstain = pred.relation == "abstain"
        abstain_tp += int(gold_abstain and pred_abstain)
        abstain_fp += int((not gold_abstain) and pred_abstain)
        abstain_fn += int(gold_abstain and (not pred_abstain))

    total = len(rows)
    precision_den = abstain_tp + abstain_fp
    recall_den = abstain_tp + abstain_fn
    return {
        "total": total,
        "relation_accuracy": relation_correct / total if total else 0.0,
        "subject_span_exact": subject_correct / total if total else 0.0,
        "object_span_exact": object_correct / total if total else 0.0,
        "strict_structural_exact_match": strict_correct / total if total else 0.0,
        "invalid_accepted_proposal_rate": invalid_accepted / total if total else 0.0,
        "abstention_precision": abstain_tp / precision_den if precision_den else 1.0,
        "abstention_recall": abstain_tp / recall_den if recall_den else 1.0,
    }


def run(data: Path, checkpoint: Path, split: str = "blind") -> dict:
    ds = GLLMDataset(data, split=split)
    model, vocab, relations, meta = NeuralRussianGraphCompiler.load_checkpoint(checkpoint)
    predictions = [model.predict(row["input_text"], vocab, relations) for row in ds.rows]
    metrics = score_compiler_predictions(ds.rows, predictions)
    return {
        "split": split,
        "checkpoint_meta": meta,
        "metrics": metrics,
        "results": [
            {
                "id": row["id"],
                "gold": row["compiler_target"],
                "prediction": pred.__dict__,
            }
            for row, pred in zip(ds.rows, predictions)
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("data", type=Path)
    parser.add_argument("checkpoint", type=Path)
    parser.add_argument("--split", default="blind")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = run(args.data, args.checkpoint, args.split)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
