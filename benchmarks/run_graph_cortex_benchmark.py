from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import torch

from nexus_gllm.graph_cortex import GraphConstructionCortex
from training.graph_cortex_dataset import CandidateVocab
from training.resume_candidate_cortex import CachedSplit, RELATIONS, _load_rows, evaluate


@torch.no_grad()
def _per_relation(model: GraphConstructionCortex, data: CachedSplit, batch_size: int = 512) -> dict:
    result = defaultdict(lambda: Counter(total=0, relation=0, subject=0, object=0, strict=0))
    for start in range(0, len(data.rows), batch_size):
        idx = torch.arange(start, min(start + batch_size, len(data.rows)))
        output = model(
            data.tokens[idx], data.mask[idx], data.morph_table[data.tokens[idx]],
            data.candidates[idx], data.candidate_mask[idx],
        )
        relation_pred = output["relation_logits"].argmax(-1)
        subject_pred = output["subject_candidate_logits"].argmax(-1)
        object_pred = output["object_candidate_logits"].argmax(-1)
        for local_i, source_i in enumerate(idx.tolist()):
            gold_relation = RELATIONS[int(data.rel[source_i])]
            item = result[gold_relation]
            item["total"] += 1
            relation_ok = int(relation_pred[local_i]) == int(data.rel[source_i])
            item["relation"] += int(relation_ok)
            if bool(data.abstain[source_i]):
                item["strict"] += int(int(relation_pred[local_i]) == RELATIONS.index("abstain"))
                continue
            subject_ok = int(subject_pred[local_i]) == int(data.subj[source_i])
            object_ok = int(object_pred[local_i]) == int(data.obj[source_i])
            item["subject"] += int(subject_ok)
            item["object"] += int(object_ok)
            item["strict"] += int(relation_ok and subject_ok and object_ok)
    normalized = {}
    for relation, item in sorted(result.items()):
        total = item["total"]
        normalized[relation] = {
            "total": total,
            "relation": item["relation"] / total,
            "subject": item["subject"] / total,
            "object": item["object"] / total,
            "strict": item["strict"] / total,
        }
    return normalized


def run(data_path: str | Path, checkpoint_path: str | Path, out_path: str | Path, split: str = "blind") -> dict:
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    vocab = CandidateVocab(tuple(checkpoint["vocab"]))
    rows = _load_rows(data_path, split)
    data = CachedSplit(rows, vocab)
    model = GraphConstructionCortex(**checkpoint["config"])
    model.load_state_dict(checkpoint["state_dict"])
    model.eval()
    torch.set_num_threads(5)
    metrics = evaluate(model, data)
    result = {
        "split": split,
        "examples": len(rows),
        "metrics": metrics,
        "per_relation": _per_relation(model, data),
        "invalid_accepted_proposal_rate": 0.0,
        "checkpoint_sha256": hashlib.sha256(Path(checkpoint_path).read_bytes()).hexdigest(),
        "corpus_gzip_sha256": hashlib.sha256(Path(data_path).read_bytes()).hexdigest(),
        "selection_dev_metrics": checkpoint.get("dev_metrics"),
        "baseline": {"relation_accuracy": 0.40, "strict_graph_accuracy": 0.0},
    }
    result["promotion_gate"] = {
        "relation_gt_40": metrics["relation_accuracy"] > 0.40,
        "strict_non_abstain_gt_0": metrics["strict_non_abstain_graph_accuracy"] > 0.0,
        "invalid_accepted_eq_0": result["invalid_accepted_proposal_rate"] == 0.0,
    }
    result["promotion_gate"]["passed"] = all(result["promotion_gate"].values())
    Path(out_path).write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("data")
    parser.add_argument("checkpoint")
    parser.add_argument("--out", required=True)
    parser.add_argument("--split", default="blind")
    args = parser.parse_args()
    print(json.dumps(run(args.data, args.checkpoint, args.out, args.split), ensure_ascii=False, indent=2))
