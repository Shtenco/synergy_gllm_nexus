# NEXUS-FTX1 Freeze Report — 2026-09-17

Status: **FROZEN / VERIFIED**

Base development line: `nexus-ftx1-freeze-v1`, originating from the approved FTX1 preregistration. Unified v2 RC1 was not modified during benchmark construction.

## Corpus

The canonical Family-C BLIND suite contains exactly **2,400 cases**, with **300 cases in each of eight tracks**. Runtime and scorer-only gold are serialized separately. Runtime records contain only `case_id`, `prompt`, `history`, and `documents`.

The long-horizon track contains 30/50/75/100-turn episodes, with each horizon represented by at least 60 cases. All blind cases participate in paired semantic-equivalence groups, exceeding the preregistered >=40% requirement.

## Structural verification

`validate_bundle()` returned **0 errors**. Runtime serialization was independently scanned for forbidden gold-adjacent keys including `path_edges`, pair/group metadata, semantic keys, ontology IDs, renderer IDs, proof paths and answer indices; none were present.

## Shortcut red-team

Candidate Family C passed every preregistered veto:

- regex/template baseline: 0.0000
- nearest DEV-template baseline: 0.0000
- exact DEV-skeleton matcher: 0.0000
- answer-frequency baseline: 0.0000
- metadata-only baseline: 0.0000
- normalized skeleton overlap DEV -> BLIND: 0.0000
- normalized skeleton overlap SHADOW -> BLIND: 0.0000

These are anti-shortcut diagnostics, not v3 intelligence scores.

## Verification

The focused FTX1 test suite completed with **11 passed, 0 failed**. Python `compileall` completed without errors for public FTX1 modules and the sealed generator. The ZIP integrity check passed, all embedded corpus/source hashes were independently recomputed, and both runtime and gold contain exactly 2,400 records.

## Canonical hashes

- archive SHA-256: `cd01b1c37cc35ddf970aaffff2a6ae25723e4db1c0421fdccf5c423a35efae56`
- runtime SHA-256: `f19fe25cc839a78966b0b07ce8733f162462d35ab67c8bd73e547ff59a13bebf`
- scorer-only gold SHA-256: `d2d1f023f03e7b0e960f146feed95631f79351b8e0895d0923e1df9061acf11b`
- sealed Family-C generator SHA-256: `58b3fa6be603ee2f469be2d035b81afdc249b7fda398194df5651c80c2b172b9`
- red-team report SHA-256: `284654b16b2dc56843f3cdf3a30007995fbdc5767c3bcb2a702f5724c1cc43a7`

The canonical sealed ZIP is kept outside GitHub development source. GitHub receives only public code, tests, hashes and this report.

## Gate

After the public freeze commit is written and read back successfully, branch `unified-v3-generalization-first` may be created from that exact commit. No BLIND content may be inspected during v3 development. The one-shot evaluation is valid only against the frozen preblind v3 checkpoint.
