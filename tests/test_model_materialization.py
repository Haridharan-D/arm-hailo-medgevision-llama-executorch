import hashlib
import json
import pytest
from tools.materialize_models import materialize


def fixture_parts(tmp_path):
    folder = tmp_path/'model_parts'
    folder.mkdir()
    content = b'frozen model bytes'
    part = folder/'example.part'
    part.write_bytes(content)
    (folder/'manifest.json').write_text(json.dumps([dict(
        path='models/example.onnx', bytes=len(content),
        sha256=hashlib.sha256(content).hexdigest(),
        parts=[dict(path='model_parts/example.part', sha256=hashlib.sha256(content).hexdigest())])]))
    return content, part


def test_reconstructs_exact_bytes_and_is_idempotent(tmp_path):
    content, _ = fixture_parts(tmp_path)
    materialize(tmp_path)
    materialize(tmp_path)
    assert (tmp_path/'models/example.onnx').read_bytes() == content


def test_rejects_corrupted_part_before_publishing(tmp_path):
    _, part = fixture_parts(tmp_path)
    part.write_bytes(b'corruption')
    with pytest.raises(ValueError, match='Corrupted model part'):
        materialize(tmp_path)
    assert not (tmp_path/'models/example.onnx').exists()


def test_recovers_existing_invalid_model(tmp_path):
    content, _ = fixture_parts(tmp_path)
    target = tmp_path/'models/example.onnx'
    target.parent.mkdir()
    target.write_bytes(b'interrupted prior copy')
    materialize(tmp_path)
    assert target.read_bytes() == content
