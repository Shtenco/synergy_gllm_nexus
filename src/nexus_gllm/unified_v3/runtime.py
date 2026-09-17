from __future__ import annotations
from .contracts import *
from .surface import ControlledSurfaceAdapter,SurfaceRequest
from .role_binding import RoleBinder
from .world import WorldInducer
from .rule_induction import RuleInducer
from .task_induction import TaskInducer
from .executor import Executor
from .epistemic import EpistemicController
from .generalization import GeneralizationGovernor
from .renderer import RussianRenderer

class UnifiedNexusV3P0:
    def __init__(self):
        self.surface=ControlledSurfaceAdapter(); self.binder=RoleBinder(); self.world=WorldInducer(); self.rules=RuleInducer(); self.tasks=TaskInducer(); self.executor=Executor(); self.epistemic=EpistemicController(); self.generalization=GeneralizationGovernor(); self.renderer=RussianRenderer()
    def _execute_request(self,request,rule_program,task_program):
        obs=self.binder.bind(self.surface.parse(request)); world=self.world.from_observations((obs,))[0]
        if request.structured_query:
            task_program=TaskProgram(task_program.opcode,task_program.operator_id,tuple(x.casefold() for x in request.structured_query))
        return self.executor.execute(world,rule_program,task_program,max_steps=5)
    def respond(self,request:SurfaceRequest,*,demonstrations,task_examples,audit_variants=()):
        trace=[]
        obs=self.surface.parse(request); trace.append(TraceEvent('surface_parse'))
        obs=self.binder.bind(obs); trace.append(TraceEvent('bind'))
        world=self.world.from_observations((obs,))[0]; trace.append(TraceEvent('world_build'))
        rp=self.rules.induce(tuple(demonstrations)); trace.append(TraceEvent('rule_induce'))
        tp=self.tasks.induce(tuple(task_examples)); trace.append(TraceEvent('task_induce'))
        if request.structured_query:
            tp=TaskProgram(tp.opcode,tp.operator_id,tuple(x.casefold() for x in request.structured_query))
        ex=self.executor.execute(world,rp,tp,max_steps=5); trace.append(TraceEvent('execute'))
        ep=self.epistemic.resolve((ex,)); trace.append(TraceEvent('epistemic'))
        variants=tuple(self._execute_request(v,rp,tp) for v in audit_variants)
        audit=self.generalization.audit(ex,variants); trace.append(TraceEvent('generalization'))
        text=self.renderer.render(ep); trace.append(TraceEvent('render'))
        return V3Response(text,ep,ex,audit,rp,tp,tuple(trace))
