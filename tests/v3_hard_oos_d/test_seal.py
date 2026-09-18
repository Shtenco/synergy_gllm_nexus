import pytest
from training.v3_hard_oos_d.seal import verify_checkpoint_hash

def test_checkpoint_hash_mismatch_aborts(tmp_path):
    p=tmp_path/'x.pt'; p.write_bytes(b'bad')
    with pytest.raises(ValueError,match='checkpoint hash mismatch'):
        verify_checkpoint_hash(p,'0'*64)
