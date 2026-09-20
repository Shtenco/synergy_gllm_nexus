from pathlib import Path
import hashlib, json, shutil, subprocess
import pytest

from nexus_gllm.unified_v3.moe.exact_artifacts import ArtifactCatalog, ArtifactStatus

ROOT=Path(__file__).resolve().parents[2]
ART=ROOT/'artifacts/recovered/r7443_deployed/context-binder-r7443.js'
EXPECTED='d248bb75c45694bbde6914615243080b711d2efea80b22c2652e692cc8307703'

def test_r7443_deployed_hash_and_catalog_status():
    assert ART.is_file()
    assert hashlib.sha256(ART.read_bytes()).hexdigest()==EXPECTED
    rec=ArtifactCatalog.default(Path('/mnt/data')).verify('r7443')
    assert rec.status is ArtifactStatus.EXACT_DEPLOYED_RUNTIME

@pytest.mark.skipif(shutil.which('node') is None,reason='node runtime unavailable')
def test_r7443_six_frozen_context_contracts():
    harness=r"""
const fs=require('fs'),vm=require('vm');global.window={};
vm.runInThisContext(fs.readFileSync(process.argv[1],'utf8'));
const B=window.NexusR7443ContextBinder;
function ok(x,m){if(!x)throw new Error(m)}
let b=B.create(),r=b.before('Подбери налоги для ИП в Москве, B2B консалтинг, выручка 3 млн рублей, без сотрудников, нужен НДС');
ok(r.handled&&b.status().pending?.task_type==='TAX_DECISION','pending');
r=b.before('Какая ключевая ставка ЦБ сейчас?');ok(!r.handled&&b.status().pending===null&&b.status().suspended.includes('TAX_DECISION'),'verified interrupt');
b=B.create();b.before('Подбери налоги для ИП в Москве');b.before('Работать с НДС, B2B, консалтинг, выручка 3 млн, расходы указаны, без сотрудников');ok(b.pending.slots.vat_need==='да','vat positive');
b=B.create();b.before('Подбери налоги для ИП в Москве');b.before('Без НДС, B2C, магазин, выручка 2 млн, расходы указаны, без сотрудников');ok(b.pending.slots.vat_need==='нет','vat negative');
b=B.create();b.before('Расскажи про налоги');b.after('Расскажи про налоги',{category:'tax_answer',text:'Проверенный ответ'});r=b.before('Почему именно так?');ok(r.handled&&r.category==='dialog_context_followup','anaphora');
b=B.create();b.before('Расскажи про налоги');b.after('Расскажи про налоги',{category:'tax_answer',text:'Старый ответ'});r=b.before('Почему у Tesla снизилась маржа?');ok(!r.handled,'bare why isolation');
b=B.create();b.before('Подбери налоги для ИП в Москве');b.before('Другая тема: расскажи про оборотный капитал бизнеса');ok(b.status().suspended.length===0&&b.status().validated===null,'hard boundary');
b=B.create();b.before('Финансовая модель бизнеса: ООО в Москве, B2B консалтинг, капитал 2 млн рублей');r=b.before('Какая погода в Алматы?');ok(!r.handled&&b.status().suspended.includes('BUSINESS_PROFILE'),'suspend');r=b.before('Вернёмся к финансовой модели бизнеса: цена указана, объем продаж указан, переменные расходы указаны, постоянные расходы указаны, отсрочка оплаты, без сотрудников, без НДС');ok(r.handled&&r.category==='dialog_active_inquiry','resume');
console.log(JSON.stringify({passed:8,total:8}));
"""
    cp=subprocess.run(['node','-e',harness,str(ART)],capture_output=True,text=True,check=False)
    assert cp.returncode==0,cp.stderr
    assert json.loads(cp.stdout.strip())=={'passed':8,'total':8}
