import json,time
from pathlib import Path
import cv2
import numpy as np
from fastapi.testclient import TestClient
from app.server import create_app

def test_nested_demo_images_are_reachable_but_cannot_escape_root(tmp_path):
    folder=tmp_path/'test_images/defects/crack';folder.mkdir(parents=True)
    image=np.full((80,80,3),120,np.uint8);cv2.imwrite(str(folder/'sample.jpg'),image)
    (folder.parent/'manifest.json').write_text(json.dumps([{'file':'defects/crack/sample.jpg','group':'crack','label_origin':'Prediction only'}]))
    outside=tmp_path/'private.jpg';cv2.imwrite(str(outside),image)
    class Service:
        def close(self):pass
        def inspect_anomaly(self,image,profile,source):return {'decision':'REVIEW','profile':profile,'source':source}
    cfg={'data_dir':tmp_path,'test_images':tmp_path/'test_images','profile_validated':False}
    with TestClient(create_app(cfg,Service())) as client:
        for _ in range(30):
            if client.get('/api/health').json()['ready']:break
            time.sleep(.01)
        rows=client.get('/api/library').json()
        assert rows[0]['group']=='crack' and rows[0]['label_origin']=='Prediction only'
        assert client.get(rows[0]['url']).status_code==200
        assert client.get('/api/library/image/%2E%2E/private.jpg').status_code==404
        assert client.post('/api/library/inspect',json={'name':'../private.jpg'}).status_code==404
        ok,encoded=cv2.imencode('.png',image)
        result=client.post('/api/anomaly/inspect-upload?profile=mvtec_pill',files={'file':('test.png',encoded.tobytes(),'image/png')})
        assert result.status_code==200 and result.json()['decision']=='REVIEW'
        bad=client.post('/api/anomaly/inspect-upload?profile=mvtec_pill',files={'file':('bad.png',b'broken','image/png')})
        assert bad.status_code==400
