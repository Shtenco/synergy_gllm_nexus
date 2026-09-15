from __future__ import annotations
from dataclasses import dataclass

@dataclass
class ResearchMetrics:
    factual_accuracy: float
    citation_precision: float
    citation_coverage: float
    evidence_graph_precision: float
    contradiction_detection: float

def evaluate(rows):
    n=max(1,len(rows))
    factual=sum(bool(r.get('answer_correct')) for r in rows)/n
    cited=[r for r in rows if r.get('uses_external')]
    cp=sum(bool(r.get('citations_correct')) for r in cited)/max(1,len(cited))
    cc=sum(bool(r.get('has_citations')) for r in cited)/max(1,len(cited))
    eg=sum(bool(r.get('graph_correct')) for r in rows)/n
    cd=sum(bool(r.get('contradiction_correct')) for r in rows if r.get('has_contradiction'))/max(1,sum(bool(r.get('has_contradiction')) for r in rows))
    return ResearchMetrics(factual,cp,cc,eg,cd)