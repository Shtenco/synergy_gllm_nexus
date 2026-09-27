# Streaming trainer specification for NEXUS V5.
# Purpose: train a larger planner without precomputing a full feature matrix in RAM.
# Target architecture: 4096 combined RU features -> 1280 hidden -> 4 residual blocks -> 640 head.
# Approximate parameter count: ~19-20M.
# Training curriculum must include contrastive pairs where irrelevant facts are embedded
# naturally (parentheses, reference notes, not-X-but-Y, reordered clauses), not only
# explicit tokens such as "noise"/"ignore".
#
# HARD-OOS-E is development-only after its one-shot report.
# V5 must be frozen before a fresh HARD-OOS-F is generated/opened.
