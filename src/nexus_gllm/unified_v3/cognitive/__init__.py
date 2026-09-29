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

from .semantic_authority import SemanticFactStatus, AttestationKind, SemanticAttestation, SemanticCommitDecision, SemanticCommitResult, SemanticCommitGate, atom_fingerprint

from .action_boundary import ActionRisk, ActionProposal, ExecutionPermit, ActionAuthorization, AuthorizedAction, ActionBoundary

from .belief_state import BeliefStatus, Belief, BeliefResolution, BeliefLedger
from .belief_bridge import ingest_semantic_commit

from .causal_model import CausalEvidenceKind, CausalEvidence, CausalEdge, CausalGraph, InterventionRecord, InterventionLedger

from .information_gain import HypothesisMass, QueryOutcome, InformationQuery, QueryScore, ActiveInformationSelector, entropy

from .memory_consolidation import ConsolidationProposal, ConsolidationResult, EvidencePreservingConsolidator

from .calibration import CalibrationObservation, CalibrationMetrics, CalibrationLedger

from .replay_bank import ReplayCase, ReplayOutcome, ReplayReport, FrozenReplayBank, AntiForgettingEvaluator
from .replay_promotion import promotion_candidate_from_replay

from .scientific_query import QueryActionSpec, ScientificQueryPlan, ScientificQueryPlanner

from .dialogue_context import ContextValueStatus, ContextValue, PendingSlot, Referent, DialogueContextState, DialogueContextR1
