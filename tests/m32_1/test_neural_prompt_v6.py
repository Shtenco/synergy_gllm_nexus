from __future__ import annotations

from nexus_gllm.unified_v3.cognitive.generalized_ingress import GeneralizedIngressRequest
from nexus_gllm.unified_v3.cognitive.generalized_ingress_llamacpp import LlamaCppGeneralizedIngressBackend


def test_v6_source_payload_exposes_independent_character_lengths():
    request = GeneralizedIngressRequest.from_texts(
        'Query trusts uma wren.',
        history=('uma trusts vix',),
        documents=('vix trusts wren',),
    )
    block = LlamaCppGeneralizedIngressBackend._source_block(request)
    assert '"char_len":22' in block
    assert '"char_len":14' in block
    assert '"char_len":15' in block


def test_v6_prompt_has_capacity_gate_rules():
    request = GeneralizedIngressRequest.from_texts('Query parent a c.', documents=('a parent b; b parent c',))
    system = LlamaCppGeneralizedIngressBackend._messages(request)[0]['content']
    for phrase in (
        'PROMPT is query-only',
        'Never synthesize operator names',
        'Never merge two explicit source clauses into one semantic atom',
        'Cyrillic proper names',
        'A modifier such as disputed is never an operator',
    ):
        assert phrase in system


def test_v6_fewshots_cover_same_source_chain_conflict_and_multilingual_identity():
    request = GeneralizedIngressRequest.from_texts('Query parent a c.')
    messages = LlamaCppGeneralizedIngressBackend._messages(request)
    assistants = [m['content'] for m in messages if m['role'] == 'assistant']
    joined = '\n'.join(assistants)
    assert 'rule:transitive:guides' in joined
    assert 'Check disputed owns fact.' in '\n'.join(m['content'] for m in messages if m['role'] == 'user')
    assert '"operator_id":"owns"' in joined
    assert '"arguments":["ava","ben"]' in joined
    assert '"arguments":["ben","cyra"]' in joined
