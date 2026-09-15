from __future__ import annotations

import argparse
import json
from pathlib import Path

from nexus_gllm.graph import DynamicHyperGraph
from nexus_gllm.temporal import EventGraphReasoner


def run_temporal_smoke() -> dict:
    cases = []

    graph = DynamicHyperGraph()
    temporal = EventGraphReasoner(graph)
    a = temporal.ensure_event("А")
    b = temporal.ensure_event("Б")
    c = temporal.ensure_event("В")
    temporal.add_before(a, b)
    temporal.add_before(b, c)
    cases.append(("one_hop_before", temporal.before(a, b).holds))
    cases.append(("multi_hop_before", temporal.before(a, c).holds))

    cause_graph = DynamicHyperGraph()
    causal = EventGraphReasoner(cause_graph)
    x = causal.ensure_event("Причина")
    y = causal.ensure_event("Промежуточное")
    z = causal.ensure_event("Следствие")
    causal.add_cause(x, y)
    causal.add_cause(y, z)
    cases.append(("multi_hop_causal", causal.causes(x, z).holds))

    cycle_rejected = False
    try:
        temporal.add_before(c, a)
    except ValueError:
        cycle_rejected = True
    cases.append(("cycle_rejection", cycle_rejected))

    retract_graph = DynamicHyperGraph()
    retract = EventGraphReasoner(retract_graph)
    r1 = retract.ensure_event("Р1")
    r2 = retract.ensure_event("Р2")
    edge_id = retract.add_before(r1, r2)
    retract_graph.retract_edge(edge_id)
    cases.append(("retraction_aware", not retract.before(r1, r2).holds))

    passed = sum(1 for _, ok in cases if ok)
    return {
        "total": len(cases),
        "passed": passed,
        "accuracy": passed / len(cases) if cases else 0.0,
        "cases": [{"name": name, "passed": bool(ok)} for name, ok in cases],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = run_temporal_smoke()
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
