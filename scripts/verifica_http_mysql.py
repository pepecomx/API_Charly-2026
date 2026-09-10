"""Read-only integration check: local HTTP API against the configured MySQL.
Uses an existing valid token in memory; never prints tokens or passwords.
"""
import json
import os
import sys
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import event, text
import uvicorn
from config.db import engine
from main import app

if engine.dialect.name != 'mysql':
    raise SystemExit('This integration check requires MySQL.')

@event.listens_for(engine, 'connect')
def read_only(dbapi, _):
    cursor = dbapi.cursor()
    cursor.execute('SET SESSION TRANSACTION READ ONLY')
    cursor.close()

server = None
try:
    with engine.connect() as conn:
        # Match the application clock too: the old API stores naive datetimes.
        user = conn.execute(text('SELECT IdUsuario, Token FROM usuarios WHERE FechaExpiracion >= :now AND Token IS NOT NULL AND Token <> :empty LIMIT 1'), {'now': datetime.now(), 'empty': ''}).mappings().first()
        if not user:
            raise SystemExit('No valid existing API token for the local application clock.')
        latest = conn.execute(text('SELECT FechaCreacionLocal FROM vision.eventos_vw1 WHERE FechaCreacionLocal IS NOT NULL ORDER BY FechaCreacionLocal DESC LIMIT 1')).scalar()
        if latest is None:
            raise SystemExit('The events view has no dated rows.')
        start = datetime.combine(latest.date(), datetime.min.time())
        end = start + timedelta(days=1)
        expected = conn.execute(text('SELECT COUNT(NombreLinea) FROM vision.eventos_vw1 WHERE FechaCreacionLocal >= :start AND FechaCreacionLocal < :end'), {'start':start,'end':end}).scalar_one()
        print('EVENT_DATE', start.date(), 'EXPECTED_COUNT', expected, flush=True)

    # Bind an OS-assigned local port before starting the HTTP server.
    config = uvicorn.Config(app, host='127.0.0.1', port=0, log_level='error', access_log=False)
    sock = config.bind_socket()
    port = sock.getsockname()[1]
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, kwargs={'sockets':[sock]}, daemon=True)
    thread.start()
    for _ in range(100):
        if server.started:
            break
        time.sleep(0.05)
    if not server.started:
        raise RuntimeError('Local HTTP server did not start')

    def get(path, params=None, body=None):
        url = f'http://127.0.0.1:{port}{path}'
        if params:
            url += '?' + urlencode(params)
        if body is not None:
            url = Request(url, data=json.dumps(body).encode(), headers={'Content-Type':'application/json'}, method='POST')
        try:
            with urlopen(url, timeout=40) as response:
                return response.status, json.load(response)
        except HTTPError as exc:
            return exc.code, json.load(exc)

    status, schema = get('/openapi.json')
    print('LOCAL_OPENAPI', status, 'ENDPOINTS', len(schema.get('paths',{})), flush=True)
    assert status == 200
    if os.getenv('API_USER') and os.getenv('API_PASSWORD'):
        status, token = get('/api/ObtieneToken/', body={'_IdUsuario':os.environ['API_USER'], '_contrasena':os.environ['API_PASSWORD']})
        print('LOCAL_GET_TOKEN_HTTP',status,flush=True)
        if status != 201:
            print('LOCAL_GET_TOKEN_MESSAGE', token.get('message') if isinstance(token,dict) else 'unexpected response',flush=True)
            raise SystemExit(1)
        assert isinstance(token,str) and token
        user = {'IdUsuario':os.environ['API_USER'], 'Token':token}
    status, rows = get('/api/obtieneEventos/', {'_IdUsuario': user['IdUsuario'], '_token': user['Token'], '_fecha': str(start.date())})
    print('LOCAL_EVENTS_HTTP', status, flush=True)
    assert status == 201, 'Events endpoint did not succeed'
    actual = sum(row['cantidad'] for row in rows)
    print('GROUPS', len(rows), 'RETURNED_COUNT', actual, 'MATCHES_DATABASE', actual == expected, flush=True)
    assert actual == expected and rows, 'Returned data does not match MySQL'
    print('JSON_FIELDS', sorted(rows[0]), flush=True)
    status, _ = get('/api/ObtieneToken/', body={'_IdUsuario':'diagnostico_inexistente_20260910','_contrasena':'not-real'})
    print('LOCAL_UNKNOWN_USER_HTTP',status,flush=True)
    assert status == 404
    # Verify both PUT routes without changing the remote account.
    if os.getenv('API_USER') and os.getenv('API_PASSWORD'):
        for path, body in [
            
            ('/api/actualizaContrasena/', {'_IdUsuario':os.environ['API_USER'], '_contrasenaActual':os.environ['API_PASSWORD']+'-incorrecta', '_contrasenaNueva':'not-applied'}),
        ]:
            req = Request(f'http://127.0.0.1:{port}{path}', data=json.dumps(body).encode(), headers={'Content-Type':'application/json'}, method='PUT')
            try:
                with urlopen(req,timeout=40) as response:
                    status=response.status
            except HTTPError as exc:
                status=exc.code
                exc.close()
            print('LOCAL_PUT_WRONG_PASSWORD',path,status,flush=True)
            assert status == 403
    status, _ = get('/api/obtieneToken/')
    assert status == 404
    status, _ = get('/api/actualizaToken/')
    assert status == 404
    assert set(schema['paths']) == {'/api/actualizaContrasena/','/api/ObtieneToken/','/api/obtieneEventos/'}
    print('READ_ONLY_INTEGRATION_OK', flush=True)
except Exception as exc:
    original = getattr(exc, 'orig', None)
    code = original.args[0] if original and original.args and isinstance(original.args[0], int) else None
    print('FAILURE_TYPE',type(exc).__name__,'MYSQL_CODE',code,flush=True)
    raise SystemExit(1)
finally:
    if server:
        server.should_exit = True
        thread.join(timeout=5)
        sock.close()
    engine.dispose()
