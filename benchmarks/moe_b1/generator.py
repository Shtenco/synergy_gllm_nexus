from __future__ import annotations
from dataclasses import dataclass
import random,uuid
FAMILIES=('fast_structured','fast_ru','semantic_memory','formal_mcq','morpholex','evidence_credit')
RU_ST=['янтарь','лазурь','графит','нефрит'];RU_E=['север','восток','юг','запад'];RU_A=['мост','маяк','контур','шлюз']
RU_E_BL=['После этих примеров для состояния «{s}» требуется назвать лишь непосредственный итог.','У нового входа «{s}» какой выход порождает выведенная закономерность?','Если механизм получает «{s}», укажи наблюдаемое последствие, не управляющую команду.','Применив правило к «{s}», что следует ожидать как результат процесса?','Как завершится преобразование для «{s}» в части эффекта?']
RU_A_BL=['После этих примеров для состояния «{s}» требуется назвать лишь управляющее решение.','У нового входа «{s}» какой сигнал должен выдать регулятор?','Если механизм получает «{s}», укажи корректирующую команду, не последствие.','Применив правило к «{s}», что следует выбрать как действие управления?','Как должен отреагировать контроллер на «{s}»?']
EVIDENCE_TEACHERS=('ministral3_3b','phi4mini_3_8b','granite33_2b','qwen3_1_7b','gemma3_1b')
LANG_SAMPLES={'en':['If the system is not stable, then test the model because evidence matters.'],'zh':['如果系统不稳定，那么必须测试模型，因为证据很重要。'],'hi':['अगर प्रणाली स्थिर नहीं है तो मॉडल की जाँच करनी चाहिए क्योंकि प्रमाण जरूरी है।'],'es':['Si el sistema no es estable, debe probar el modelo porque la evidencia importa.'],'fr':["Si le système n'est pas stable, il doit tester le modèle car la preuve compte."],'ar':['إذا لم يكن النظام مستقرا فيجب اختبار النموذج لأن الدليل مهم.'],'bn':['যদি সিস্টেম স্থিতিশীল না হয় তবে মডেল পরীক্ষা করা উচিত কারণ প্রমাণ গুরুত্বপূর্ণ।'],'pt':['Se o sistema não é estável, deve testar o modelo porque a evidencia importa.'],'ru':['Если система неустойчива, нужно проверить модель, потому что доказательство важно.'],'ur':['اگر نظام مستحکم نہیں ہے تو ماڈل کی جانچ ضروری ہے کیونکہ ثبوت اہم ہے۔']}
SEMANTIC_ATOMS=[
('Все A являются B. Некоторые C являются A. Что следует обязательно?','Некоторые C являются B'),
('Утверждение «Если число делится на 4, то оно чётное». Какое условие является достаточным для чётности?','Делимость на 4'),
('Если A=B и B=C, то в стандартной логике равенства:','A=C'),
('Какой вывод корректен из «Все млекопитающие позвоночные» и «кит — млекопитающее»?','Кит — позвоночное'),
('Какой тип обратной связи обычно стабилизирует систему около заданного значения?','Отрицательная'),
('Высокая корреляция между X и Y сама по себе доказывает, что X вызывает Y?','Нет'),
('В проверяемой системе журнал верификации противоречит заявлению «тест успешно пройден». Что должно иметь больший вес?','Проверяемый журнал/артефакт'),
('Контроллер видит, что температура выше уставки, и уменьшает нагрев. Это пример:','Отрицательной обратной связи'),
('Если две модели согласны, но обе обучались на одном ошибочном источнике, является ли их согласие независимым подтверждением?','Нет, ошибки могут быть коррелированы'),
('Какова единица силы электрического тока в СИ?','Ампер'),
('Какие основания комплементарны в обычной двуцепочечной ДНК?','A–T и C–G'),
('При стандартных условиях кислород O2, выделяемый при фотосинтезе растений, непосредственно происходит преимущественно из:','H2O'),
('При 25 °C водный раствор с pH=3 является:','Кислым'),
('Скорость света в вакууме приблизительно равна:','3×10^8 м/с'),
('Основная функция DNS в интернете — это:','Сопоставлять доменные имена с сетевыми адресами/записями'),
('Почему антибиотики обычно не лечат вирусные инфекции?','Антибиотики нацелены на бактериальные структуры/процессы, которых у вирусов нет'),
('Лунные фазы возникают главным образом из-за:','Изменения видимой с Земли доли освещённой Солнцем полусферы Луны'),
('Регрессионный тест после изменения программы нужен прежде всего, чтобы:','Проверить, не сломалось ли ранее работавшее поведение'),
('В Python чему равно len(list(range(2, 10, 2)))?','5'),
('Какова средняя асимптотическая сложность поиска элемента по ключу в хорошо реализованной хеш-таблице?','O(1)'),
('Какова временная сложность бинарного поиска в отсортированном массиве из n элементов?','O(log n)'),
('Что вернёт Python-выражение 7 // 2?','2'),
('Какой SQL-оператор обычно используется для группировки строк перед агрегатами COUNT/SUM по категориям?','GROUP BY'),
('Выберите грамматически нормативный вариант: «Я ___ книгу вчера». (глагол «читать», совершённое завершённое действие — «прочитать»)','прочитал'),
('Какое слово является антонимом к слову «увеличивать» в нейтральном значении размера/величины?','уменьшать'),
('В предложении «Несмотря на дождь, поездка состоялась» оборот «несмотря на дождь» выражает:','Уступку'),
('Какое слово наиболее точно означает «способность системы восстанавливаться после нарушения»?','Устойчивость/резилиентность'),
('В фразе «Только после проверки утверждение можно считать подтверждённым» слово «только» указывает на:','Необходимость указанного условия в данном утверждении'),
('Система выбирает между ответом внешней модели и проверенным формальным доказательством, и они противоречат друг другу. Какой источник должен иметь приоритет в архитектуре NEXUS-надсистемы?','Проверенное формальное доказательство/Authority')
]
@dataclass(frozen=True)
class B1Case:
    case_id:str;family:str;text:str;gold:str;options:dict|None;payload:dict
    def router_features(self):
        t=self.text or '';n=max(1,len(t));cyr=sum('а'<=c.lower()<='я' or c in 'ёЁ' for c in t)/n
        return {'support_count':float(len(self.payload.get('support',()))),'text_len':min(len(t)/240,1.0),'cyrillic_ratio':cyr,'option_count':float(len(self.options or {}))/4,'digit_count':min(sum(ch.isdigit() for ch in t)/8,1.0),'evidence_count':float(len(self.payload.get('teacher_rows',{})))/5,'guillemet_count':min(t.count('«')/4,1.0),'has_arrow':float('→' in t)}

def _ru_support_text(s,e,a,k):
    templates=[f'Опыт номер {k}: режим «{s}» дал следствие «{e}», а регулятор выбрал «{a}».',f'В демонстрации {k} состояние «{s}» связано с результатом «{e}» и командой «{a}».',f'Наблюдение {k}: при «{s}» появляется «{e}», управление — «{a}».']
    return templates[k%len(templates)]
def _id(r):return uuid.UUID(int=r.getrandbits(128)).hex
def _teacher_rows(gold,r):
    rows={};wrong_index=r.randrange(len(EVIDENCE_TEACHERS));wrong_label=r.choice([x for x in 'ABCD' if x!=gold])
    for i,t in enumerate(EVIDENCE_TEACHERS):
        chosen=wrong_label if i==wrong_index else gold;lp={a:-4.5 for a in 'ABCD'};lp[chosen]=(-3.0-r.random()*.2) if i==wrong_index else (-0.05-r.random()*.1);rows[t]={'pred':chosen,'option_logprobs':lp}
    return rows
def _formal(r):
    a,b=r.randint(3,29),r.randint(2,12);ans=a*b;vals=[ans+r.choice([-20,-10,10,20]),ans,ans+r.choice([-2,2,3]),ans+r.choice([5,7,9])];r.shuffle(vals);letters='ABCD';opts={letters[i]:str(vals[i]) for i in range(4)};gold=letters[vals.index(ans)];return f'Чему равно {a} × {b}?',opts,gold
def _case(fam,r,i):
    if fam=='fast_structured':
        p=list(range(4));a=list(range(4));r.shuffle(p);r.shuffle(a);q=r.randrange(4);intent=r.randrange(2);sup=[s for s in range(4) if s!=q];r.shuffle(sup);support=[(s,p[s],a[s]) for s in sup];gold=str((p if intent==0 else a)[q]);return B1Case(_id(r),fam,'',gold,None,{'support':support,'query_state':q,'intent':'effect' if intent==0 else 'action'})
    if fam=='fast_ru':
        p=list(range(4));a=list(range(4));r.shuffle(p);r.shuffle(a);q=r.randrange(4);intent=r.randrange(2);sup=[s for s in range(4) if s!=q];r.shuffle(sup);texts=[_ru_support_text(RU_ST[s],RU_E[p[s]],RU_A[a[s]],j+r.randrange(3)) for j,s in enumerate(sup)];qs=r.choice(RU_E_BL if intent==0 else RU_A_BL).format(s=RU_ST[q]);gold=(RU_E if intent==0 else RU_A)[(p if intent==0 else a)[q]];return B1Case(_id(r),fam,qs,gold,None,{'support':texts,'query':qs})
    if fam=='semantic_memory':
        q,g=SEMANTIC_ATOMS[i%len(SEMANTIC_ATOMS)];return B1Case(_id(r),fam,q,g,None,{'atom_index':i%len(SEMANTIC_ATOMS)})
    if fam=='formal_mcq':
        q,o,g=_formal(r);return B1Case(_id(r),fam,q,g,o,{})
    if fam=='morpholex':
        lang=r.choice(list(LANG_SAMPLES));text=r.choice(LANG_SAMPLES[lang]);return B1Case(_id(r),fam,text,lang,None,{})
    q=f'Независимые источники оценивают четыре гипотезы в эксперименте {r.randint(1000,9999)}. Какой вариант лучше подтверждён?';gold=r.choice(list('ABCD'));opts={a:f'гипотеза {a}' for a in 'ABCD'};return B1Case(_id(r),fam,q,gold,opts,{'teacher_rows':_teacher_rows(gold,r)})
def generate_splits(seed=6100,train_per_family=120,dev_per_family=30,test_per_family=60):
    out={}
    for si,(name,n) in enumerate([('train',train_per_family),('dev',dev_per_family),('test',test_per_family)]):
        r=random.Random(seed+si*100003);rows=[]
        for fam in FAMILIES:
            for i in range(n):rows.append(_case(fam,r,i+si*n))
        r.shuffle(rows);out[name]=tuple(rows)
    return out
