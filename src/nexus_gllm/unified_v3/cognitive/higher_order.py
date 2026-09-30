from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from nexus_gllm.unified_v3.contracts import (
    Entity, ExecutionResult, Intervention, InterventionKind, OperatorSymbol,
    TaskOpcode, TaskProgram, WorldFact, WorldHypothesis, FactLifecycle,
)
from nexus_gllm.unified_v3.counterfactual import CounterfactualEngine
from nexus_gllm.unified_v3.executor import Executor
from nexus_gllm.unified_v3.temporal import TemporalLedger
from .program_ast import ProgramKind, ProgramNode
from .program_compiler import CognitiveProgramCompiler, CompileStatus


class HigherOrderStatus(str, Enum):
    EXECUTED = "EXECUTED"
    CONDITION_FALSE = "CONDITION_FALSE"
    INHIBITED = "INHIBITED"
    UNRESOLVED = "UNRESOLVED"
    MALFORMED = "MALFORMED"
    MISSING_CONTEXT = "MISSING_CONTEXT"


@dataclass(frozen=True)
class HigherOrderContext:
    world: WorldHypothesis
    task: TaskProgram
    temporal_ledger: TemporalLedger | None = None


@dataclass(frozen=True)
class HigherOrderResult:
    status: HigherOrderStatus
    execution: ExecutionResult = ExecutionResult(None)
    trace: tuple[str, ...] = ()
    world_id: str | None = None


class HigherOrderExecutor:
    """Typed CRC-R1 higher-order AST interpreter.

    IF(condition, body)
    INHIBIT(blocker, body)
    TEMPORAL(child, mode=current | time=<int>)
    COUNTERFACTUAL(child, kind/op/src/dst[/polarity])

    Primitive rule atoms are delegated to the existing V3 Executor. No
    benchmark-specific solver or name-similarity fallback is used.
    """

    def __init__(self):
        self.executor = Executor()
        self.compiler = CognitiveProgramCompiler()
        self.counterfactual = CounterfactualEngine()

    @staticmethod
    def _params(node: ProgramNode) -> dict[str, str]:
        return dict(node.params)

    @staticmethod
    def _task_for(node: ProgramNode, fallback: TaskProgram) -> TaskProgram:
        p = dict(node.params)
        if not any(k in p for k in ("query_operator", "query_src", "query_dst")):
            return fallback
        if not all(k in p for k in ("query_operator", "query_src", "query_dst")):
            raise ValueError("partial query override")
        return TaskProgram(TaskOpcode.QUERY_RELATION, p["query_operator"], (p["query_src"], p["query_dst"]))

    @staticmethod
    def _aggregate(results: list[HigherOrderResult], kind: str) -> HigherOrderResult:
        if not results:
            return HigherOrderResult(HigherOrderStatus.MALFORMED, trace=(f"{kind}:empty",))
        for r in results:
            if r.status is not HigherOrderStatus.EXECUTED:
                return HigherOrderResult(r.status, r.execution, tuple(x for z in results for x in z.trace), r.world_id)
        truths = [r.execution.truth for r in results]
        truth = False if any(t is False for t in truths) else (True if all(t is True for t in truths) else None)
        last = results[-1]
        return HigherOrderResult(
            HigherOrderStatus.EXECUTED,
            ExecutionResult(truth, last.execution.derivation, last.execution.answer),
            tuple(x for r in results for x in r.trace) + (f"{kind}:aggregate:{truth}",),
            last.world_id,
        )

    def _primitive(self, node: ProgramNode, ctx: HigherOrderContext) -> HigherOrderResult:
        compiled = self.compiler.compile(node)
        if compiled.status is not CompileStatus.COMPILED or compiled.execution_mode != "rule_program":
            return HigherOrderResult(HigherOrderStatus.MALFORMED, trace=("primitive:compile_failed",), world_id=ctx.world.world_id)
        try:
            task = self._task_for(node, ctx.task)
        except ValueError:
            return HigherOrderResult(HigherOrderStatus.MALFORMED, trace=("primitive:partial_query_override",), world_id=ctx.world.world_id)
        out = self.executor.execute(ctx.world, compiled.rule_program, task)
        if out.truth is None and task.operator_id and len(task.arguments) == 2:
            src_id, dst_id = task.arguments
            negative = next((
                f for f in ctx.world.facts
                if f.operator.operator_id == task.operator_id
                and len(f.arguments) == 2
                and f.arguments[0].entity_id == src_id
                and f.arguments[1].entity_id == dst_id
                and f.polarity is False
            ), None)
            if negative is not None:
                from nexus_gllm.unified_v3.contracts import DerivedFact
                out = ExecutionResult(
                    False,
                    DerivedFact(negative, (), "explicit_negative", 1, world_id=ctx.world.world_id),
                )
        return HigherOrderResult(HigherOrderStatus.EXECUTED, out, (f"ATOM:{node.symbol}:{out.truth}",), ctx.world.world_id)

    @staticmethod
    def _temporal_world(base: WorldHypothesis, ledger: TemporalLedger, *, mode: str, time: int | None) -> WorldHypothesis:
        keys = {(v.relation, v.subject) for v in ledger.versions}
        kept = [
            f for f in base.facts
            if not (len(f.arguments) == 2 and (f.operator.operator_id, f.arguments[0].entity_id) in keys)
        ]
        selected = []
        for relation, subject in sorted(keys):
            v = ledger.current(relation, subject) if mode == "current" else ledger.at(relation, subject, int(time))
            if v is None:
                continue
            selected.append(WorldFact(OperatorSymbol(relation, 2), (Entity(subject), Entity(v.value)), True))
        return WorldHypothesis(base.world_id + f":temporal:{mode}:{time}", tuple(kept + selected), parent_world_id=base.world_id)

    def _counterfactual_context(self, node: ProgramNode, ctx: HigherOrderContext) -> HigherOrderContext | None:
        p = self._params(node)
        try:
            kind = InterventionKind[p["kind"]]
        except (KeyError, ValueError):
            return None
        if kind not in (InterventionKind.ADD_FACT, InterventionKind.REMOVE_FACT, InterventionKind.FLIP_POLARITY):
            return None
        if not all(k in p for k in ("operator", "src", "dst")):
            return None
        polarity = p.get("polarity", "true").lower() not in ("0", "false", "no")
        fact = WorldFact(OperatorSymbol(p["operator"], 2), (Entity(p["src"]), Entity(p["dst"])), polarity)
        world = self.counterfactual.apply(ctx.world, (Intervention(kind, fact),))
        return HigherOrderContext(world, ctx.task, ctx.temporal_ledger)

    def execute(self, node: ProgramNode, ctx: HigherOrderContext) -> HigherOrderResult:
        if node.kind is ProgramKind.ATOM:
            return self._primitive(node, ctx)

        if node.kind in (ProgramKind.SEQUENCE, ProgramKind.COMPOSE):
            if not node.children:
                return HigherOrderResult(HigherOrderStatus.MALFORMED, trace=(f"{node.kind.value}:empty",), world_id=ctx.world.world_id)
            return self._aggregate([self.execute(c, ctx) for c in node.children], node.kind.value)

        if node.kind is ProgramKind.IF:
            if len(node.children) != 2:
                return HigherOrderResult(HigherOrderStatus.MALFORMED, trace=("IF:arity",), world_id=ctx.world.world_id)
            cond = self.execute(node.children[0], ctx)
            if cond.status is not HigherOrderStatus.EXECUTED:
                return cond
            if cond.execution.truth is None:
                return HigherOrderResult(HigherOrderStatus.UNRESOLVED, cond.execution, cond.trace + ("IF:unresolved",), ctx.world.world_id)
            if cond.execution.truth is False:
                return HigherOrderResult(HigherOrderStatus.CONDITION_FALSE, cond.execution, cond.trace + ("IF:false",), ctx.world.world_id)
            body = self.execute(node.children[1], ctx)
            return HigherOrderResult(body.status, body.execution, cond.trace + ("IF:true",) + body.trace, body.world_id)

        if node.kind is ProgramKind.INHIBIT:
            if len(node.children) != 2:
                return HigherOrderResult(HigherOrderStatus.MALFORMED, trace=("INHIBIT:arity",), world_id=ctx.world.world_id)
            blocker = self.execute(node.children[0], ctx)
            if blocker.status is not HigherOrderStatus.EXECUTED:
                return blocker
            if blocker.execution.truth is None:
                return HigherOrderResult(HigherOrderStatus.UNRESOLVED, blocker.execution, blocker.trace + ("INHIBIT:unresolved",), ctx.world.world_id)
            if blocker.execution.truth is True:
                return HigherOrderResult(HigherOrderStatus.INHIBITED, ExecutionResult(None), blocker.trace + ("INHIBIT:blocked",), ctx.world.world_id)
            body = self.execute(node.children[1], ctx)
            return HigherOrderResult(body.status, body.execution, blocker.trace + ("INHIBIT:open",) + body.trace, body.world_id)

        if node.kind is ProgramKind.TEMPORAL:
            if len(node.children) != 1:
                return HigherOrderResult(HigherOrderStatus.MALFORMED, trace=("TEMPORAL:arity",), world_id=ctx.world.world_id)
            if ctx.temporal_ledger is None:
                return HigherOrderResult(HigherOrderStatus.MISSING_CONTEXT, trace=("TEMPORAL:no_ledger",), world_id=ctx.world.world_id)
            p = self._params(node)
            if "time" in p:
                try:
                    time = int(p["time"])
                except ValueError:
                    return HigherOrderResult(HigherOrderStatus.MALFORMED, trace=("TEMPORAL:bad_time",), world_id=ctx.world.world_id)
                mode = "at"
            elif p.get("mode") == "current":
                mode, time = "current", None
            else:
                return HigherOrderResult(HigherOrderStatus.MALFORMED, trace=("TEMPORAL:missing_mode",), world_id=ctx.world.world_id)
            world = self._temporal_world(ctx.world, ctx.temporal_ledger, mode=mode, time=time)
            out = self.execute(node.children[0], HigherOrderContext(world, ctx.task, ctx.temporal_ledger))
            return HigherOrderResult(out.status, out.execution, (f"TEMPORAL:{mode}:{time}",) + out.trace, world.world_id)

        if node.kind is ProgramKind.COUNTERFACTUAL:
            if len(node.children) != 1:
                return HigherOrderResult(HigherOrderStatus.MALFORMED, trace=("COUNTERFACTUAL:arity",), world_id=ctx.world.world_id)
            cf = self._counterfactual_context(node, ctx)
            if cf is None:
                return HigherOrderResult(HigherOrderStatus.MALFORMED, trace=("COUNTERFACTUAL:bad_intervention",), world_id=ctx.world.world_id)
            out = self.execute(node.children[0], cf)
            return HigherOrderResult(out.status, out.execution, ("COUNTERFACTUAL:applied",) + out.trace, cf.world.world_id)

        return HigherOrderResult(HigherOrderStatus.MALFORMED, trace=(f"unknown:{node.kind}",), world_id=ctx.world.world_id)
