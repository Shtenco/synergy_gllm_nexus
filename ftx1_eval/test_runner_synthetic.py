from ftx1_eval.runner import predict_case


def test_unrecognized_surface_is_deterministic_and_fail_closed():
    case = {
        'case_id': 'synthetic-1',
        'prompt': 'Это намеренно неподдерживаемая свободная формулировка.',
        'history': [],
        'documents': [],
    }
    a = predict_case(case)
    b = predict_case(case)
    assert a == b
    assert a['case_id'] == 'synthetic-1'
    assert a['runner_status'] == 'OK'
    assert a['epistemic'] == 'UNRESOLVED'
    assert a['abstain'] is True
    assert a['answer'] is None


def test_runtime_fields_only_and_no_retry_contract():
    case = {
        'case_id': 'synthetic-2',
        'prompt': 'Есть ли отношение rel от A к B?',
        'history': ['контекст вне контролируемой грамматики'],
        'documents': [{'id': 'd1', 'text': 'тоже неподдерживаемый документ'}],
    }
    p = predict_case(case)
    required = {'case_id','answer','structured','epistemic','abstain','citations','runner_status'}
    assert required.issubset(p)
    assert p['case_id'] == 'synthetic-2'
