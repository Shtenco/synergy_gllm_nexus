# CRC-R1 M29 — Pre-FTX1 Validation Contract v3

**Date:** 2026-09-30

validation.v3 supersedes v2 after explicit negative higher-order semantics and the sealed HARD-OOS F2 protocol.

New mandatory gates:
- hard_f2_strict_ge_095
- hard_f2_representation_lt_fixed
- hard_f2_all_strata_ge_095

GitHub CI and the portable validator now execute F2 independently and persist its evidence before building the pre-FTX1 manifest.

The freeze gate rejects validation.v2 even when every v2 gate passes. Passing v3 still does not open FTX1; it only permits creation of FROZEN_PRE_FTX1.
