from __future__ import annotations

import argparse
import json
from pathlib import Path

from benchmarks.m32_dev.generator import generate
from nexus_gllm.unified_v3.cognitive.generalized_ingress import GeneralizedIngressRequest
from nexus_gllm.unified_v3.cognitive.generalized_ingress_llamacpp import (
    LlamaCppGeneralizedIngressBackend,
    LlamaCppModelRef,
    LlamaCppTransport,
)


class RecordingTransport:
    """Capture raw OpenAI-compatible responses without altering backend semantics."""

    def __init__(self, inner=None):
        self.inner = inner or LlamaCppTransport()
        self.last_response = None

    def post_json(self, url, payload, timeout_s):
        self.last_response = self.inner.post_json(url, payload, timeout_s)
        return self.last_response


def _unique_cases(seed: int = 32001, n_per_family: int = 20):
    seen = set()
    out = []
    for case in generate(seed, n_per_family):
        key = (case.prompt, tuple(case.history), tuple(case.documents))
        if key in seen:
            continue
        seen.add(key)
        out.append(case)
    return tuple(out)


def run(*, model_path: str, endpoint: str, expected_sha256: str, max_tokens: int = 192, seed: int = 32001):
    transport = RecordingTransport()
    backend = LlamaCppGeneralizedIngressBackend(
        LlamaCppModelRef(
            model_path=model_path,
            expected_sha256=expected_sha256,
            endpoint=endpoint,
            timeout_s=60.0,
            seed=42,
            max_tokens=int(max_tokens),
        ),
        transport=transport,
    )

    rows = []
    for case in _unique_cases(seed):
        request = GeneralizedIngressRequest.from_texts(case.prompt, case.history, case.documents)
        transport.last_response = None
        exc_type = None
        exc_message = None
        proposal_ok = False
        try:
            backend.propose(request)
            proposal_ok = True
        except Exception as exc:  # diagnostic only; preserve exact backend behavior
            exc_type = type(exc).__name__
            exc_message = str(exc)

        response = transport.last_response or {}
        choice = None
        try:
            choice = response.get("choices", [None])[0]
        except Exception:
            choice = None
        if not isinstance(choice, dict):
            choice = {}
        message = choice.get("message") if isinstance(choice.get("message"), dict) else {}
        raw = message.get("content")
        raw = raw if isinstance(raw, str) else None

        rows.append({
            "case_id": case.case_id,
            "family": case.family,
            "source_texts": {
                "prompt": case.prompt,
                "history": list(case.history),
                "documents": list(case.documents),
            },
            "proposal_ok": proposal_ok,
            "exception_type": exc_type,
            "exception_message": exc_message,
            "finish_reason": choice.get("finish_reason"),
            "raw_content": raw,
            "raw_content_chars": None if raw is None else len(raw),
            "response_keys": sorted(response.keys()) if isinstance(response, dict) else [],
        })

    return {
        "schema": "nexus.m32_1.neural_dev.diagnostic.v1",
        "model_sha256": backend.verified_model_sha256,
        "generation": {"temperature": 0.0, "seed": 42, "max_tokens": int(max_tokens)},
        "unique_inputs": len(rows),
        "rows": rows,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--sha256", required=True)
    ap.add_argument("--endpoint", default="http://127.0.0.1:8080")
    ap.add_argument("--max-tokens", type=int, default=192)
    ap.add_argument("--seed", type=int, default=32001)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    report = run(
        model_path=args.model,
        endpoint=args.endpoint,
        expected_sha256=args.sha256,
        max_tokens=args.max_tokens,
        seed=args.seed,
    )
    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    Path(args.output).write_text(text + "\n", encoding="utf-8")
    print(json.dumps({
        "unique_inputs": report["unique_inputs"],
        "proposal_ok": sum(1 for row in report["rows"] if row["proposal_ok"]),
        "exceptions": [
            {"family": row["family"], "type": row["exception_type"], "message": row["exception_message"], "finish_reason": row["finish_reason"]}
            for row in report["rows"]
        ],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
