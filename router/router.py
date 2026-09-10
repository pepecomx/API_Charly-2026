import logging
from sqlalchemy import text
from fastapi import APIRouter, Body, Query
from fastapi.responses import JSONResponse
from jwt_file.function_jwt import expire_date, writeFile
from router.local import key
from config.db import engine
from model.db_model import usuarios_c
from cryptography.fernet import Fernet
from datetime import datetime, timedelta
secret_pwd = Fernet(key)
key2 = Fernet.generate_key()
secret_Token = Fernet(key2)
logger = logging.getLogger(__name__)
dispositivoAPI = APIRouter()
# Preserved routes: intentionally NOT included in main.app.
rutas_desactivadas = APIRouter()

def token_expiration(value):
    # Drivers may return DATETIME as datetime or a string from legacy columns.
    return value if isinstance(value, datetime) else datetime.fromisoformat(value)


@dispositivoAPI.put('/api/actualizaContrasena/', status_code=200, summary='Actualizacontrasena', operation_id='actualizaContrasena_api_actualizaContrasena__put')
async def actualiza_contrasena(
    *,
    id_usuario: str = Query(..., alias='_IdUsuario', min_length=1, description='Identificador del usuario de la API.'),
    contrasena_actual: str = Query(..., alias='_contrasenaActual', min_length=1, description='Contrasena actual del usuario.'),
    contrasena_nueva: str = Query(..., alias='_contrasenaNueva', min_length=1, description='Nueva contrasena; debe ser diferente de la actual.'),
):
    """Cambia la contrasena verificando la actual e invalida el token anterior."""
    fecha_y_hora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        with engine.begin() as conn:
            datos = conn.execute(
                usuarios_c.select().where(usuarios_c.c.IdUsuario == id_usuario).with_for_update()
            ).mappings().first()
            if datos is None:
                return JSONResponse(content={'message': 'Usuario no encontrado!!'}, status_code=401)
            actual = secret_pwd.decrypt(datos['Contrasena'].encode('utf-8')).decode('utf-8')
            if contrasena_actual != actual:
                return JSONResponse(content={'message': 'Contrasena actual no correcta!!'}, status_code=403)
            if contrasena_nueva == actual:
                return JSONResponse(content={'message': 'La nueva contrasena debe ser diferente'}, status_code=422)
            conn.execute(usuarios_c.update().where(usuarios_c.c.IdUsuario == id_usuario).values(
                Contrasena=secret_pwd.encrypt(contrasena_nueva.encode('utf-8')).decode('utf-8'),
                Token=secret_Token.encrypt(contrasena_nueva.encode('utf-8')).decode('utf-8'),
                FechaExpiracion=expire_date(2),
            ))
        writeFile(id_usuario, fecha_y_hora, 'actualiza_contrasena:Contrasena actualizada')
        return {'message': 'Contrasena actualizada correctamente'}
    except Exception:
        logger.exception('Error procesando cambio de contrasena')
        return JSONResponse(content={'message': 'Error No identificado!!'}, status_code=500)

@rutas_desactivadas.put('/api/actualizaToken/', status_code=201)
async def actualiza_token(*, id_usuario: str=Body(..., alias='_IdUsuario'), contrasena: str=Body(..., alias='_contrasena')):
    fecha_y_hora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        with engine.begin() as conn:
            id = conn.execute(usuarios_c.select().where(usuarios_c.c.IdUsuario == id_usuario)).first()
            if id != None:
                datos = conn.execute(usuarios_c.select().where(usuarios_c.c.IdUsuario == id_usuario)).first()
                contrasena_int = secret_pwd.decrypt(datos[2].encode('utf-8'))
                contrasena_int_s = str(contrasena_int.decode())
                if contrasena == contrasena_int_s:
                    fecha_hoy = expire_date(0)
                    token = secret_Token.encrypt(contrasena.encode('utf-8')).decode('utf-8')
                    fecha = expire_date(2)
                    result_t = conn.execute(usuarios_c.update().values(Token=token).where(usuarios_c.c.IdUsuario == id_usuario))
                    result_f = conn.execute(usuarios_c.update().values(FechaExpiracion=fecha).where(usuarios_c.c.IdUsuario == id_usuario))
                    writeFile(id_usuario, fecha_y_hora, 'actualiza_token:Token actualizado')
                    return JSONResponse(content={'message': 'Token actualizado'}, status_code=201)
                else:
                    writeFile(id_usuario, fecha_y_hora, 'actualiza_token:ContraseÃ±a actual no correcta!!')
                    return JSONResponse(content={'message': 'ContraseÃ±a actual no correcta!!'}, status_code=403)
            else:
                writeFile(id_usuario, fecha_y_hora, 'actualiza_token:Usuario no encontrado!!')
                return JSONResponse(content={'message': 'Usuario no encontrado!!'}, status_code=401)
    except Exception:
        logger.exception('Error procesando solicitud')
        writeFile(id_usuario, fecha_y_hora, 'actualiza_token:Error No identificado!!')
        return JSONResponse(content={'message': 'Error No identificado!!'}, status_code=500)

@rutas_desactivadas.get('/api/obtieneToken/', status_code=201)
async def obtiene_token(_IdUsuario: str, _contrasena: str):
    fecha_y_hora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        with engine.connect() as conn:
            id = conn.execute(usuarios_c.select().where(usuarios_c.c.IdUsuario == _IdUsuario)).first()
            if id != None:
                datos = conn.execute(usuarios_c.select().where(usuarios_c.c.IdUsuario == _IdUsuario)).first()
                contrasena_int = secret_pwd.decrypt(datos[2].encode('utf-8'))
                contrasena_int_s = str(contrasena_int.decode())
                if _contrasena == contrasena_int_s:
                    fecha_hoy = expire_date(0)
                    if fecha_hoy <= token_expiration(datos[4]):
                        writeFile(_IdUsuario, fecha_y_hora, 'obtiene_token:Token Enviado')
                        return datos[3]
                    else:
                        writeFile(_IdUsuario, fecha_y_hora, 'obtiene_token:Token caducado')
                        return JSONResponse(content={'message': 'Token caducado'}, status_code=406)
                else:
                    writeFile(_IdUsuario, fecha_y_hora, 'obtiene_token:Contraseña actual no correcta!!')
                    return JSONResponse(content={'message': 'Contraseña actual no correcta'}, status_code=401)
            else:
                writeFile(_IdUsuario, fecha_y_hora, 'obtiene_token:Usuario no encontrado!!')
                return JSONResponse(content={'message': 'Usuario no encontrado'}, status_code=404)
    except Exception:
        logger.exception('Error procesando solicitud')
        writeFile(_IdUsuario, fecha_y_hora, 'obtiene_token:Error No identificado!!')
        return JSONResponse(content={'message': 'Error No identificado!!'}, status_code=500)

@dispositivoAPI.post('/api/ObtieneToken/', status_code=200, summary='Obtienetoken', operation_id='ObtieneToken_api_ObtieneToken__post')
async def obtiene_token_post(
    *,
    id_usuario: str = Query(..., alias='_IdUsuario', min_length=1, description='Identificador del usuario de la API.'),
    contrasena: str = Query(..., alias='_contrasena', min_length=1, description='Contrasena del usuario de la API.'),
):
    """Devuelve el token vigente. Completa los campos y pulsa Execute para obtener el token vigente."""
    token = await obtiene_token(id_usuario, contrasena)
    if isinstance(token, JSONResponse):
        return token
    return {'Token': token}

@dispositivoAPI.get('/api/obtieneEventos/', status_code=200, summary='Obtiene Eventos')
async def obtiene_eventos(
    _token: str = Query(..., min_length=1, description='Token devuelto por POST /api/ObtieneToken/. Pegalo sin comillas ni el prefijo Bearer.'),
    _fecha: str = Query(
        ...,
        description=(
            'Fecha del dia a consultar en formato **AAAA-MM-DD** (ano-mes-dia). '
            'Ejemplo: **2026-09-10** = 10 de septiembre de 2026. '
            'Usa guiones y dos digitos para mes y dia; no incluyas hora, barras ni comillas. '
            'Consulta el dia completo segun FechaCreacionLocal, sin incluir el dia siguiente. '
            'Si no hay eventos para esa fecha, se devuelve una lista vacia [].'
        ),
        examples=['2026-09-10'],
    ),
):
    fecha_y_hora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        fecha_inicio = datetime.strptime(_fecha, '%Y-%m-%d')
        fecha_fin = fecha_inicio + timedelta(days=1)
    except ValueError:
        return JSONResponse(content={'message': 'Error en fecha!!'}, status_code=405)
    try:
        with engine.connect() as conn:
            datos = conn.execute(usuarios_c.select().where(usuarios_c.c.Token == _token)).first()
            if datos is None or datos[3] != _token:
                return JSONResponse(content={'message': 'Token no valido!!'}, status_code=402)
            if expire_date(0) > token_expiration(datos[4]):
                return JSONResponse(content={'message': 'Token caducado!!'}, status_code=406)
            query = text("""
                SELECT NombreLinea, NombreSeccion, Accion AS clasif,
                       HOUR(FechaCreacionLocal) AS hora,
                       MIN(FechaCreacionLocal) AS FechaCreacionLocal,
                       COUNT(NombreLinea) AS cantidad
                FROM vision.eventos_vw1
                WHERE FechaCreacionLocal >= :fecha_inicio
                  AND FechaCreacionLocal < :fecha_fin
                GROUP BY NombreLinea, NombreSeccion, Accion, HOUR(FechaCreacionLocal)
                ORDER BY NombreLinea, NombreSeccion, clasif, hora
            """)
            result = [dict(row) for row in conn.execute(query, {
                'fecha_inicio': str(fecha_inicio), 'fecha_fin': str(fecha_fin)
            }).mappings().all()]
        writeFile(datos[0], fecha_y_hora, 'obtiene_eventos:Consulta exitosa')
        return result
    except Exception:
        logger.exception('Error procesando solicitud')
        return JSONResponse(content={'message': 'Error No identificado!!'}, status_code=500)
