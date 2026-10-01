from __future__ import annotations

import json
import re
from pathlib import Path

_HEX64=re.compile(r'[0-9a-f]{64}')


def build_manifest(*,generator_sha256:str,seed:int,case_count:int,implementation_commit:str)->dict:
    if not _HEX64.fullmatch(generator_sha256):
        raise ValueError('generator_sha256 must be 64 lowercase hex chars')
    if not implementation_commit:
        raise ValueError('implementation_commit required')
    if case_count<=0:
        raise ValueError('case_count must be positive')
    return {
        'schema':'nexus.m32.meta.freeze.v1',
        'benchmark':'M32-META',
        'generator_sha256':generator_sha256,
        'seed':int(seed),
        'case_count':int(case_count),
        'implementation_commit':implementation_commit,
        'sealed_before_first_integrated_evaluation':True,
        'test_open_count':0,
        'ftx1_status':'CONSUMED_FTX1',
        'ftx1_used_as_clean_oos':False,
        'ftx2_authored':False,
    }


def write_manifest(path:Path|str,manifest:dict)->dict:
    path=Path(path)
    if path.exists():
        existing=json.loads(path.read_text(encoding='utf-8'))
        if existing!=manifest:
            raise RuntimeError('sealed M32-META manifest mismatch; refusing overwrite')
        return existing
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    return manifest
