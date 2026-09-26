# R1.3-X Exact Cognitive Russian Runtime V2 — exact artifact provenance

Date: 2026-09-26

## Mounted exact organs

### R7.6 Semantic Real-Teacher Knowledge Organ

- organ file: `r76_semantic_knowledge_organ.pkl`
- organ bytes: 4,083,213
- organ SHA-256: `bf0c95f208e398f866b0108709c05fb7e4ef4dee5b48c3b3c4d4f5c87bc9130f`
- release ZIP SHA-256: `1ecb9c54f44b329d9a110abee612f2d2a7de80c07916591d7107a50e17ad5b3a`
- loaded structure: TF-IDF vectorizer + 3 frozen classifiers + 29 accepted semantic atoms
- freeze stage: before Blind-23 creation
- internal `SHA256SUMS.txt`: PASS
- runtime sanity check: formal atom L01 returned `Некоторые C являются B`

### R7.8 Top-2 Cognitive Arbitration

- release ZIP SHA-256: `61a7038f68375c586bee4fdb636e5a0fe9c6ff036da55d35b5fb2ab2bee5f195`
- frozen native authority: `02_NATIVE_AUTHORITY_FROZEN.py`
- freeze stage: before Blind-25 creation
- internal `SHA256SUMS.txt`: PASS
- runtime sanity check: `23 × 7` -> option B / `math_mul`

### R7.10 Proof-First Generalization

- release ZIP SHA-256: `7d700397e809dc68dfe3eada90883946d008a3d17fd7dfc0993ded62b6821544`
- runtime source: `FREEZE/source/runtime_v2.py`
- compiler / solver / independent verifier source hashes are frozen in `00_R710_FREEZE_MANIFEST.json`
- fresh-unpack `SHA256SUMS.txt`: PASS for all files
- note: importing Python rewrites `.pyc`; source/manifests/models remain unchanged
- runtime sanity check: `23 × 7` -> VERIFIED ProofObject, conclusion 161
- V2 extension: free-form `prove(question)` API added without altering frozen source

### R7.14 Multilingual MorphoLex

- release ZIP SHA-256: `ca8746639187950bd6051c812b9118cca5f8814c00b5fe46497aab194f3f3127`
- frozen source: `source/morpholex_engine.py`
- self-test in manifest: 150/150 over ten listed languages
- internal `SHA256SUMS.txt`: PASS
- runtime sanity check: Russian detected as `ru`; canonicalization executed
- integration role: canonicalization / linguistic provenance only; no direct answer override

## V2 runtime roles

- R7.14: pre-analysis / provenance and canonicalization
- R7.6: semantic retrieval only inside a high-similarity frozen neighborhood
- R7.10: proof-first exact/formal verification with ProofObject
- R7.8 + R7.10: MCQ exact-consensus; answer accepted only on agreement
- R1.3-X governor / Russian runtime: session memory, world state, causal graph, renderer and abstention

## Artifact integrity

The four external organs were copied from the user's Google Drive and mounted locally. Their release bytes were not modified.

R7.6 manifest explicitly binds the semantic organ to SHA-256 `bf0c95f...` and states that it contains 29 accepted semantic atoms rather than answer-position labels.

## Known integration defect after HARD-DIALOGUE-6

`R710_NESTED_LEN_RANGE_AUTHORITY`

Query:
`В Python чему равно len(list(range(2, 10, 2)))?`

Observed V2 behavior:
R7.10 compiles the inner `range` operation, independently verifies `[2,4,6,8]`, and V2 accepts that verified result.

Correct whole-expression answer:
`5`.

R7.6 frozen semantic atom P01 contains exactly this whole-question answer. This is an arbitration / compositional-scope defect, not an artifact-integrity failure.

No post-open fix was applied before preserving HARD-DIALOGUE-6.
