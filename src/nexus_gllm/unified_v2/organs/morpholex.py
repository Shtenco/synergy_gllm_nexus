from __future__ import annotations
import hashlib
import importlib.util
import sys
from pathlib import Path

from .donor_adapters import ArtifactUnavailable

EXPECTED_SOURCE_SHA256='b0557657ad21a3eab59ee4388a3003a3391895cfa537dc4d06cf674d8b188d40'
EXPECTED_MODEL_SHA256='13c66f9faab8b5459687fa1a65b9987f6cfd976ec3d2f969b3beb0ea651144cc'


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class MorpholexAdapter:
    organ_id='morpholex'
    source_version='R7.14'
    has_commit_authority=False

    def __init__(self, root: Path):
        root=Path(root)
        source=root/'source'/'morpholex_layer.py'
        model=root/'models_morpholex_distiller.joblib'
        if not source.is_file() or not model.is_file():
            raise ArtifactUnavailable(f'missing R7.14 MorphoLex artifact under {root}')
        self.source_sha256=_sha(source); self.model_sha256=_sha(model)
        if self.source_sha256 != EXPECTED_SOURCE_SHA256:
            raise ArtifactUnavailable(f'R7.14 source digest mismatch: {self.source_sha256}')
        if self.model_sha256 != EXPECTED_MODEL_SHA256:
            raise ArtifactUnavailable(f'R7.14 model digest mismatch: {self.model_sha256}')
        srcdir=str(root/'source')
        if srcdir not in sys.path: sys.path.insert(0,srcdir)
        name='nexus_v2_r714_morpholex_'+self.source_sha256[:12]
        spec=importlib.util.spec_from_file_location(name,source)
        if spec is None or spec.loader is None: raise ArtifactUnavailable('cannot load R7.14 MorphoLex')
        mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        self.module=mod

    def canonicalize(self,text: str, lang: str|None=None) -> str:
        return self.module.canonicalize(text,lang)

    def feature_vector(self,text: str, lang: str|None=None):
        return self.module.feature_vector(text,lang)

    def analyze(self,text: str, lang: str|None=None):
        return self.module.analyze(text,lang)
