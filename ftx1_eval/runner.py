from __future__ import annotations
import argparse, json
from pathlib import Path
from nexus_gllm.unified_v3.cognitive.conversation_shell import ConversationShellR1
from nexus_gllm.unified_v3.cognitive.conversational_reasoner import ConversationalReasonerR1

RUNTIME_COMMIT='fded8bd46777b2e868620b4c85d60c5c375b5ec1'

def predict_case(case: dict) -> dict:
    cid=str(case['case_id'])
    shell=ConversationShellR1('ftx1:'+cid)
    try:
        for d in case.get('documents', ()):
            text=d.get('text','') if isinstance(d,dict) else str(d[1] if isinstance(d,(list,tuple)) and len(d)>1 else d)
            shell.ingest(str(text))
        for turn in case.get('history', ()):
            shell.ingest(str(turn))
        result=ConversationalReasonerR1(shell).answer(str(case.get('prompt','')))
        ep=result.epistemic
        values=tuple(str(x) for x in ep.answer)
        answer=values[0] if len(values)==1 else ('|'.join(values) if values else None)
        abstain=ep.state.value in ('UNRESOLVED','CONFLICTED')
        return {'case_id':cid,'answer':answer,'structured':[],'epistemic':ep.state.value,'abstain':abstain,'citations':[],'runner_status':'OK'}
    except Exception as exc:
        return {'case_id':cid,'answer':None,'structured':[],'epistemic':'UNRESOLVED','abstain':True,'citations':[],'runner_status':'ERROR','error_type':type(exc).__name__}

def run_jsonl(inp: Path, out: Path) -> int:
    count=0
    with inp.open('r',encoding='utf-8') as fi, out.open('w',encoding='utf-8',newline='\n') as fo:
        for line in fi:
            if not line.strip(): continue
            pred=predict_case(json.loads(line))
            fo.write(json.dumps(pred,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n')
            count+=1
    return count

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--input',required=True);ap.add_argument('--output',required=True);a=ap.parse_args()
    n=run_jsonl(Path(a.input),Path(a.output));print(json.dumps({'runtime_commit':RUNTIME_COMMIT,'predictions':n},sort_keys=True))
if __name__=='__main__':main()
