# R1.3-X / Unified V3 integration

The integration is deliberately an adapter, not a fork of Unified V3.

Pipeline:
1. EvidenceRouter ranks proposals without deleting alternatives.
2. Blackboard retains every competing hypothesis.
3. Existing R1.3-X Verifier upgrades exact-verifiable proposals.
4. Unified V3 CounterfactualEngine applies interventions to a world hypothesis.
5. Unified V3 EpistemicController classifies boolean evidence.
6. WorldConsistency rejects proposals explicitly marked inconsistent.
7. Authority Governor resolves the surviving set or abstains.
8. A deterministic replay hash is emitted from the complete decision inputs.

The adapter does not claim that historical V4.2/V5.7 weights have been recovered. Those remain immutable recovery leads until exact bytes are located and hash-verified.
