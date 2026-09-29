# CRC-R1 M19 — Online Confidence Calibration

**Date:** 2026-09-30

CRC already tracked uncertainty and stored a calibration-error field in SelfModel, but no component computed calibration from actual confidence/outcome pairs. M19 closes that gap.

`CalibrationLedger` records per-capability:
- confidence;
- correctness;
- Brier score;
- expected calibration error (ECE);
- mean confidence;
- empirical accuracy.

Calibration can update the capability SelfModel and produces an `abstention_pressure` signal after enough samples.

MetaController now consumes this signal. A historically accurate capability that becomes badly overconfident can therefore receive increased verification or abstention pressure even when raw accuracy/reliability still looks high.

This prevents the system from treating "usually correct" and "well calibrated" as the same property.
