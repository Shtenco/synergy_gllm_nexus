# CRC-R1 M16 — Active Information Gain

**Date:** 2026-09-30

M16 gives CRC an explicit answer to: *what should I observe or test next?*

The selector represents a current hypothesis distribution and candidate queries/interventions with possible outcomes and posteriors. For each candidate it computes:

`IG = H(prior) - E[H(posterior)]`

and utility:

`IG - λ_cost·cost - λ_risk·risk`.

This prevents the MetaController from equating "more compute" with "more intelligence". A high-value query is one that is expected to collapse uncertainty efficiently, not merely one that is expensive or exhaustive.

The controlled benchmark includes:
- a diagnostic moderate-cost query;
- a cheap but almost uninformative query;
- a perfectly diagnostic but high-risk intervention.

With preregistered cost/risk weights, the safe diagnostic query wins.

M16 is a decision-theoretic query selector, not proof of autonomous scientific discovery. Its next integration is to let uncertain belief/causal states propose candidate observations while keeping external experiments behind the M13 action permit boundary.
