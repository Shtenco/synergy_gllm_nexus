"""NEXUS Cognitive Recursive Core (CRC-R1) experimental foundation."""
from .state import NexusCognitiveState, CognitiveTraceEvent, ComputeBudget
from .memory import MemoryLevel, MemoryRecord, HierarchicalMemoryStore
from .program_ast import ProgramKind, ProgramNode, ProgramSynthesizer
from .future_tree import BranchValue, FutureBranch, FutureTreePlanner
from .reward import RewardVector, RewardWeights, RPEngine
from .credit import CreditNode, CreditEdge, CognitiveTraceGraph
from .self_model import CapabilityEstimate, NexusSelfModel
from .meta_controller import MetaDecision, MetaController
from .continual import LearningTier, PromotionEvidence, ContinualLearningPolicy
