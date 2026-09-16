from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class UnifiedV2Config:
    workspace_root: Path
    r78_module: Path
    r718_module: Path
    r72_root: Path
    r714_root: Path
    omega15r2_root: Path
    unified_v1_root: Path
    r7l_root: Path
    r717_root: Path
    omega16_root: Path

    @classmethod
    def local_default(cls, workspace_root: Path) -> 'UnifiedV2Config':
        workspace_root = Path(workspace_root)
        r718_root = Path('/mnt/data/nexus_ub1_src/r718/NEXUS_R718_BEST_OF_EVIDENCE_CREDIT_FREEZE_2026-08-23')
        return cls(
            workspace_root=workspace_root,
            r78_module=Path('/mnt/data/nexus_ub1_src/r79/NEXUS_R79_REAL_BLIND26_DUALNODE_2026-08-20/SOURCE/R78_NATIVE_AUTHORITY_FROZEN.py'),
            r718_module=r718_root/'source/runtime_r718.py',
            r72_root=Path('/mnt/data/nexus_ub1_src/r72full/NEXUS_R72_DISENTANGLED_NATURAL_UNSEEN_2026-08-18'),
            r714_root=r718_root/'base_r717/base_r716/base_r715/base_r714',
            omega15r2_root=Path('/mnt/data/nexus_ub1_src/omega15r2/omega15r2_bundle'),
            unified_v1_root=Path('/mnt/data/nexus_ub1_src/unified/nexus_unified_rebuild_v1'),
            r7l_root=workspace_root/'.donors/r7l/NEXUS_R7L_FAST_LEARNING_UNSEEN_OPERATOR_D192_2026-08-18',
            r717_root=r718_root/'base_r717',
            omega16_root=workspace_root/'.donors/omega16',
        )
