# CRC-R1 M1.2 — P1 artifact-integrity correction

Self-audit found that hard-coded SHA values previously placed in the loader were not backed by an independently generated repository integrity manifest. Keeping them would risk permanent fallback or, worse, confusing a guessed hash with verified provenance.

M1.2 removes those constants as the default authority. The loader now requires either:
1. an explicit expected SHA map supplied by a verified caller, or
2. a committed `integrity.sha256.json` beside the P1 payload.

Without one, learned P1 loading fails closed with `integrity_manifest_missing`.

A generator is added so CI can compute hashes from the exact checked-out commit. The intended next step is:
- GitHub CI checks out the PR commit;
- generates the integrity manifest;
- runs the P1/B2 one-shot;
- uploads integrity + result as a workflow artifact;
- those exact hashes/results are then committed back as frozen evidence.

This corrects the earlier overstatement that P1 was already production-loadable by default.
