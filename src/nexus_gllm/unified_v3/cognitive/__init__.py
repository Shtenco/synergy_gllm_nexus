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

from .program_compiler import CompileStatus, CompileResult, CognitiveProgramCompiler

from .higher_order import HigherOrderStatus, HigherOrderContext, HigherOrderResult, HigherOrderExecutor

from .persistent_memory import MemoryVersion, PersistentMemoryIndex

from .world_model import TransitionPrediction, EmpiricalWorldModel
from .learned_planner import PlannedAction, LearnedFuturePlanner

from .credit_learning import CreditStat, RecursiveCreditLearner

from .promotion import ReplayMetrics, PromotionCandidate, PromotionDecision, GuardedPromotionGate

from .pre_ftx1 import PreFTX1Decision, PreFTX1FreezeGate

from .generative import SurfaceContract, SurfaceCandidate, SurfaceGuardResult, SafeSurfaceResult, DeterministicRussianSurface, SurfaceSemanticGuard, AuthoritySafeGenerativeCortex
from .generative_port import CRCGenerativePort, contract_from_epistemic

from .generative_admission import GenerativeArtifactKind, GenerativeArtifactSpec, GenerativeEvalMetrics, GenerativeAdmissionDecision, GenerativeCortexAdmissionGate
from .generative_registry import RegisteredGenerativeCortex, GenerativeCortexRegistry

from .ollama_surface import OllamaModelRef, OllamaTransport, OllamaSurfaceBackend
from .generative_selector import GenerativeBackendSelector

from .cognitive_loop import CognitiveRequest, CognitiveDecision, CognitiveLoopR1

from .language_cortex import SourceSpanRef, ProposedAtom, LanguageParseProposal, LanguageAdmission, LanguageParseResult, LanguageProposalGate, LanguageCortexPort, ControlledLanguageBackend
