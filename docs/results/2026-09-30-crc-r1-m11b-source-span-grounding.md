# CRC-R1 M11b — Source-Span-Grounded Language Proposals

**Date:** 2026-09-30

M11's first proposal contract required a syntactically valid span digest but could not prove that the digest referred to an actual substring of the current input. M11b closes that gap before any stronger neural parser is mounted.

Every proposed atom now carries:

`SourceSpanRef(start, end, sha256(text[start:end]))`.

The ingress gate verifies bounds and recomputes the digest against the exact current user text before raw text is quarantined. After admission, only typed Semantic IR plus span offsets/digests survive the language boundary.

A parser therefore cannot claim provenance from an invented substring by supplying an arbitrary 64-hex value.

The proposal still has **zero fact-commit authority**. M12 is the separate proposal→fact authority gate.
