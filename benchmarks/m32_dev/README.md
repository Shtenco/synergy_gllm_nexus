# M32-DEV

Fresh development benchmark for the M32 generalized-ingress architecture.

This corpus is **not** FTX1, is **not** clean OOS, and does **not** measure neural-model quality. It uses a deterministic fixture proposal backend so the benchmark isolates the deterministic M32 contracts and authority/execution plumbing.

Families: RU, EN, mixed-language, history, documents, composition, counterfactual, conflict, adversarial malformed provenance.

Acceptance targets:

- task admission >= 95% on cases expected to be admissible;
- admitted provenance validity = 100%;
- program admission >= 90% on solvable cases;
- end-to-end strict >= 80% on solvable cases;
- unsafe durable authority promotions = 0.

FTX1 is consumed and must never be used here as clean OOS or as a threshold-selection source.
