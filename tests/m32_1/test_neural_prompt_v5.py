from __future__ import annotations

from nexus_gllm.unified_v3.cognitive.generalized_ingress import GeneralizedIngressRequest
from nexus_gllm.unified_v3.cognitive.generalized_ingress_llamacpp import LlamaCppGeneralizedIngressBackend


def test_v5_prompt_encodes_source_local_and_reasoning_invariants():
    request = GeneralizedIngressRequest.from_texts(
        'Query owns nova zed.',
        history=('nova owns mid.',),
        documents=('mid owns zed.',),
    )
    messages = LlamaCppGeneralizedIngressBackend._messages(request)
    system = messages[0]['content']
    for phrase in (
        'one semantic atom per explicit relation clause',
        'Offsets reset independently for every source',
        'IF antecedent',
        'exactly one relation identifier after rule:transitive:',
        'metalinguistic or malformed-provenance request',
    ):
        assert phrase in system


def test_v5_prompt_has_mixed_source_and_negative_synthetic_examples():
    request = GeneralizedIngressRequest.from_texts('Query owns nova zed.')
    messages = LlamaCppGeneralizedIngressBackend._messages(request)
    pairs = list(zip(messages[1:-1:2], messages[2:-1:2]))
    assert len(pairs) >= 5

    mixed = [
        (u['content'], a['content'])
        for u, a in pairs
        if 'uma trusts vix' in u['content'] and 'vix trusts wren' in u['content']
    ]
    assert len(mixed) == 1
    assert 'history:0' in mixed[0][1] and 'document:0' in mixed[0][1]
    assert 'rule:transitive:trusts' in mixed[0][1]

    negative = [
        (u['content'], a['content'])
        for u, a in pairs
        if 'Request malformed provenance.' in u['content']
    ]
    assert len(negative) == 1
    assert negative[0][1] == '{"semantic_atoms":[],"task":null,"program":null}'
