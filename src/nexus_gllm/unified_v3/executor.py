from __future__ import annotations
from .contracts import *
class Executor:
    def execute(self,world:WorldHypothesis,rules:RuleProgram,task:TaskProgram,*,max_steps:int=5)->ExecutionResult:
        if not isinstance(world,WorldHypothesis): raise TypeError('world must be WorldHypothesis')
        if task.opcode is not TaskOpcode.QUERY_RELATION or not task.operator_id or len(task.arguments)!=2:
            return ExecutionResult(None)
        opid=task.operator_id; src,dst=task.arguments
        direct={(f.arguments[0].entity_id,f.arguments[1].entity_id):DerivedFact(f,(),None,1) for f in world.facts if f.operator.operator_id==opid and len(f.arguments)==2 and f.polarity}
        if (src,dst) in direct: return ExecutionResult(True,direct[(src,dst)])
        if not rules.has_property('transitive'): return ExecutionResult(None)
        adjacency={}
        for (a,b),df in direct.items(): adjacency.setdefault(a,[]).append((b,df.fact))
        queue=[(src,0,())]; seen={(src,0)}
        while queue:
            node,depth,path=queue.pop(0)
            if depth>=max_steps: continue
            for nxt,fact in adjacency.get(node,[]):
                nd=depth+1; np=path+(fact,)
                if nxt==dst:
                    out=WorldFact(OperatorSymbol(opid,2),(Entity(src),Entity(dst)))
                    return ExecutionResult(True,DerivedFact(out,np,'rule:transitive',nd))
                key=(nxt,nd)
                if key not in seen:
                    seen.add(key); queue.append((nxt,nd,np))
        return ExecutionResult(None)
