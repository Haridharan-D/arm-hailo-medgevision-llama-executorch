import hashlib,json
import pytest
from app.anomaly import AnomalyEngine

def test_only_manifested_nested_demo_images_can_be_opened(tmp_path):
    engine=AnomalyEngine(tmp_path);engine.contracts={'test':{}}
    folder=tmp_path/'samples/test';image=folder/'demo/safe/one.png';image.parent.mkdir(parents=True);image.write_bytes(b'image')
    (folder/'manifest.json').write_text(json.dumps([{'file':'demo/safe/one.png','sha256':hashlib.sha256(b'image').hexdigest()}]))
    assert engine.sample_path('test','demo/safe/one.png')[0]==image
    with pytest.raises(ValueError):engine.sample_path('test','../../escape.png')
    image.write_bytes(b'tampered')
    with pytest.raises(ValueError):engine.sample_path('test','demo/safe/one.png')
