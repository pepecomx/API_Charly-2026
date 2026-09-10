import logging
from sqlalchemy import text
from fastapi import APIRouter, Body
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


@dispositivoAPI.put('/api/actualizaContrasena/', status_code=200, summary='Actualiza contrasena')
async def actualiza_contrasena(
    *,
    id_usuario: str = Body(..., alias='_IdUsuario', min_length=1),
    contrasena_actual: str = Body(..., alias='_contrasenaActual', min_length=1),
    contrasena_nueva: str = Body(..., alias='_contrasenaNueva', min_length=1),
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

@dispositivoAPI.post('/api/ObtieneToken/', status_code=201, summary='Obtiene token')
async def obtiene_token_post(
    *,
    id_usuario: str = Body(..., alias='_IdUsuario', min_length=1),
    contrasena: str = Body(..., alias='_contrasena', min_length=1),
):
    """Devuelve el token vigente. Las credenciales se reciben en JSON."""
    return await obtiene_token(id_usuario, contrasena)

@dispositivoAPI.get('/api/obtieneEventos/', status_code=201)
async def obtiene_eventos(_IdUsuario: str, _token: str, _fecha: str):
    fecha_y_hora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        fecha_inicio = datetime.strptime(_fecha, '%Y-%m-%d')
        fecha_fin = fecha_inicio + timedelta(days=1)
    except ValueError:
        return JSONResponse(content={'message': 'Error en fecha!!'}, status_code=405)
    try:
        with engine.connect() as conn:
            datos = conn.execute(usuarios_c.select().where(usuarios_c.c.IdUsuario == _IdUsuario)).first()
            if datos is None:
                return JSONResponse(content={'message': 'Usuario no encontrado!!'}, status_code=401)
            if expire_date(0) > token_expiration(datos[4]):
                return JSONResponse(content={'message': 'Token caducado!!'}, status_code=406)
            if datos[3] != _token:
                return JSONResponse(content={'message': 'Token no valido!!'}, status_code=402)
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
        writeFile(_IdUsuario, fecha_y_hora, 'obtiene_eventos:Consulta exitosa')
        return result
    except Exception:
        logger.exception('Error procesando solicitud')
        return JSONResponse(content={'message': 'Error No identificado!!'}, status_code=500)
