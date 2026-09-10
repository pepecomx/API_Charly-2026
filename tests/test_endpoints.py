import asyncio
import json
import os
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch
from urllib.parse import urlencode

from sqlalchemy import create_engine, event, text
from sqlalchemy.pool import StaticPool
# Never connect to the deployment database from these regression tests.
os.environ['DATABASE_URL'] = 'sqlite://'
from main import app
from model.db_model import usuarios_c
from router import router

async def request(method, path, params=None, body=None):
    messages = []
    payload = json.dumps(body).encode() if body is not None else b''
    scope = {'type': 'http', 'asgi': {'version': '3.0'}, 'http_version': '1.1',
             'method': method, 'scheme': 'http', 'path': path, 'raw_path': path.encode(),
             'query_string': urlencode(params or {}).encode(), 'root_path': '',
             'headers': [(b'content-type', b'application/json')],
             'client': ('127.0.0.1', 1234), 'server': ('test', 80)}
    async def receive():
        return {'type': 'http.request', 'body': payload, 'more_body': False}
    async def send(message):
        messages.append(message)
    await app(scope, receive, send)
    status = next(m['status'] for m in messages if m['type'] == 'http.response.start')
    data = b''.join(m.get('body', b'') for m in messages if m['type'] == 'http.response.body')
    return status, json.loads(data)

class EndpointsTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://', poolclass=StaticPool, connect_args={'check_same_thread': False})
        @event.listens_for(self.engine, 'connect')
        def setup(dbapi, _):
            dbapi.create_function('hour', 1, lambda value: datetime.fromisoformat(value).hour)
            dbapi.execute("ATTACH DATABASE ':memory:' AS vision")
        usuarios_c.create(self.engine)
        with self.engine.begin() as conn:
            conn.execute(usuarios_c.insert().values(IdUsuario='test', NombreUsuario='Test',
                Contrasena=router.secret_pwd.encrypt(b'test-password').decode(),
                Token='test-token', FechaExpiracion=(datetime.now()+timedelta(days=1)).isoformat(' ')))
            conn.execute(text('CREATE TABLE vision.eventos_vw1 (NombreLinea TEXT, NombreSeccion TEXT, Accion TEXT, FechaCreacionLocal TEXT)'))
            for moment in ['2026-09-01 10:00:00', '2026-09-01 10:30:00', '2026-09-02 00:00:00']:
                conn.execute(text("INSERT INTO vision.eventos_vw1 VALUES ('L1','S1','entrada',:moment)"), {'moment': moment})
        self.patch = patch.object(router, 'engine', self.engine)
        self.patch.start()
        self.logpatch = patch.object(router, 'writeFile')
        self.logpatch.start()
        self.addCleanup(self.engine.dispose)
        self.addCleanup(self.patch.stop)
        self.addCleanup(self.logpatch.stop)

    def call(self, method, path, **kwargs):
        return asyncio.run(request(method, path, **kwargs))

    def test_get_token(self):
        status, data = self.call('POST','/api/ObtieneToken/',body={'_IdUsuario':'test','_contrasena':'test-password'})
        self.assertEqual(status,201)
        self.assertEqual(data,'test-token')

    def test_events_grouping_json_and_day_boundary(self):
        status, data = self.call('GET','/api/obtieneEventos/',params={'_IdUsuario':'test','_token':'test-token','_fecha':'2026-09-01'})
        self.assertEqual(status,201)
        self.assertEqual(len(data),1)
        self.assertEqual(data[0]['cantidad'],2)
        self.assertEqual(data[0]['hora'],10)

    def test_no_events(self):
        status,data=self.call('GET','/api/obtieneEventos/',params={'_IdUsuario':'test','_token':'test-token','_fecha':'2020-01-01'})
        self.assertEqual((status,data),(201,[]))

    def test_update_token_persists(self):
        response=asyncio.run(router.actualiza_token(id_usuario='test',contrasena='test-password'))
        status=response.status_code
        self.assertEqual(status,201)
        with self.engine.connect() as conn:
            token=conn.execute(usuarios_c.select()).mappings().one()['Token']
        self.assertIsInstance(token,str)
        self.assertNotEqual(token,'test-token')
        self.assertEqual(self.call('POST','/api/ObtieneToken/',body={'_IdUsuario':'test','_contrasena':'test-password'}),(201,token))

    def test_update_password_persists(self):
        status,_=self.call('PUT','/api/actualizaContrasena/',body={'_IdUsuario':'test','_contrasenaActual':'test-password','_contrasenaNueva':'new-password'})
        self.assertEqual(status,200)
        with self.engine.connect() as conn:
            password=conn.execute(usuarios_c.select()).mappings().one()['Contrasena']
        self.assertEqual(router.secret_pwd.decrypt(password.encode()),b'new-password')

    def test_errors(self):
        cases=[('POST','/api/ObtieneToken/',{'_IdUsuario':'missing','_contrasena':'bad'},404),
               ('POST','/api/ObtieneToken/',{'_IdUsuario':'test','_contrasena':'bad'},401),
               ('GET','/api/obtieneEventos/',{'_IdUsuario':'test','_token':'bad','_fecha':'2026-09-01'},402),
               ('GET','/api/obtieneEventos/',{'_IdUsuario':'test','_token':'test-token','_fecha':'bad'},405)]
        for method,path,params,expected in cases:
            with self.subTest(path=path,expected=expected):
                self.assertEqual(self.call(method,path,**({'body':params} if method == 'POST' else {'params':params}))[0],expected)
        self.assertEqual(self.call('PUT','/api/actualizaToken/',body={})[0],404)
        self.assertEqual(self.call('PUT','/api/actualizaContrasena/',body={})[0],422)

    def test_expired_token(self):
        with self.engine.begin() as conn:
            conn.execute(usuarios_c.update().values(FechaExpiracion='2000-01-01 00:00:00'))
        self.assertEqual(self.call('POST','/api/ObtieneToken/',body={'_IdUsuario':'test','_contrasena':'test-password'})[0],406)

    def test_wrong_password_does_not_write(self):
        for path, body in [
            
            ('/api/actualizaContrasena/', {'_IdUsuario':'test','_contrasenaActual':'bad','_contrasenaNueva':'new'}),
        ]:
            with self.subTest(path=path):
                self.assertEqual(self.call('PUT',path,body=body)[0],403)
        with self.engine.connect() as conn:
            row=conn.execute(usuarios_c.select()).mappings().one()
        self.assertEqual(row['Token'],'test-token')
        self.assertEqual(router.secret_pwd.decrypt(row['Contrasena'].encode()),b'test-password')

    def test_only_requested_routes_active(self):
        paths=app.openapi()['paths']
        self.assertEqual({(path,method) for path,methods in paths.items() for method in methods}, {
            ('/api/actualizaContrasena/','put'), ('/api/ObtieneToken/','post'), ('/api/obtieneEventos/','get')})
        self.assertEqual(self.call('GET','/api/obtieneToken/')[0],404)
        self.assertEqual(self.call('GET','/api/ObtieneToken/')[0],405)
        self.assertEqual(self.call('POST','/api/ObtieneToken/',params={'_IdUsuario':'test','_contrasena':'test-password'})[0],422)
        self.assertEqual(len(router.rutas_desactivadas.routes),2)

    def test_password_change_invalidates_old_credentials(self):
        payload={'_IdUsuario':'test','_contrasenaActual':'test-password','_contrasenaNueva':'new-password'}
        self.assertEqual(self.call('PUT','/api/actualizaContrasena/',body=payload)[0],200)
        self.assertEqual(self.call('POST','/api/ObtieneToken/',body={'_IdUsuario':'test','_contrasena':'test-password'})[0],401)
        status,token=self.call('POST','/api/ObtieneToken/',body={'_IdUsuario':'test','_contrasena':'new-password'})
        self.assertEqual(status,201)
        self.assertNotEqual(token,'test-token')
        self.assertEqual(self.call('GET','/api/obtieneEventos/',params={'_IdUsuario':'test','_token':'test-token','_fecha':'2026-09-01'})[0],402)
        self.assertEqual(self.call('PUT','/api/actualizaContrasena/',body=payload)[0],403)
        self.assertEqual(self.call('POST','/api/ObtieneToken/',body={'_IdUsuario':'test','_contrasena':'new-password'}),(201,token))

    def test_empty_or_unchanged_password_rejected(self):
        for new in ['', 'test-password']:
            self.assertEqual(self.call('PUT','/api/actualizaContrasena/',body={'_IdUsuario':'test','_contrasenaActual':'test-password','_contrasenaNueva':new})[0],422)

    def test_connection_failure_returns_json(self):
        with patch.object(router.engine,'connect',side_effect=RuntimeError('DB unavailable')):
            with self.assertLogs(router.logger,level='ERROR'):
                status,data=self.call('POST','/api/ObtieneToken/',body={'_IdUsuario':'test','_contrasena':'test-password'})
        self.assertEqual(status,500)
        self.assertIn('message',data)

if __name__ == '__main__':
    unittest.main()
