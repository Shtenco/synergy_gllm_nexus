from nexus_gllm.research.scheduler import ResearchScheduler
from nexus_gllm.research.types import ResearchNeed

def test_scheduler_utility_and_termination():
    s=ResearchScheduler(max_queries=2,epsilon=.1)
    a=ResearchNeed('a',importance=1,novelty=1,expected_gain=3,cost=1)
    b=ResearchNeed('b',importance=1,novelty=.5,expected_gain=1,cost=1)
    assert s.choose([b,a]).query=='a'
    s.record('a'); assert s.choose([a]) is None