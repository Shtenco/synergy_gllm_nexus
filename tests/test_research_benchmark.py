from benchmarks.run_research_benchmark import evaluate

def test_metrics_separate_not_composite():
    m=evaluate([{'answer_correct':1,'uses_external':1,'citations_correct':1,'has_citations':1,'graph_correct':1,'has_contradiction':1,'contradiction_correct':1}])
    assert m.factual_accuracy==1 and m.citation_precision==1 and m.evidence_graph_precision==1
    assert not hasattr(m,'overall_score')