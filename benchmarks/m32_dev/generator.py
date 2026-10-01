from __future__ import annotations

from dataclasses import dataclass
import hashlib
import random

from nexus_gllm.unified_v3.cognitive.program_ast import ProgramKind, ProgramNode

FAMILIES=(
    'ru','en','mixed','history','documents','composition','counterfactual','conflict','adversarial'
)


@dataclass(frozen=True)
class DevCase:
    case_id:str
    family:str
    prompt:str
    history:tuple[str,...]
    documents:tuple[str,...]
    facts:tuple[tuple[str,str,str,bool,str],...]
    task:tuple[str,str,str]
    program:ProgramNode|None
    expected_truth:bool|None
    admission_expected:bool=True
    solvable:bool=True
    malformed_source:bool=False
    conflict:bool=False


def _id(seed,family,i):
    return hashlib.sha256(f'M32-DEV:{seed}:{family}:{i}'.encode()).hexdigest()[:24]


def _transitive(op='parent'):
    return ProgramNode(ProgramKind.ATOM,f'rule:transitive:{op}')


def _case(seed,family,i):
    cid=_id(seed,family,i)
    if family=='ru':
        return DevCase(cid,family,'Докажи связь Алисы и Кэрол.',(),('Алиса parent Боб. Боб parent Кэрол.',),(('parent','alice','bob',True,'document:0'),('parent','bob','carol',True,'document:0')),('parent','alice','carol'),_transitive(),True)
    if family=='en':
        return DevCase(cid,family,'Is Alice related to Carol by parent?',(),('Alice parent Bob. Bob parent Carol.',),(('parent','alice','bob',True,'document:0'),('parent','bob','carol',True,'document:0')),('parent','alice','carol'),_transitive(),True)
    if family=='mixed':
        return DevCase(cid,family,'Проверь parent Alice -> Carol.',('Alice parent Bob.',),('Боб parent Кэрол.',),(('parent','alice','bob',True,'history:0'),('parent','bob','carol',True,'document:0')),('parent','alice','carol'),_transitive(),True)
    if family=='history':
        return DevCase(cid,family,'Query parent alice carol.',('alice parent bob; bob parent carol',),(),(('parent','alice','bob',True,'history:0'),('parent','bob','carol',True,'history:0')),('parent','alice','carol'),_transitive(),True)
    if family=='documents':
        return DevCase(cid,family,'Query parent alice carol.',(),('alice parent bob; bob parent carol',),(('parent','alice','bob',True,'document:0'),('parent','bob','carol',True,'document:0')),('parent','alice','carol'),_transitive(),True)
    if family=='composition':
        node=ProgramNode(ProgramKind.ATOM,'rule:composition:parent:sibling:related')
        return DevCase(cid,family,'Is alice related to carol?',(),('alice parent bob; bob sibling carol',),(('parent','alice','bob',True,'document:0'),('sibling','bob','carol',True,'document:0')),('related','alice','carol'),node,True)
    if family=='counterfactual':
        child=_transitive('parent')
        node=ProgramNode(ProgramKind.COUNTERFACTUAL,children=(child,),params=(('kind','ADD_FACT'),('operator','parent'),('src','bob'),('dst','carol')))
        return DevCase(cid,family,'If Bob parent Carol, is Alice parent Carol?',('alice parent bob',),(),(('parent','alice','bob',True,'history:0'),),('parent','alice','carol'),node,True)
    if family=='conflict':
        return DevCase(cid,family,'Check disputed parent fact.',(),('alice parent bob',),(('parent','alice','bob',True,'document:0'),),('parent','alice','bob'),_transitive(),None,True,False,False,True)
    return DevCase(cid,family,'Adversarial malformed provenance.',(),('alice parent bob',),(('parent','alice','bob',True,'missing:9'),),('parent','alice','bob'),_transitive(),None,False,False,True,False)


def generate(seed=32001,n_per_family=20):
    cases=[_case(seed,family,i) for family in FAMILIES for i in range(n_per_family)]
    rng=random.Random(seed);rng.shuffle(cases)
    return tuple(cases)
