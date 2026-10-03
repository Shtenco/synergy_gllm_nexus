from __future__ import annotations
from dataclasses import dataclass
from .world_model import EmpiricalWorldModel


@dataclass(frozen=True)
class PlannedAction:
    action: str | None
    value: float
    branch_id: str | None
    depth: int
    expanded_nodes: int = 0
    max_expansions: int | None = None
    budget_exhausted: bool = False


@dataclass(frozen=True)
class _BeamNode:
    state: str
    first_action: str | None
    branch_id: str
    depth: int
    cumulative_value: float


class LearnedFuturePlanner:
    """Budgeted anytime beam planner over the empirical world model.

    ``max_depth`` is only a safety ceiling. The operational search resource is
    ``max_expansions``: every evaluated state/action transition consumes one
    expansion. This makes search effort measurable and allows the caller to
    scale planning compute without silently changing the scoring rule.

    The planner is anytime: when the expansion budget is exhausted it returns
    the best root policy found so far together with explicit telemetry.
    """

    def __init__(
        self,
        world_model: EmpiricalWorldModel,
        *,
        max_depth: int = 3,
        fanout: int = 4,
        beam_width: int = 12,
        gamma: float = .95,
        uncertainty_penalty: float = .25,
        max_expansions: int | None = None,
    ):
        if max_depth <= 0:
            raise ValueError("max_depth must be positive")
        if fanout <= 0 or beam_width <= 0:
            raise ValueError("fanout and beam_width must be positive")
        if max_expansions is not None and max_expansions <= 0:
            raise ValueError("max_expansions must be positive when provided")
        self.model = world_model
        self.max_depth = int(max_depth)
        self.fanout = int(fanout)
        self.beam_width = int(beam_width)
        self.gamma = float(gamma)
        self.uncertainty_penalty = float(uncertainty_penalty)
        self.max_expansions = None if max_expansions is None else int(max_expansions)

    def plan(self, state):
        root = _BeamNode(state, None, "root", 0, 0.0)
        beam = (root,)
        all_nodes = [root]
        expanded = 0
        budget_exhausted = False

        for depth in range(1, self.max_depth + 1):
            nxt = []
            stop = False
            for parent in beam:
                actions = self.model.known_actions(parent.state)[: self.fanout]
                for action in actions:
                    if self.max_expansions is not None and expanded >= self.max_expansions:
                        budget_exhausted = True
                        stop = True
                        break
                    pred = self.model.predict(parent.state, action)
                    expanded += 1
                    edge = (self.gamma ** (depth - 1)) * (
                        pred.expected_reward - self.uncertainty_penalty * pred.uncertainty
                    )
                    first = parent.first_action or action
                    node = _BeamNode(
                        pred.next_state,
                        first,
                        f"{parent.branch_id}/{action}",
                        depth,
                        parent.cumulative_value + edge,
                    )
                    nxt.append(node)
                    all_nodes.append(node)
                if stop:
                    break
            if nxt:
                nxt.sort(key=lambda n: (-n.cumulative_value, n.depth, n.branch_id))
                beam = tuple(nxt[: self.beam_width])
            else:
                break
            if stop:
                break

        candidates = [n for n in all_nodes if n.depth > 0]
        if not candidates:
            return PlannedAction(
                None,
                0.0,
                None,
                0,
                expanded_nodes=expanded,
                max_expansions=self.max_expansions,
                budget_exhausted=budget_exhausted,
            )
        best = max(candidates, key=lambda n: (n.cumulative_value, -n.depth, n.branch_id))
        return PlannedAction(
            best.first_action,
            best.cumulative_value,
            best.branch_id,
            best.depth,
            expanded_nodes=expanded,
            max_expansions=self.max_expansions,
            budget_exhausted=budget_exhausted,
        )
