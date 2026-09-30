# R1.3-X Compositional Authority Governor V3 — conflict audit

## Discovery

The frozen R7.6 semantic organ is not a truth store. Its own artifact metadata contains 29 accepted semantic atoms, but two are explicitly marked `governor_correct=false`:

- P01 — `len(list(range(2,10,2)))` stored semantic answer `5`
- P04 — `7 // 2` stored semantic answer `2`

The correct executable results are:

- `len(list(range(2,10,2))) = 4`
- `7 // 2 = 3`

P01 is especially useful because R7.10 does **not** prove the whole requested expression. It compiles the inner `range(2,10,2)`, verifies the conclusion `[2,4,6,8]`, and therefore supplies a correct **intermediate proof**, not a final answer.

## New V3 authority policy

V3 introduces explicit proof scope:

- `FULL_SCOPE`: R7.10 proof covers the complete requested operation.
- `PARTIAL_SCOPE`: R7.10 proves a valid internal operation but the original request has an outer composition.
- `NONE`: no verified proof.

Authority rules:

1. `governor_correct=false` frozen atoms are retained for provenance but quarantined.
2. `FULL_SCOPE VERIFIED` outranks learned/frozen semantic memory.
3. `PARTIAL_SCOPE VERIFIED` is not returned as the final answer.
4. A partial proof may be completed only by a small safe executable composition whitelist.
5. Unsupported composition fails closed.
6. `governor_correct=true` R7.6 knowledge remains an advisory fallback when no stronger full proof exists.

## P01 resolution

Query:

`В Python чему равно len(list(range(2, 10, 2)))?`

R7.6:

- atom P01
- stored answer 5
- `governor_correct=false`
- quarantined

R7.10:

- compiler rule `py_range`
- independently verified intermediate conclusion `[2,4,6,8]`
- proof scope `PARTIAL_SCOPE`

V3 safe outer composition:

`len([2,4,6,8]) = 4`

Final authority:

`COMPOSED_VERIFIED_EXECUTION`

Final answer:

**4**

## P04 resolution

Query:

`В Python чему равно 7 // 2?`

R7.10:

- compiler rule `py_floordiv`
- independently recomputed result 3
- `FULL_SCOPE`

Final answer:

**3**

The R7.6 retrieval model does not reliably retrieve its own P04 atom for the exact P04 query; with the current vectorizer it points toward P01 at low similarity. The V3 semantic threshold therefore excludes that noisy retrieval and the full verified proof wins.

## Benchmarks

Initial AUTHORITY-CONFLICT-V3 diagnostic:

- 10/11 first open
- missing policy entry: R7.10 `binary_search` was independently VERIFIED but not yet classified as FULL_SCOPE

After inspecting its IR/ProofObject, `binary_search` was added to the full-scope rule set.

Fresh AUTHORITY-CONFLICT-V3-B2:

**12/12 = 100%**

No post-open tuning was applied to B2.

B2 covers:

- known-wrong frozen memory;
- full exact proof;
- partial exact proof;
- safe `len/sum/max` composition;
- direct `py_len`;
- arithmetic and GCD;
- binary-search proof;
- correct semantic-only fallback;
- unsupported outer composition fail-closed;
- completely unknown query abstention.

## Scientific conclusion

The conflict was not evidence that R7.10 was wrong. It exposed two separate issues:

1. R7.6 contains a small number of known-wrong advisory atoms and therefore cannot be treated as unquestioned truth.
2. R7.10 can produce a perfectly valid proof for a subexpression while failing to cover the whole user's requested expression.

The correct authority model is therefore **scope-aware**, not simply `verified > learned`.

A verified intermediate result has high authority over that intermediate claim only. It becomes final authority only after the rest of the requested computation is itself verified or safely executed.
