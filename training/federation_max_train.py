from __future__ import annotations

import argparse
import json
from pathlib import Path

from training.v3_moe.train_router import run_training


def load_curriculum(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    weights = data["data"]
    total = sum(float(v) for v in weights.values())
    if abs(total - 1.0) > 1e-9:
        raise ValueError(f"curriculum data weights must sum to 1.0, got {total}")
    if data["promotion_gates"]["blind_sets_allowed_in_training"]:
        raise ValueError("blind sets must remain excluded from training")
    seals = data["seals"]
    if seals["m32_meta_opened"] or seals["ftx2_authored"] or seals["third_blind_corpus_authored"]:
        raise ValueError("research seal violation")
    return data


def run_router_stage(cfg: dict, out: Path) -> dict:
    rcfg = cfg["federation"]["router"]
    result = run_training(
        out,
        train_n=int(rcfg["train_n"]),
        dev_n=int(rcfg["dev_n"]),
        oos_n=int(rcfg["oos_n"]),
        seed=20261020,
        epochs=int(rcfg["epochs"]),
    )
    metrics = result["metrics"]
    gates = cfg["promotion_gates"]
    checks = {
        "strict_routing_success": metrics.get("strict_routing_success", 0.0) >= gates["router_strict_success_min"],
        "useful_expert_recall": metrics.get("useful_expert_recall", 0.0) >= gates["router_useful_recall_min"],
        "moe_gain_positive": metrics.get("moe_gain_over_best_single", -1.0) > 0.0,
    }
    result["promotion_checks"] = checks
    result["router_stage_pass"] = all(checks.values())
    return result


def main() -> None:
    p = argparse.ArgumentParser(description="NEXUS maximal federation curriculum orchestrator")
    p.add_argument("--curriculum", type=Path, default=Path("training/federation_max_curriculum.json"))
    p.add_argument("--out", type=Path, default=Path("artifacts/federation_max_train/router"))
    p.add_argument("--router-only", action="store_true", help="Run the CPU-compatible federation router stage")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    cfg = load_curriculum(args.curriculum)
    if args.dry_run:
        print(json.dumps({
            "curriculum": cfg["name"],
            "data_weights": cfg["data"],
            "federation": cfg["federation"],
            "replay": cfg["replay"],
            "promotion_gates": cfg["promotion_gates"],
            "seals": cfg["seals"],
        }, ensure_ascii=False, indent=2))
        return

    if args.router_only:
        args.out.mkdir(parents=True, exist_ok=True)
        result = run_router_stage(cfg, args.out)
        (args.out / "federation_max_router_result.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return

    raise SystemExit(
        "Neural checkpoint continuation intentionally requires the recovered nexus_omega_20x trainer + GPU. "
        "Use --router-only now; do not silently retrain last.pt with a different architecture."
    )


if __name__ == "__main__":
    main()
