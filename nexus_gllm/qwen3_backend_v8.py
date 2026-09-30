from __future__ import annotations
import json, urllib.request, urllib.error
from typing import Any

class Qwen3OpenAIBackendV8:
    """OpenAI-compatible backend for R2.1/Qwen3 llama-server or any compatible server."""
    def __init__(self,base_url:str="http://127.0.0.1:8080/v1/chat/completions",model:str="Qwen3-14B-Q4_K_M",api_key:str="none",timeout_s:int=1800):
        self.base_url=base_url; self.model=model; self.api_key=api_key; self.timeout_s=int(timeout_s)
    def available(self)->bool:
        url=self.base_url.rsplit("/chat/completions",1)[0]+"/models"
        req=urllib.request.Request(url,headers={"Authorization":f"Bearer {self.api_key}"})
        try:
            with urllib.request.urlopen(req,timeout=10) as r: return 200<=r.status<300
        except Exception:return False
    def generate(self,prompt:str,*,system:str,max_tokens:int=384,temperature:float=0.0)->dict[str,Any]:
        payload={"model":self.model,"messages":[{"role":"system","content":system},{"role":"user","content":prompt.rstrip()+"\n/no_think"}],"max_tokens":int(max_tokens),"temperature":float(temperature),"stream":False}
        req=urllib.request.Request(self.base_url,data=json.dumps(payload,ensure_ascii=False).encode(),method="POST",headers={"Content-Type":"application/json","Authorization":f"Bearer {self.api_key}"})
        try:
            with urllib.request.urlopen(req,timeout=self.timeout_s) as r: body=json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            detail=e.read().decode(errors="replace"); raise RuntimeError(f"Qwen3 HTTP {e.code}: {detail[-1500:]}") from e
        text=str(body["choices"][0]["message"]["content"]).strip()
        if not text: raise RuntimeError("Qwen3 returned empty response")
        return {"text":text,"backend":self.model,"usage":body.get("usage")}
