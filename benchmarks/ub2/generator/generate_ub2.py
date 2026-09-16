from __future__ import annotations
import random
from benchmarks.ub2.schema import UB2Case, SemanticContract
from benchmarks.ub2.generator.evidence_corpus import build_corpus

TRACK_COUNTS = {
    'russian_free_dialogue': 300,
    'long_memory': 300,
    'russian_coreference': 300,
    'complex_causality': 300,
    'research_evidence': 300,
    'graph_ood_reasoning': 320,
    'unseen_task_induction': 320,
}

NAMES = ['Анна','Борис','Вера','Глеб','Дарья','Егор','Жанна','Илья','Кира','Лев','Мира','Никита']
ITEMS = ['ключ','папка','отчёт','датчик','договор','модуль','архив','граф','проект','протокол']
PREFIX = {
    'russian_free_dialogue':'rfd', 'long_memory':'lmem', 'russian_coreference':'rcf',
    'complex_causality':'cca', 'research_evidence':'res', 'graph_ood_reasoning':'god',
    'unseen_task_induction':'uti',
}

def _cid(track: str, i: int) -> str:
    return f'{PREFIX[track]}-{i:04d}'

def _dialogue(rng, i):
    name = rng.choice(NAMES); item = rng.choice(ITEMS)
    corrected = i % 5 == 0
    history = (f'Пользователь: {name} отвечает за {item}.',)
    if corrected:
        history += (f'Пользователь: Исправление: за {item} теперь отвечает {NAMES[(NAMES.index(name)+1)%len(NAMES)]}.',)
        name = NAMES[(NAMES.index(name)+1)%len(NAMES)]
    return UB2Case(_cid('russian_free_dialogue', i),'russian_free_dialogue',f'Кто сейчас отвечает за {item}?',history,
                   SemanticContract(required_claims=(f'{name} отвечает за {item}',)),
                   {'correction': corrected, 'deterministic': True})

def _memory(rng, i):
    turn_count = (30,50,75,100)[i % 4]
    owner = rng.choice(NAMES); item = rng.choice(ITEMS)
    history=[]
    for t in range(turn_count-2):
        history.append(f'Ход {t+1}: обсуждение темы {rng.choice(ITEMS)} без изменения факта.')
    history.append(f'Факт: {owner} хранит {item}.')
    if i % 3 == 0:
        new_owner=NAMES[(NAMES.index(owner)+2)%len(NAMES)]
        history.append(f'Исправление: теперь {new_owner} хранит {item}.')
        owner=new_owner
    else:
        history.append('Продолжаем разговор без изменения владельца.')
    return UB2Case(_cid('long_memory', i),'long_memory',f'Кто хранит {item}?',tuple(history),
                   SemanticContract(required_claims=(f'{owner} хранит {item}',)),
                   {'turn_count':turn_count,'deterministic':True})

def _coref(rng, i):
    a,b=rng.sample(NAMES,2); item=rng.choice(ITEMS); ambiguous=i%6==0
    if ambiguous:
        hist=(f'{a} встретил {b}.',f'Он взял {item}.'); contract=SemanticContract(clarification_required=True); prompt='Кто именно взял предмет?'; deterministic=False
    else:
        hist=(f'{a} передал {item} {b}.',f'После этого {b} положил его в сейф.'); contract=SemanticContract(required_claims=(f'{b} положил {item} в сейф',)); prompt='Кто положил предмет в сейф?'; deterministic=True
    return UB2Case(_cid('russian_coreference', i),'russian_coreference',prompt,hist,contract,{'deterministic':deterministic,'ambiguous':ambiguous})

def _causal(rng, i):
    depth=2+(i%4); causes=[f'C{i}_{j}' for j in range(depth+1)]; blocked=i%7==0; edges=[(causes[j],causes[j+1]) for j in range(depth)]
    claim=f'{causes[-1]} не наступает из-за блокиратора B{i}' if blocked else f'{causes[0]} приводит к {causes[-1]}'
    prompt='; '.join(f'{a} вызывает {b}' for a,b in edges)
    if blocked: prompt += f'; B{i} блокирует {causes[-1]}'
    return UB2Case(_cid('complex_causality', i),'complex_causality',prompt,(),SemanticContract(required_claims=(claim,)),{'edges':edges,'blocked':blocked,'deterministic':True})

def _research(rng, i):
    corpus=build_corpus(); ids=[f'doc-{(i*3+j)%120:03d}' for j in range(4)]; fact=i%20
    positive=[d for d in corpus if d.doc_id in ids and 'подтверждает' in d.text]
    contradictory=[d for d in corpus if d.doc_id in ids and 'оспаривает' in d.text]
    uncertain=bool(contradictory) and bool(positive)
    required=(f'F{fact} подтверждено',) if not uncertain else ()
    contract=SemanticContract(required_claims=required,required_citations=tuple(d.doc_id for d in positive[:2]),expected_uncertainty=uncertain)
    return UB2Case(_cid('research_evidence', i),'research_evidence',f'Оцени утверждение F{fact} по локальным источникам.',(),contract,{'evidence_doc_ids':ids,'deterministic':True,'uncertain':uncertain})

def _graph(rng, i):
    depth=1+(i%8); rel=('before','causes','is_a','contains')[i%4]; nodes=[f'N{i}_{j}' for j in range(depth+1)]; edges=[(nodes[j],rel,nodes[j+1]) for j in range(depth)]
    return UB2Case(_cid('graph_ood_reasoning', i),'graph_ood_reasoning',f'Определи связь {nodes[0]} -> {nodes[-1]}.',(),SemanticContract(required_claims=(f'{nodes[0]} {rel}*{depth} {nodes[-1]}',)),{'declared_depth':depth,'path_edges':edges,'relation':rel,'deterministic':True})

def _unseen(rng, i):
    op=f'оператор-{chr(1072+(i%20))}{(i*7)%97}'; x=f'объект-{(i*5)%113}'; y=f'объект-{(i*11+3)%127}'; reverse=i%2==0; negative=i%9==0
    rule=f'Если {y} указан после {x}, применяй {op} от {x} к {y}.' if reverse else f'Если встречаются {x} и {y}, применяй {op} к паре в порядке упоминания.'
    target=f'NOTA:{op}' if negative else f'{op}({x},{y})'
    return UB2Case(_cid('unseen_task_induction', i),'unseen_task_induction',rule,(),SemanticContract(required_claims=(target,)),{'reverse_order':reverse,'nota':negative,'deterministic':True})

def generate_all(seed: int = 260916):
    rng=random.Random(seed)
    builders={'russian_free_dialogue':_dialogue,'long_memory':_memory,'russian_coreference':_coref,'complex_causality':_causal,'research_evidence':_research,'graph_ood_reasoning':_graph,'unseen_task_induction':_unseen}
    return {track:[builders[track](rng,i) for i in range(n)] for track,n in TRACK_COUNTS.items()}
