from __future__ import annotations

from nexus_gllm.unified_v3.cognitive.generalized_ingress import GeneralizedIngressRequest
from nexus_gllm.unified_v3.cognitive.generalized_ingress_llamacpp import LlamaCppGeneralizedIngressBackend


def test_shallow_typed_fewshots_teach_values_not_schema_metavocabulary():
    request = GeneralizedIngressRequest.from_texts(
        'Is Alice parent Carol?',
        history=('Alice parent Bob.',),
        documents=('Bob parent Carol.',),
    )
    messages = LlamaCppGeneralizedIngressBackend._messages(request)
    assistants = [m['content'] for m in messages if m['role'] == 'assistant']
    assert len(assistants) >= 3
    joined = '\n'.join(assistants)

    # Demonstrations must use the same shallow typed IR as the enforced schema.
    assert '"semantic_atoms"' in joined
    assert '"task"' in joined
    assert '"program_recipe"' in joined
    assert '"kind":"transitive"' in joined
    assert '"kind":"composition"' in joined
    assert '"kind":"counterfactual_transitive"' in joined

    # They must demonstrate grounded source values rather than recursive AST/offset work.
    assert '"operator_id":"follows"' in joined
    assert '"arguments":["mira","noah"]' in joined
    assert '"operators":["follows"]' in joined
    assert '"source_ids":["document:0"]' in joined
    assert '"node"' not in joined
    assert '"spans"' not in joined


def test_system_contract_explicitly_separates_schema_labels_from_source_values():
    request = GeneralizedIngressRequest.from_texts(
        'Query parent alice carol.',
        documents=('alice parent bob; bob parent carol',),
    )
    system = LlamaCppGeneralizedIngressBackend._messages(request)[0]['content']
    assert 'Schema labels are not source values' in system
    assert 'query_relation is an opcode, never a relation operator_id' in system
    assert 'operator_id must come from the relation/predicate expressed in SOURCES' in system
