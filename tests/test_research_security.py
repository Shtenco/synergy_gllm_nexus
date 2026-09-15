import pytest
from nexus_gllm.research.security import validate_public_http_url
from nexus_gllm.research.source_normalizer import normalize_url

def test_ssrf_guards_and_normalization():
    for u in ['http://127.0.0.1/x','http://10.0.0.1/x','file:///etc/passwd','http://169.254.169.254/latest']:
        with pytest.raises(ValueError): validate_public_http_url(u)
    assert normalize_url('https://Example.com/a?utm_source=x&b=2#frag') == 'https://example.com/a?b=2'