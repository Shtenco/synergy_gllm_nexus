# Unified V3 MoE recovery freeze

- Source branch: `unified-v3-generalization-first`
- Source commit: `a18fa5a58fcd6d3e3bfb7bb7df0b092f13ff940c`
- Recovery branch: `nexus-r13x-recovery-2026-09-26`
- Recovery commit: `2abbe7add354deedd69503a0dfd36949f88e4698`
- Status: EXACT GIT BLOB RESTORATION
- Files restored: 26
- Modification policy: source blobs were referenced directly in the new Git tree; no source text was rewritten.
- Integrity note: the recorded SHA values are Git blob SHA-1 object IDs, not SHA-256 byte digests. Identical blob IDs between source and recovery are the byte-level Git integrity check.

| Path | Git blob SHA-1 | Bytes |
|---|---|---:|
| src/nexus_gllm/unified_v3/moe/__init__.py | b5e32726db671d8dd666c85b9568eeeb2ef7f524 | 25 |
| src/nexus_gllm/unified_v3/moe/capability_router.py | e360ab4d745bfcb2ca6c8763fec9b5715a43836e | 1254 |
| src/nexus_gllm/unified_v3/moe/contracts.py | 6f6a68ce17bd05e3fab40c23392daa874a708a4a | 2445 |
| src/nexus_gllm/unified_v3/moe/exact_artifacts.py | 8f37cd5ab19a6ff7f79802565ffcea2f12bc2c03 | 4768 |
| src/nexus_gllm/unified_v3/moe/exact_experts.py | b5c4823835490c758d7e0011f8c99a0bb1d90c67 | 10149 |
| src/nexus_gllm/unified_v3/moe/experts/__init__.py | e69de29bb2d1d6434b8b29ae775ad8c2e48c5391 | 0 |
| src/nexus_gllm/unified_v3/moe/experts/base.py | f4767c17ed47a7b08eaece73a80a1bda9edbe5cd | 808 |
| src/nexus_gllm/unified_v3/moe/experts/omega15r2_graph.py | e1e791f76af770682a6d4940013cc55bfcd04c7d | 531 |
| src/nexus_gllm/unified_v3/moe/experts/r710_proof.py | b4f4ebde1b0f37487f1aefdd4326a7cb3ffee9ac | 309 |
| src/nexus_gllm/unified_v3/moe/experts/r714_morpholex.py | ebc8e69c0c33b377f43fae88b9b902a511262a1a | 313 |
| src/nexus_gllm/unified_v3/moe/experts/r718_evidence.py | 5e37185b23b3b087d4f0038daceb811de6caba99 | 557 |
| src/nexus_gllm/unified_v3/moe/experts/r72_language.py | 92a6d375e2b632a807bcfd73b62016d5eb648c83 | 759 |
| src/nexus_gllm/unified_v3/moe/experts/r744_context.py | 778df2a1522450349c8daf2ce5bc6789d8ffb782 | 560 |
| src/nexus_gllm/unified_v3/moe/experts/r76_semantic_memory.py | 8f0566518ee8ce3ea17ffbb33b5a4ba664c453c9 | 318 |
| src/nexus_gllm/unified_v3/moe/experts/r78_formal.py | 681dca481152ea717ee190a63684085aa01b1fc3 | 309 |
| src/nexus_gllm/unified_v3/moe/experts/r7l_fast_induction.py | 2fa40f666797d61961dbcb042a054371c3d6d1d5 | 1417 |
| src/nexus_gllm/unified_v3/moe/experts/unified_r13.py | 5a5ffb945a70514bdf3c16506577c690ddbfe717 | 310 |
| src/nexus_gllm/unified_v3/moe/experts/v10_procedural.py | 11216e5eae91c16866b95b3331213b61ab535c66 | 313 |
| src/nexus_gllm/unified_v3/moe/experts/v30_shadow.py | f1a41567ad43b1b7e34cffbaf749dc1c1156904d | 309 |
| src/nexus_gllm/unified_v3/moe/experts/v3_hypothesis.py | d21616a3070364a34966860096d641d80422ee94 | 568 |
| src/nexus_gllm/unified_v3/moe/lineage.py | 5a3ed77f2bfde835cebee67abb5843871bb522df | 181 |
| src/nexus_gllm/unified_v3/moe/novelty_gate.py | ff5dc6d94271b6bf0f0998bfd5156ddb8a9118a6 | 850 |
| src/nexus_gllm/unified_v3/moe/proposal_fusion.py | 26ecf2d620f651930ee6a8d4136be38349bc40d6 | 864 |
| src/nexus_gllm/unified_v3/moe/registry.py | f7a2f17747cccb72d8f4d1c893ff048dfd8243fc | 987 |
| src/nexus_gllm/unified_v3/moe/registry_defaults.py | 26f00c4ec91cd2b40977d86e9b6a5d062b84ba9c | 1797 |
| src/nexus_gllm/unified_v3/moe/runtime.py | baaf37144d9ec91e2ec1270079742c3ebf5f8a6d | 2794 |
