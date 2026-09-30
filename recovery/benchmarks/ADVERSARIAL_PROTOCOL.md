# R1.3-X adversarial benchmark

This benchmark measures the decision layer, not historical neural checkpoints.

Every case uses the same proposal schema and is evaluated independently for:
- answer correctness
- abstention
- equal-authority contradiction detection
- exact-authority override
- provenance/evidence contribution
- counterfactual state change
- deterministic replay

Historical MoE figures (94.44% learned, 95.83% oracle) are retained as comparison targets only. They are not copied into current results and are not comparable unless the original frozen dataset and exact scoring protocol are recovered.
