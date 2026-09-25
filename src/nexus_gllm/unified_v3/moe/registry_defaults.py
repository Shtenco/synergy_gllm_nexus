from .contracts import *
from .registry import ExpertRegistry
def build_default_registry():
    reg=ExpertRegistry()
    active=[
      ExpertSpec('r7l','R7-L D192',(CapabilityTag.FAST_INDUCTION,), 'r7_fast',None,None,'R7LFastInductionExpert',ExpertMode.ACTIVE,1000,.99,ExpertProvenanceKind.ADAPTER_RECONSTRUCTION),
      ExpertSpec('r72','R7.2',(CapabilityTag.LANGUAGE,), 'r7_fast',None,None,'R72LanguageExpert',ExpertMode.ACTIVE,1000,.98,ExpertProvenanceKind.ADAPTER_RECONSTRUCTION),
      ExpertSpec('r718','R7.18',(CapabilityTag.EVIDENCE,CapabilityTag.PROOF), 'r7_late',None,None,'R718EvidenceExpert',ExpertMode.ACTIVE,1200,.96,ExpertProvenanceKind.ADAPTER_RECONSTRUCTION),
      ExpertSpec('r744','R7.44.3',(CapabilityTag.CONTEXT,), 'r744',None,None,'R744ContextExpert',ExpertMode.ACTIVE,1000,.99,ExpertProvenanceKind.ADAPTER_RECONSTRUCTION),
      ExpertSpec('graph','Omega-1.5R2',(CapabilityTag.GRAPH,), 'omega_graph',None,None,'Omega15R2GraphExpert',ExpertMode.ACTIVE,1000,.95,ExpertProvenanceKind.ADAPTER_RECONSTRUCTION),
      ExpertSpec('v3','v3-P0.1',(CapabilityTag.HYPOTHESIS,), 'v3',None,None,'V3HypothesisExpert',ExpertMode.ACTIVE,1500,1.0,ExpertProvenanceKind.NATIVE_V3),
    ]
    shadow=[('r76','R7.6',CapabilityTag.SEMANTIC_MEMORY,'r7_sem'),('r78','R7.8',CapabilityTag.FORMAL,'r7_proof'),('r710','R7.10',CapabilityTag.PROOF,'r7_proof'),('r714','R7.14',CapabilityTag.MORPHOLOGY,'r7_lang'),('v10','V10 600K',CapabilityTag.PROCEDURAL,'v10'),('unified_r13','Unified R1.3',CapabilityTag.OPEN_SET,'unified'),('v30','V30',CapabilityTag.PROCEDURAL,'v30')]
    for s in active: reg.register(s)
    for eid,ver,cap,line in shadow: reg.register(ExpertSpec(eid,ver,(cap,),line,None,None,'ShadowAdapter',ExpertMode.SHADOW,2000,.5,ExpertProvenanceKind.ADAPTER_RECONSTRUCTION))
    return reg
