from __future__ import annotations
from dataclasses import dataclass
import json
from urllib import request as urllib_request
from .generative import SurfaceContract

@dataclass(frozen=True)
class OllamaModelRef:
    model_id:str
    digest_sha256:str
    endpoint:str='http://127.0.0.1:11434'
    timeout_s:float=30.0

class OllamaTransport:
    def post_json(self,url,payload,timeout):
        body=json.dumps(payload,ensure_ascii=False).encode('utf-8')
        req=urllib_request.Request(url,data=body,headers={'Content-Type':'application/json'},method='POST')
        with urllib_request.urlopen(req,timeout=timeout) as resp:
            return json.loads(resp.read().decode('utf-8'))

class OllamaSurfaceBackend:
    """Surface-only Ollama adapter. It has no reasoning/memory/tool authority."""
    def __init__(self,model_ref:OllamaModelRef,transport=None):
        if len(model_ref.digest_sha256)!=64:
            raise ValueError('verified Ollama model digest required')
        self.ref=model_ref
        self.transport=transport or OllamaTransport()
        self.backend_id='ollama:'+model_ref.model_id
    @staticmethod
    def _prompt(c:SurfaceContract)->str:
        vals='; '.join(c.answer_values) if c.answer_values else '(нет отдельного значения)'
        entities='; '.join(c.entity_names) if c.entity_names else '(нет)'
        nums='; '.join(c.licensed_numbers) if c.licensed_numbers else '(нет)'
        uncertainty='; '.join(c.uncertainty) if c.uncertainty else '(нет)'
        return (
          'Сформулируй естественный краткий ответ на русском языке. '
          'Тебе запрещено добавлять новые факты, числа, имена, причины или источники. '
          'Используй только семантику ниже.\n'
          f'Эпистемический статус: {c.epistemic_state.value}\n'
          f'Разрешенные значения ответа: {vals}\n'
          f'Разрешенные сущности: {entities}\n'
          f'Разрешенные числа: {nums}\n'
          f'Неопределенность: {uncertainty}\n'
          f'Разрешено отрицание: {c.allow_negation}\n'
          'Верни только текст ответа.'
        )
    def generate(self,contract:SurfaceContract)->str:
        payload={'model':self.ref.model_id,'prompt':self._prompt(contract),'stream':False,'options':{'temperature':0.2}}
        data=self.transport.post_json(self.ref.endpoint.rstrip('/')+'/api/generate',payload,self.ref.timeout_s)
        text=data.get('response')
        if not isinstance(text,str) or not text.strip():
            raise RuntimeError('ollama returned empty surface')
        return text.strip()
