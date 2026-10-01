from nexus_gllm.unified_v3.cognitive.generalized_ingress_ollama import OllamaGeneralizedIngressBackend


def test_backend_exists():
    assert OllamaGeneralizedIngressBackend is not None
