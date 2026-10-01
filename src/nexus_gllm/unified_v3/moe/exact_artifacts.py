from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import hashlib

class ArtifactStatus(str,Enum):
    EXACT_RUNNABLE='EXACT_RUNNABLE'
    EXACT_DEPLOYED_RUNTIME='EXACT_DEPLOYED_RUNTIME'
    VERIFIED_OPERATIONAL_RUNTIME='VERIFIED_OPERATIONAL_RUNTIME'
    EXACT_SOURCE_INCOMPLETE_RUNTIME='EXACT_SOURCE_INCOMPLETE_RUNTIME'
    CHECKPOINT_NOT_MOUNTED='CHECKPOINT_NOT_MOUNTED'
    EXACT_SOURCE_INTEGRATION_CHECKPOINT_NOT_MOUNTED='EXACT_SOURCE_INTEGRATION_CHECKPOINT_NOT_MOUNTED'
    HISTORICAL_RELEASE_NOT_MOUNTED='HISTORICAL_RELEASE_NOT_MOUNTED'
    HASH_MISMATCH='HASH_MISMATCH'

@dataclass(frozen=True)
class ArtifactRecord:
    expert_id:str; status:ArtifactStatus; paths:tuple[str,...]=(); expected_sha256:tuple[str,...]=(); notes:str=''

class ArtifactCatalog:
    def __init__(self,root:Path,records:dict[str,ArtifactRecord]):
        self.root=Path(root); self.records=records

    @classmethod
    def default(cls,root:Path):
        rec={
          'r7l':ArtifactRecord('r7l',ArtifactStatus.EXACT_RUNNABLE,('r7_seed711.pt','r7_seed712.pt','r7_seed713.pt'),('c447d872a0e9299aa3bbf0e82ad884c9b9ba4fcdf7514960c91b33d2ee50aff3','a6b949fde908aa801b5c69e702e1710d32e84e1c2627d0fadd9aab71e5cb7c18','b01679fa280a375966fae3221b98abe7528d5188675bae702f1f9c122b33116f'),'R7-L exact three-seed collective 711/712/713'),
          'r72':ArtifactRecord('r72',ArtifactStatus.EXACT_RUNNABLE,('r72_language_binder.pt','r7l_core_seed712.pt'),('b6ef32052ddd3144dde76a84a81c41b5d7caf7761d5658eed18ebee21bef5eb7','a6b949fde908aa801b5c69e702e1710d32e84e1c2627d0fadd9aab71e5cb7c18'),'exact binder + frozen R7-L core'),
          'r76':ArtifactRecord('r76',ArtifactStatus.EXACT_RUNNABLE,('r76_semantic_knowledge_organ.pkl.bin',),('bf0c95f208e398f866b0108709c05fb7e4ef4dee5b48c3b3c4d4f5c87bc9130f',),'exact semantic knowledge organ'),
          'r78':ArtifactRecord('r78',ArtifactStatus.EXACT_RUNNABLE,('NEXUS_R78_TOP2_ARBITRATION_REAL_BLIND25_2026-08-20.zip',),('61a7038f68375c586bee4fdb636e5a0fe9c6ff036da55d35b5fb2ab2bee5f195',),'exact frozen archive; native authority source runnable'),
          'r710':ArtifactRecord('r710',ArtifactStatus.EXACT_RUNNABLE,('NEXUS_R710_PROOF_FIRST_FREEZE_2026-08-21.zip',),('b397e355b67ed91fb6d675a8bae502b759a923cfedf33a9ad172c070c09e29c7',),'exact proof-first freeze'),
          'r714':ArtifactRecord('r714',ArtifactStatus.EXACT_RUNNABLE,('NEXUS_R714_MULTILINGUAL_MORPHOLEX_FREEZE_2026-08-23.zip',),('ca8746639187950bd6051c812b9118cca5f8814c00b5fe46497aab194f3f3127',),'exact MorphoLex freeze'),
          'r718':ArtifactRecord('r718',ArtifactStatus.EXACT_RUNNABLE,('NEXUS_R718_BEST_OF_EVIDENCE_CREDIT_FREEZE_2026-08-23.zip',),('12a5c190d2f6d3a88a938b2b064ff0e7341df6ec9c169a7462c9ab4ee904021d',),'exact evidence-credit freeze; original selftests run'),
          'r7443':ArtifactRecord('r7443',ArtifactStatus.EXACT_DEPLOYED_RUNTIME,('artifacts/recovered/r7443_deployed/context-binder-r7443.js',),('d248bb75c45694bbde6914615243080b711d2efea80b22c2652e692cc8307703',),'byte-identical deployed R7.44.3 MOBILE PORT recovered from SINERGIYA-FINANS-v8.0.1-NEXUS-R7443-MAX.apk; original Python lineage still lacks R7.38 dependencies'),
          'omega15r2':ArtifactRecord('omega15r2',ArtifactStatus.EXACT_RUNNABLE,('omega15r2_bundle/omega15r2_bundle/artifacts/omega15r2_v1/omega15r2_joint_binder_frozen.joblib','omega15r2_bundle/omega15r2_bundle/artifacts/base_semantic/omega14r_semantic_operator.joblib'),('0bf09576104a1ca867d103b7fd2bb536510c0c2e044e1b549126ef44c47f12d6','aae4b5ddcb8b1d4375e1248d258b9f0a89fbb190621c497b9352b6bd2a9894da'),'exact Omega-1.5R2 frozen binder + exact Omega-1.4R semantic base; original frozen bundle tests 12/12'),
          'v10':ArtifactRecord('v10',ArtifactStatus.EXACT_RUNNABLE,('unified_ru_v1/NEXUS_UNIFIED_RU_V1/assets/arc_v10/checkpoints/v11_infograph_policy_600000.pt','unified_ru_v1/NEXUS_UNIFIED_RU_V1/assets/arc_v10/arc_solver_v11.py','unified_ru_v1/NEXUS_UNIFIED_RU_V1/assets/arc_v10/v11_model.py'),('50304acc6b99f5129b5d66a405fd96c86deb7d64dbb4160d4396e6d08b58ef5a','fb6e0f0bbcfa6e3820bd473741f85cb78c320b9afbeb58ff851723e9a8a1c772','d39eabf3246c6e7cc6cd41cb516b4f278fde2f4ab6f6355aff1e05d664a06883'),'exact V10 600K checkpoint + frozen solver/model recovered from original Unified RU bundle'),
          'unified_r13':ArtifactRecord('unified_r13',ArtifactStatus.HISTORICAL_RELEASE_NOT_MOUNTED,(),(), 'historical sealed result exists; byte-identical original R1.3 release tree remains distinct from later R1.3-X'),
          'r13x_v3':ArtifactRecord('r13x_v3',ArtifactStatus.VERIFIED_OPERATIONAL_RUNTIME,(),(), 'verified operational authority runtime: R1.3-X V2 exact cognitive runtime + V3 compositional authority governor; provenance anchored to GitHub PR #6 head 4735ca4f36d441f4fa2de6af4c704d5140a6c586 and PR #7 head 105a692d64a42d6c772de69dcaeb16ac27833b01; not relabelled as byte-identical historical R1.3'),
        }
        return cls(root,rec)

    def _resolve(self,rel:str)->Path:
        external=self.root/rel
        if external.is_file(): return external
        return Path(rel)

    def verify(self,expert_id:str)->ArtifactRecord:
        r=self.records[expert_id]
        if not r.paths:return r
        for rel,exp in zip(r.paths,r.expected_sha256):
            p=self._resolve(rel)
            if not p.is_file():
                return ArtifactRecord(r.expert_id,ArtifactStatus.CHECKPOINT_NOT_MOUNTED,r.paths,r.expected_sha256,r.notes)
            if hashlib.sha256(p.read_bytes()).hexdigest()!=exp:
                return ArtifactRecord(r.expert_id,ArtifactStatus.HASH_MISMATCH,r.paths,r.expected_sha256,r.notes)
        return r
