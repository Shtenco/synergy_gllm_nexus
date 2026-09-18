from __future__ import annotations
from .contracts import *
from .rule_algebra import RuleFamily
class Executor:
    def _closure(self,world,rules,max_steps):
        facts=list(world.facts); seen={(f.operator.operator_id,tuple(x.entity_id for x in f.arguments),f.polarity) for f in facts}
        clauses=getattr(rules,'clauses',())
        for _ in range(max_steps):
            added=[]
            for c in clauses:
                if c.family is RuleFamily.SYMMETRIC:
                    op=c.operators[0]
                    for f in facts:
                        if f.operator.operator_id==op and f.polarity and len(f.arguments)==2:
                            nf=WorldFact(f.operator,(f.arguments[1],f.arguments[0]),True); key=(op,(nf.arguments[0].entity_id,nf.arguments[1].entity_id),True)
                            if key not in seen: seen.add(key); added.append(nf)
                elif c.family is RuleFamily.INVERSE:
                    a,b=c.operators[:2]
                    for f in facts:
                        if f.operator.operator_id==a and f.polarity and len(f.arguments)==2:
                            nf=WorldFact(OperatorSymbol(b,2),(f.arguments[1],f.arguments[0]),True); key=(b,(nf.arguments[0].entity_id,nf.arguments[1].entity_id),True)
                            if key not in seen: seen.add(key); added.append(nf)
                elif c.family is RuleFamily.TRANSITIVE:
                    op=c.operators[0]; rows=[f for f in facts if f.operator.operator_id==op and f.polarity and len(f.arguments)==2]
                    for x in rows:
                        for y in rows:
                            if x.arguments[1]==y.arguments[0]:
                                nf=WorldFact(x.operator,(x.arguments[0],y.arguments[1]),True); key=(op,(nf.arguments[0].entity_id,nf.arguments[1].entity_id),True)
                                if key not in seen: seen.add(key); added.append(nf)
                elif c.family is RuleFamily.COMPOSITION:
                    a,b,cop=c.operators; xs=[f for f in facts if f.operator.operator_id==a and f.polarity]; ys=[f for f in facts if f.operator.operator_id==b and f.polarity]
                    for x in xs:
                        for y in ys:
                            if len(x.arguments)==2 and len(y.arguments)==2 and x.arguments[1]==y.arguments[0]:
                                nf=WorldFact(OperatorSymbol(cop,2),(x.arguments[0],y.arguments[1]),True); key=(cop,(nf.arguments[0].entity_id,nf.arguments[1].entity_id),True)
                                if key not in seen: seen.add(key); added.append(nf)
            if not added: break
            facts.extend(added)
        return facts
    def execute(self,world:WorldHypothesis,rules:RuleProgram,task:TaskProgram,*,max_steps:int=5)->ExecutionResult:
        if not isinstance(world,WorldHypothesis): raise TypeError('world must be WorldHypothesis')
        if task.opcode not in (TaskOpcode.QUERY_RELATION,TaskOpcode.FIND_PROOF,TaskOpcode.FIND_MINIMAL_PROOF) or not task.operator_id or len(task.arguments)!=2: return ExecutionResult(None)
        opid=task.operator_id; src,dst=task.arguments
        allfacts=self._closure(world,rules,max_steps)
        match=[f for f in allfacts if f.operator.operator_id==opid and len(f.arguments)==2 and f.arguments[0].entity_id==src and f.arguments[1].entity_id==dst and f.polarity]
        if match:
            direct=next((f for f in world.facts if f in match),None)
            if direct: return ExecutionResult(True,DerivedFact(direct,(),None,1,world_id=world.world_id))
            if rules.has_property('transitive'):
                adj={}
                for f in world.facts:
                    if f.operator.operator_id==opid and f.polarity and len(f.arguments)==2: adj.setdefault(f.arguments[0].entity_id,[]).append((f.arguments[1].entity_id,f))
                q=[(src,0,())]; vis={src}
                while q:
                    n,d,path=q.pop(0)
                    for nxt,f in adj.get(n,[]):
                        np=path+(f,)
                        if nxt==dst: return ExecutionResult(True,DerivedFact(match[0],np,'rule:transitive',d+1,world_id=world.world_id))
                        if nxt not in vis and d+1<max_steps: vis.add(nxt); q.append((nxt,d+1,np))
            rid=getattr(getattr(rules,'clauses',(None,))[0],'family',None)
            return ExecutionResult(True,DerivedFact(match[0],(),rid.value if rid else None,2,world_id=world.world_id))
        if rules.has_property('transitive') and not getattr(rules,'clauses',()):
            adj={}
            for f in world.facts:
                if f.operator.operator_id==opid and f.polarity and len(f.arguments)==2: adj.setdefault(f.arguments[0].entity_id,[]).append((f.arguments[1].entity_id,f))
            q=[(src,0,())]; vis={(src,0)}
            while q:
                n,d,path=q.pop(0)
                if d>=max_steps: continue
                for nxt,f in adj.get(n,[]):
                    nd=d+1; np=path+(f,)
                    if nxt==dst: return ExecutionResult(True,DerivedFact(WorldFact(OperatorSymbol(opid,2),(Entity(src),Entity(dst))),np,'rule:transitive',nd,world_id=world.world_id))
                    k=(nxt,nd)
                    if k not in vis: vis.add(k); q.append((nxt,nd,np))
        return ExecutionResult(None)
