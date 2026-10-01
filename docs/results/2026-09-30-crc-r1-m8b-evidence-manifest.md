# CRC-R1 M8b — Pre-FTX1 Evidence Manifest

M8b adds a machine-readable evidence gate instead of relying on prose conclusions.

The CI artifact now contains `PRE_FTX1_EVIDENCE_MANIFEST.json`, which records:
- exact commit;
- P1 integrity manifest;
- B2 routing gates relative to random control;
- HARD-OOS F strict/representation gates;
- memory provenance delta;
- learned future-planning delta;
- causal-vs-spurious credit separation;
- metacontrol compute monotonicity;
- explicit FTX1=false and HARD-OOS-D-clean-reuse=false.

`ready_for_pre_ftx1_freeze` becomes true only when every preregistered gate passes. The code does not open FTX1 automatically even when this flag is true.
