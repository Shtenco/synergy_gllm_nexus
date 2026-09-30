import re
from ..contracts import ExpertContext,ExpertProposal,CapabilityTag
class R72LanguageExpert:
    expert_id='r72'
    def propose(self,context:ExpertContext):
        text=str(context.meta().get('text','')).strip().rstrip('.'); low=text.casefold()
        m=re.match(r'(?P<dst>\w+) получил от (?P<src>\w+) (?P<obj>\w+)',low); facts=[]
        if m:
            src=m.group('src'); dst=m.group('dst'); obj=m.group('obj')
            if src.endswith('ы'): src=src[:-1]+'а'
            facts.append((src,'передать',obj,dst))
        return ExpertProposal('r72:proposal',self.expert_id,CapabilityTag.LANGUAGE,semantic_facts=tuple(facts),confidence=.96 if facts else 0.0,uncertainty=.04 if facts else 1.0,provenance=('russian_binder',))
