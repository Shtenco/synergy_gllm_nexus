from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json, sys
from benchmarks.ub2.generator.generate_ub2 import TRACK_COUNTS

BANNED = ('blind','shadow','split_dev','split_shadow','split_blind','р2а','р2б','р2д','р2ш')

@dataclass(frozen=True)
class ValidationReport:
    total_cases: int
    errors: tuple[str, ...]


def validate_suite(suite) -> ValidationReport:
    errors=[]
    counts={k:len(v) for k,v in suite.items()}
    if counts != TRACK_COUNTS:
        errors.append(f'count mismatch: {counts}')
    ids=[]
    for track,cases in suite.items():
        for c in cases:
            ids.append(c.case_id)
            blob=json.dumps(c.to_dict(), ensure_ascii=False).lower()
            if any(x in blob for x in BANNED):
                errors.append(f'split marker: {c.case_id}')
            if track=='graph_ood_reasoning':
                declared=c.metadata.get('declared_depth'); actual=len(c.metadata.get('path_edges',[]))
                if declared != actual or not (1 <= actual <= 8):
                    errors.append(f'graph depth mismatch: {c.case_id} declared={declared} actual={actual}')
            if track=='research_evidence':
                docs=set(c.metadata.get('evidence_doc_ids',[])); missing=set(c.contract.required_citations)-docs
                if missing:
                    errors.append(f'invalid evidence reference: {c.case_id} {sorted(missing)}')
            if track=='russian_coreference' and c.metadata.get('deterministic') and c.contract.clarification_required:
                errors.append(f'deterministic coreference cannot require clarification: {c.case_id}')
    if len(ids) != len(set(ids)):
        errors.append('duplicate case_id')
    return ValidationReport(sum(counts.values()), tuple(errors))


def _load_dir(path: Path):
    from benchmarks.ub2.schema import UB2Case, SemanticContract
    suite={}
    for track in TRACK_COUNTS:
        fp=path/f'{track}.jsonl'; rows=[]
        with fp.open(encoding='utf-8') as f:
            for line in f:
                d=json.loads(line)
                contract=SemanticContract(**{k: tuple(v) if isinstance(v,list) else v for k,v in d['contract'].items()})
                rows.append(UB2Case(d['case_id'],d['track'],d['prompt'],tuple(d['history']),contract,d['metadata']))
        suite[track]=rows
    return suite

if __name__ == '__main__':
    target=Path(sys.argv[1]); report=validate_suite(_load_dir(target))
    print(json.dumps({'total_cases':report.total_cases,'errors':list(report.errors)},ensure_ascii=False,indent=2))
    raise SystemExit(1 if report.errors else 0)
