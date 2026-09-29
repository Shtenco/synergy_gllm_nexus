from __future__ import annotations
import hashlib,json
from nexus_gllm.unified_v3.contracts import TaskOpcode
from .ollama_surface import OllamaModelRef,OllamaTransport
from .language_cortex import SourceSpanRef,ProposedAtom,LanguageParseProposal
from .task_cortex import TaskProposal

class _OllamaIngressBase:
    def __init__(self,model_ref:OllamaModelRef,transport=None):
        if len(model_ref.digest_sha256)!=64:raise ValueError('verified model digest required')
        self.ref=model_ref;self.transport=transport or OllamaTransport()
        self.backend_id='ollama-ingress:'+model_ref.model_id
    def _call(self,prompt):
        payload={'model':self.ref.model_id,'prompt':prompt,'stream':False,'format':'json','options':{'temperature':0}}
        data=self.transport.post_json(self.ref.endpoint.rstrip('/')+'/api/generate',payload,self.ref.timeout_s)
        raw=data.get('response')
        if not isinstance(raw,str):raise ValueError('missing JSON response')
        return json.loads(raw)

class OllamaLanguageCortexBackend(_OllamaIngressBase):
    """Neural semantic parser. Model proposes offsets; NEXUS computes span hashes."""
    def propose(self,text):
        prompt=(
          'Return strict JSON only. Parse factual semantic atoms from the input. '
          'Schema: {"atoms":[{"operator_id":"...", "arguments":["..."], '
          '"polarity":true, "confidence":0.0, "start":0, "end":1}]}. '
          'start/end are Python character offsets into the exact input. '
          'Do not answer the user and do not add facts.\nINPUT:\n'+text
        )
        data=self._call(prompt);atoms=[]
        for row in data.get('atoms',[]):
            start=int(row['start']);end=int(row['end'])
            if start<0 or end<=start or end>len(text):raise ValueError('invalid span bounds')
            digest=hashlib.sha256(text[start:end].encode('utf-8')).hexdigest()
            atoms.append(ProposedAtom(str(row['operator_id']),tuple(str(x) for x in row['arguments']),bool(row.get('polarity',True)),float(row['confidence']),SourceSpanRef(start,end,digest)))
        h=hashlib.sha256(text.encode('utf-8')).hexdigest()
        return LanguageParseProposal(h,self.backend_id,tuple(atoms))

class OllamaTaskCortexBackend(_OllamaIngressBase):
    """Neural intent parser. It proposes TaskProgram fields, never executes them."""
    def propose_task(self,text):
        prompt=(
          'Return strict JSON only. Identify the requested reasoning operation. '
          'Schema: {"opcode":"query_relation","operator_id":"r",'
          '"arguments":["a","b"],"confidence":0.0,"start":0,"end":1}. '
          'Use one opcode value from the provided system TaskOpcode vocabulary. '
          'Offsets refer to the exact input. Do not answer the question.\nINPUT:\n'+text
        )
        row=self._call(prompt);start=int(row['start']);end=int(row['end'])
        if start<0 or end<=start or end>len(text):raise ValueError('invalid span bounds')
        digest=hashlib.sha256(text[start:end].encode('utf-8')).hexdigest()
        h=hashlib.sha256(text.encode('utf-8')).hexdigest()
        opcode=TaskOpcode(str(row['opcode']))
        op=row.get('operator_id')
        return TaskProposal(h,self.backend_id,opcode,None if op is None else str(op),tuple(str(x) for x in row.get('arguments',())),float(row['confidence']),SourceSpanRef(start,end,digest))
