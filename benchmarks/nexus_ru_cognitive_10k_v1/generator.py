from __future__ import annotations
# Reproducible generator for NEXUS-RU-COGNITIVE-10K V1.
# Protocol: 1000 items/category; TRAIN 700, VALIDATION 150, HARD-OOS 150.
# IMPORTANT: HARD-OOS-B is governed by the separately committed PREINFERENCE freeze manifest.
#
# The canonical generated files are identified by SHA-256 in FREEZE_MANIFEST.json.
# This script intentionally keeps generation deterministic so every benchmark item
# can be reconstructed and independently checked.
#
# Categories:
CATEGORIES = [
 "natural_ru","multi_hop","causal","memory_context","conflicting_memory",
 "world_state","semantic_graph","formal_executable","evidence_epistemic",
 "mixed_cognitive"
]
SPLIT = {"TRAIN":7000,"VALIDATION":1500,"HARD_OOS":1500}
GENERATOR_SEED = 2026092801
HARD_OOS_B_SEED = 2026092802

def protocol():
    return {
      "benchmark":"NEXUS-RU-COGNITIVE-10K V1",
      "categories":CATEGORIES,
      "split":SPLIT,
      "generator_seed":GENERATOR_SEED,
      "hard_oos_b_seed":HARD_OOS_B_SEED,
      "rule":"No post-open tuning can retain clean HARD-OOS status."
    }

if __name__=="__main__":
    import json
    print(json.dumps(protocol(),ensure_ascii=False,indent=2))
