# CRC-R1 GitHub Validation Workflow

The `crc-r1-validation` workflow executes the scientific gates from an exact Git commit on GitHub-hosted Ubuntu:

1. focused CRC/MoE/HARD-OOS regression tests;
2. compileall;
3. exact P1 SHA-256 integrity generation;
4. sealed B2 one-shot with frozen P1;
5. sealed HARD-OOS F one-shot;
6. M8 component ablation;
7. SHA-256 evidence ledger;
8. immutable workflow artifact upload.

The workflow does not run FTX1.

The evidence artifact is intentionally generated in CI rather than claimed from an unexecuted source tree.
