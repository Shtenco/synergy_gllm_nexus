from __future__ import annotations

import random

from .schema import FTXCase, FTXGold

TRACKS = (
    'semantic_rule_induction',
    'surface_far_transfer',
    'role_voice_coreference',
    'task_schema_induction',
    'compositional_reasoning',
    'cross_language_transfer',
    'long_horizon_transfer',
    'evidence_counterfactual',
)

_DEV_NAMES = ('Анна','Борис','Вера','Глеб','Ирина','Лев')
_SH_NAMES = ('Марта','Павел','Роман','София','Тимур','Юлия')


def _make(split: str, seed: int, family: str, n: int = 16):
    rng = random.Random(seed)
    names = _DEV_NAMES if split == 'DEV' else _SH_NAMES
    ns = f'{split.lower()}_{family}_ontology'
    out: dict[str, list[tuple[FTXCase, FTXGold]]] = {t: [] for t in TRACKS}
    for ti, track in enumerate(TRACKS):
        for i in range(n):
            a = names[(i + ti) % len(names)]
            b = names[(i + ti + 1) % len(names)]
            token = f'{family.upper()}{ti}{i}'
            relation = ('согласует' if family == 'A' else 'координирует')
            if track == 'semantic_rule_induction':
                prompt = f'Правило {token}: если {a} {relation} {b}, то связь {token} направлена от первого участника ко второму. {a} {relation} {b}. Кто источник связи?'
                ans = a
            elif track == 'surface_far_transfer':
                prompt = f'{a} передал пакет {b}. Переформулируй смысл: кто был отправителем?'
                ans = a
            elif track == 'role_voice_coreference':
                prompt = f'Документ был передан {b} человеком по имени {a}. Он затем подтвердил отправку. Кто отправитель?'
                ans = a
            elif track == 'task_schema_induction':
                prompt = f'Пример: [Коля, Миша] -> Миша|Коля. Выполни ту же операцию для [{a}, {b}].'
                ans = f'{b}|{a}'
            elif track == 'compositional_reasoning':
                c = names[(i + ti + 2) % len(names)]
                prompt = f'Если X ведёт к Y, а Y ведёт к Z, то X косвенно ведёт к Z. {a} ведёт к {b}; {b} ведёт к {c}. К кому косвенно ведёт {a}?'
                ans = c
            elif track == 'cross_language_transfer':
                prompt = f'Fact: {a} owns token {token}. Вопрос по-русски: кто владеет токеном {token}?'
                ans = a
            elif track == 'long_horizon_transfer':
                history = tuple(f'Шаг {j}: служебная запись {j}.' for j in range(12)) + (f'Исправление: актуальным владельцем {token} является {a}.',)
                prompt = f'Кто сейчас владеет {token}?'
                case = FTXCase(f'{split.lower()}-{ti}-{i}', track, prompt, history=history, pair_group=(f'{split}-pair-{ti}-{i//2}' if i % 2 < 2 else None))
                gold = FTXGold(answer=a, semantic_key=f'{track}:{i//2}', audit=(('ontology_ns',ns),('family',family)))
                out[track].append((case,gold))
                continue
            else:
                prompt = f'Источник d1 утверждает: {a} активировал {token}. Источник d2 повторяет d1. Контрфакт: если {a} не активировал {token}, можно ли считать активацию доказанной? Ответь UNRESOLVED.'
                ans = 'UNRESOLVED'
            pair = f'{split}-pair-{ti}-{i//2}' if i % 4 in (0,1) else None
            case = FTXCase(f'{split.lower()}-{ti}-{i}', track, prompt, pair_group=pair)
            gold = FTXGold(answer=ans, semantic_key=f'{track}:{i//2}' if pair else f'{track}:{i}', audit=(('ontology_ns',ns),('family',family)))
            out[track].append((case,gold))
    return out


def generate_dev(seed: int):
    return _make('DEV', seed, 'A')


def generate_shadow(seed: int):
    return _make('SHADOW', seed, 'B')
