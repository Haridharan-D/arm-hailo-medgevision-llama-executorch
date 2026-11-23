import json
from app.auth import LocalAuth,credential

def test_explicit_kiosk_access_preserves_saved_accounts(tmp_path):
    path=tmp_path/'users.json';path.write_text(json.dumps({'old':credential('test-password-123','administrator')}));before=path.read_bytes()
    assert LocalAuth(tmp_path).required is True
    kiosk=LocalAuth(tmp_path,required=False)
    assert kiosk.required is False and kiosk.user(None)['name']=='local-operator'
    assert path.read_bytes()==before
    assert LocalAuth(tmp_path,required=True).user(None) is None

def test_saved_account_does_not_reenable_http_login(tmp_path):
    import time
    from fastapi.testclient import TestClient
    from app.server import create_app
    from app.store import Store
    (tmp_path/'users.json').write_text(json.dumps({'old':credential('test-password-123','administrator')}))
    class Service:
        store=Store(tmp_path)
        def close(self):pass
    with TestClient(create_app({'data_dir':tmp_path,'auth_required':False},Service())) as client:
        for _ in range(50):
            if client.get('/api/health').json()['ready']:break
            time.sleep(.01)
        assert client.get('/api/auth/me').json()['required'] is False
        assert client.get('/api/batches').status_code==200
        assert client.get('/display').status_code==200
