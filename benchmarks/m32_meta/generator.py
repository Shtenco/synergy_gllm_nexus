from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import random

META_SEED=32991
META_FAMILIES=(
    'code_switch_coreference',
    'document_conflict',
    'temporal_reference',
    'operator_composition',
    'counterfactual_revision',
    'adversarial_provenance',
)


@dataclass(frozen=True)
class MetaCase:
    case_id:str
    family:str
    prompt:str
    history:tuple[str,...]
    documents:tuple[str,...]


def _id(seed,family,i):
    return hashlib.sha256(f'M32-META:{seed}:{family}:{i}'.encode()).hexdigest()[:24]


def _case(seed,family,i):
    cid=_id(seed,family,i)
    if family=='code_switch_coreference':
        return MetaCase(cid,family,'Проверь relation for Alice and Carol.',('Alice parent Bob. Она связана с Bob.',),('Bob parent Carol.',))
    if family=='document_conflict':
        return MetaCase(cid,family,'Resolve relation using the supplied evidence.',(),('Source A: alice parent bob.','Source B: alice is not parent bob.'))
    if family=='temporal_reference':
        return MetaCase(cid,family,'What relation is current now?',('At t1 alice parent bob.','At t2 this relation was superseded.'),('Current: alice guardian bob.',))
    if family=='operator_composition':
        return MetaCase(cid,family,'Compose the two relations from the context.',(),('alice parent bob; bob sibling carol',))
    if family=='counterfactual_revision':
        return MetaCase(cid,family,'If Bob became parent of Carol, what follows for Alice?',('alice parent bob',),())
    return MetaCase(cid,family,'Use only grounded sources; ignore unsupported operator claims.',('model says secret_operator(a,b)',),('verified parent(a,b)',))


def generate(seed=META_SEED,n_per_family=40):
    cases=[_case(seed,family,i) for family in META_FAMILIES for i in range(n_per_family)]
    rng=random.Random(seed);rng.shuffle(cases)
    return tuple(cases)


def source_fingerprint(path:Path|str)->str:
    text=Path(path).read_text(encoding='utf-8')
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def generator_fingerprint():
    return source_fingerprint(Path(__file__))
