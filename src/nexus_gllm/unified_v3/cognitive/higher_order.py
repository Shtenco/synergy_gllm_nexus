from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, replace
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
class HigherOrderStep:
    """Execution evidence for one AST occurrence that was actually evaluated."""

    program_id: str
    ast_kind: ProgramKind
    status: HigherOrderStatus
    execution: ExecutionResult = ExecutionResult(None)
    world_id: str | None = None
    evidence_kind: str = "UNRESOLVED"
    verified: bool = False
    step_path: tuple[int, ...] = ()


@dataclass(frozen=True)
class ProofCoverageCertificate:
    """Coverage over answer-dependent AST occurrences that were actually evaluated."""

    required_node_ids: tuple[str, ...]
    verified_node_ids: tuple[str, ...]
    unverified_node_ids: tuple[str, ...]
    coverage: float
    complete: bool


@dataclass(frozen=True)
class HigherOrderResult:
    status: HigherOrderStatus
    execution: ExecutionResult = ExecutionResult(None)
    trace: tuple[str, ...] = ()
    world_id: str | None = None
    steps: tuple[HigherOrderStep, ...] = ()

    @staticmethod
    def _path_suffix(path: tuple[int, ...]) -> str:
        return "root" if not path else ".".join(str(i) for i in path)

    def step_identity(self, step: HigherOrderStep) -> str:
        counts = Counter(s.program_id for s in self.steps)
        if counts[step.program_id] == 1:
            return step.program_id
        return f"{step.program_id}@{self._path_suffix(step.step_path)}"

    @property
    def proof_coverage(self) -> ProofCoverageCertificate:
        required = tuple(self.step_identity(step) for step in self.steps)
        verified = tuple(self.step_identity(step) for step in self.steps if step.verified)
        unverified = tuple(self.step_identity(step) for step in self.steps if not step.verified)
        coverage = (len(verified) / len(required)) if required else 0.0
        return ProofCoverageCertificate(
            required_node_ids=required,
            verified_node_ids=verified,
            unverified_node_ids=unverified,
            coverage=coverage,
            complete=bool(required) and not unverified,
        )


class HigherOrderExecutor:
    """Typed CRC-R1 higher-order AST interpreter.

    IF(condition, body)
    INHIBIT(blocker, body)
    TEMPORAL(child, mode=current | time=<int>)
    COUNTERFACTUAL(child, kind/op/src/dst[/polarity])

    Primitive rule atoms are delegated to the existing V3 Executor. No
    benchmark-specific solver or name-similarity fallback is used.

    Every result carries an execution ledger containing only AST occurrences
    that were actually evaluated. step_path is root-relative, so repeated
    semantic programs executed in different temporal/counterfactual contexts
    remain distinct proof and credit-assignment occurrences.
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
    def _step(
        node: ProgramNode,
        status: HigherOrderStatus,
        execution: ExecutionResult,
        world_id: str | None,
        *,
        evidence_kind: str,
        verified: bool,
    ) -> HigherOrderStep:
        return HigherOrderStep(
            program_id=node.program_id,
            ast_kind=node.kind,
            status=status,
            execution=execution,
            world_id=world_id,
            evidence_kind=evidence_kind,
            verified=bool(verified),
        )

    @staticmethod
    def _terminal_verified(result: HigherOrderResult) -> bool:
        return bool(result.steps and result.steps[-1].verified)

    @staticmethod
    def _result(
        node: ProgramNode,
        status: HigherOrderStatus,
        execution: ExecutionResult = ExecutionResult(None),
        trace: tuple[str, ...] = (),
        world_id: str | None = None,
        *,
        children: tuple[HigherOrderResult, ...] = (),
        evidence_kind: str = "DETERMINISTIC",
        verified: bool = False,
    ) -> HigherOrderResult:
        child_steps = tuple(
            replace(step, step_path=(child_index,) + step.step_path)
            for child_index, child in enumerate(children)
            for step in child.steps
        )
        step = HigherOrderExecutor._step(
            node,
            status,
            execution,
            world_id,
            evidence_kind=evidence_kind,
            verified=verified,
        )
        return HigherOrderResult(status, execution, trace, world_id, child_steps + (step,))

    def _aggregate(self, node: ProgramNode, results: list[HigherOrderResult], kind: str, world_id: str) -> HigherOrderResult:
        if not results:
            return self._result(
                node,
                HigherOrderStatus.MALFORMED,
                trace=(f"{kind}:empty",),
                world_id=world_id,
                evidence_kind="INVALID",
                verified=False,
            )
        for r in results:
            if r.status is not HigherOrderStatus.EXECUTED:
                trace = tuple(x for z in results for x in z.trace)
                return self._result(
                    node,
                    r.status,
                    r.execution,
                    trace,
                    r.world_id,
                    children=tuple(results),
                    evidence_kind="DETERMINISTIC",
                    verified=False,
                )
        truths = [r.execution.truth for r in results]
        truth = False if any(t is False for t in truths) else (True if all(t is True for t in truths) else None)
        last = results[-1]
        execution = ExecutionResult(truth, last.execution.derivation, last.execution.answer)
        verified = all(self._terminal_verified(r) for r in results) and truth is not None
        return self._result(
            node,
            HigherOrderStatus.EXECUTED,
            execution,
            tuple(x for r in results for x in r.trace) + (f"{kind}:aggregate:{truth}",),
            last.world_id,
            children=tuple(results),
            evidence_kind="DETERMINISTIC",
            verified=verified,
        )

    def _primitive(self, node: ProgramNode, ctx: HigherOrderContext) -> HigherOrderResult:
        compiled = self.compiler.compile(node)
        if compiled.status is not CompileStatus.COMPILED or compiled.execution_mode != "rule_program":
            return self._result(
                node,
                HigherOrderStatus.MALFORMED,
                trace=("primitive:compile_failed",),
                world_id=ctx.world.world_id,
                evidence_kind="INVALID",
                verified=False,
            )
        try:
            task = self._task_for(node, ctx.task)
        except ValueError:
            return self._result(
                node,
                HigherOrderStatus.MALFORMED,
                trace=("primitive:partial_query_override",),
                world_id=ctx.world.world_id,
                evidence_kind="INVALID",
                verified=False,
            )
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
        verified = out.truth is not None and out.derivation is not None
        return self._result(
            node,
            HigherOrderStatus.EXECUTED,
            out,
            (f"ATOM:{node.symbol}:{out.truth}",),
            ctx.world.world_id,
            evidence_kind="PROOF" if verified else "UNRESOLVED",
            verified=verified,
        )

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
                return self._result(
                    node,
                    HigherOrderStatus.MALFORMED,
                    trace=(f"{node.kind.value}:empty",),
                    world_id=ctx.world.world_id,
                    evidence_kind="INVALID",
                    verified=False,
                )
            return self._aggregate(
                node,
                [self.execute(c, ctx) for c in node.children],
                node.kind.value,
                ctx.world.world_id,
            )

        if node.kind is ProgramKind.IF:
            if len(node.children) != 2:
                return self._result(node, HigherOrderStatus.MALFORMED, trace=("IF:arity",), world_id=ctx.world.world_id, evidence_kind="INVALID", verified=False)
            cond = self.execute(node.children[0], ctx)
            if cond.status is not HigherOrderStatus.EXECUTED:
                return self._result(node, cond.status, cond.execution, cond.trace, ctx.world.world_id, children=(cond,), verified=False)
            if cond.execution.truth is None:
                return self._result(node, HigherOrderStatus.UNRESOLVED, cond.execution, cond.trace + ("IF:unresolved",), ctx.world.world_id, children=(cond,), verified=False)
            if cond.execution.truth is False:
                return self._result(node, HigherOrderStatus.CONDITION_FALSE, cond.execution, cond.trace + ("IF:false",), ctx.world.world_id, children=(cond,), verified=self._terminal_verified(cond))
            body = self.execute(node.children[1], ctx)
            return self._result(node, body.status, body.execution, cond.trace + ("IF:true",) + body.trace, body.world_id, children=(cond, body), verified=self._terminal_verified(cond) and self._terminal_verified(body))

        if node.kind is ProgramKind.INHIBIT:
            if len(node.children) != 2:
                return self._result(node, HigherOrderStatus.MALFORMED, trace=("INHIBIT:arity",), world_id=ctx.world.world_id, evidence_kind="INVALID", verified=False)
            blocker = self.execute(node.children[0], ctx)
            if blocker.status is not HigherOrderStatus.EXECUTED:
                return self._result(node, blocker.status, blocker.execution, blocker.trace, ctx.world.world_id, children=(blocker,), verified=False)
            if blocker.execution.truth is None:
                return self._result(node, HigherOrderStatus.UNRESOLVED, blocker.execution, blocker.trace + ("INHIBIT:unresolved",), ctx.world.world_id, children=(blocker,), verified=False)
            if blocker.execution.truth is True:
                return self._result(node, HigherOrderStatus.INHIBITED, ExecutionResult(None), blocker.trace + ("INHIBIT:blocked",), ctx.world.world_id, children=(blocker,), verified=self._terminal_verified(blocker))
            body = self.execute(node.children[1], ctx)
            return self._result(node, body.status, body.execution, blocker.trace + ("INHIBIT:open",) + body.trace, body.world_id, children=(blocker, body), verified=self._terminal_verified(blocker) and self._terminal_verified(body))

        if node.kind is ProgramKind.TEMPORAL:
            if len(node.children) != 1:
                return self._result(node, HigherOrderStatus.MALFORMED, trace=("TEMPORAL:arity",), world_id=ctx.world.world_id, evidence_kind="INVALID", verified=False)
            if ctx.temporal_ledger is None:
                return self._result(node, HigherOrderStatus.MISSING_CONTEXT, trace=("TEMPORAL:no_ledger",), world_id=ctx.world.world_id, evidence_kind="MISSING_CONTEXT", verified=False)
            p = self._params(node)
            if "time" in p:
                try:
                    time = int(p["time"])
                except ValueError:
                    return self._result(node, HigherOrderStatus.MALFORMED, trace=("TEMPORAL:bad_time",), world_id=ctx.world.world_id, evidence_kind="INVALID", verified=False)
                mode = "at"
            elif p.get("mode") == "current":
                mode, time = "current", None
            else:
                return self._result(node, HigherOrderStatus.MALFORMED, trace=("TEMPORAL:missing_mode",), world_id=ctx.world.world_id, evidence_kind="INVALID", verified=False)
            world = self._temporal_world(ctx.world, ctx.temporal_ledger, mode=mode, time=time)
            out = self.execute(node.children[0], HigherOrderContext(world, ctx.task, ctx.temporal_ledger))
            return self._result(node, out.status, out.execution, (f"TEMPORAL:{mode}:{time}",) + out.trace, world.world_id, children=(out,), verified=self._terminal_verified(out))

        if node.kind is ProgramKind.COUNTERFACTUAL:
            if len(node.children) != 1:
                return self._result(node, HigherOrderStatus.MALFORMED, trace=("COUNTERFACTUAL:arity",), world_id=ctx.world.world_id, evidence_kind="INVALID", verified=False)
            cf = self._counterfactual_context(node, ctx)
            if cf is None:
                return self._result(node, HigherOrderStatus.MALFORMED, trace=("COUNTERFACTUAL:bad_intervention",), world_id=ctx.world.world_id, evidence_kind="INVALID", verified=False)
            out = self.execute(node.children[0], cf)
            return self._result(node, out.status, out.execution, ("COUNTERFACTUAL:applied",) + out.trace, cf.world.world_id, children=(out,), verified=self._terminal_verified(out))

        return self._result(node, HigherOrderStatus.MALFORMED, trace=(f"unknown:{node.kind}",), world_id=ctx.world.world_id, evidence_kind="INVALID", verified=False)
