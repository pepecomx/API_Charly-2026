# API Charly: contrato activo y pruebas

## Endpoints activos

| Método | Ruta exacta | Entrada | Éxito |
|---|---|---|---|
| PUT | /api/actualizaContrasena/ | JSON: _IdUsuario, _contrasenaActual, _contrasenaNueva | 200 y mensaje |
| POST | /api/ObtieneToken/ | JSON: _IdUsuario, _contrasena | 201 y token como cadena JSON |
| GET | /api/obtieneEventos/ | Query: _IdUsuario, _token, _fecha (YYYY-MM-DD) | 201 y lista de grupos; [] sin datos |

ObtieneToken lleva O mayúscula, igual que la captura solicitada. GET /api/obtieneToken/ y PUT /api/actualizaToken/ se conservan en router/router.py, registrados en rutas_desactivadas. main.py NO incluye ese router: no aparecen en Swagger y no aceptan peticiones. No se eliminó ninguna función de endpoint en este ajuste. router/routerOK.py permanece inactivo.

El POST reutiliza la lógica existente para obtener un token vigente. No lo renueva: si está vencido responde 406. Como actualizaToken está desactivado, la renovación independiente ya no está disponible por HTTP; el cambio de contraseña sigue generando un token nuevo. No se introdujeron renovaciones automáticas.

## Revisión de PUT actualizaContrasena

Se mantiene PUT para establecer una nueva contraseña. La operación actualiza un recurso existente, por lo que devuelve 200 con mensaje, no 201 Created. Referencia: [RFC 9110, PUT](https://www.rfc-editor.org/rfc/rfc9110.html#name-put).

- Recibe las credenciales en JSON, no en la URL.
- Valida la contraseña actual y rechaza la nueva si está vacía o es igual a la anterior.
- Bloquea la fila durante el cambio en MySQL y guarda contraseña, token y expiración en una sola actualización y transacción.
- Invalida el token anterior. Tras cambiar la contraseña, solicitar el token con POST /api/ObtieneToken/ usando la nueva.
- Repetir la petición con la contraseña anterior devuelve 403 y no vuelve a cambiar el token.
- Se conserva el almacenamiento Fernet existente por compatibilidad; esta revisión no migra el formato de contraseñas ni constituye una auditoría completa de seguridad.

Ejemplo del cuerpo (valores ficticios):

```json
{
  "_IdUsuario": "usuario_prueba",
  "_contrasenaActual": "clave_actual",
  "_contrasenaNueva": "clave_nueva"
}
```

Errores: 401 usuario inexistente; 403 contraseña actual incorrecta; 422 cuerpo incompleto, contraseña vacía o nueva igual a la anterior; 500 fallo interno.

## Ejecutar localmente

```powershell
$env:DATABASE_URL = 'mysql+pymysql://USUARIO:CLAVE_CODIFICADA@HOST:3306/vision'
$py = 'C:\AMBIENTES_VIRTUALES_PYTHON\env_api_charly\Scripts\python.exe'
& $py scripts/diagnostico_db.py --fecha 2026-09-09
.\start_api.bat
```

Reemplazar los valores por la conexión real. Codificar caracteres especiales de la contraseña: # puede representarse como %23. La barra invertida antes de @ en la conexión compartida no era parte de la contraseña que funcionó. No se guardaron credenciales en archivos.

El proyecto requiere DATABASE_URL en la terminal o en las variables de ejecución de Coolify. No carga .env automáticamente. En local abre http://127.0.0.1:8000/docs. Coolify usa el puerto interno 8008 según gunicorn_conf.py.

## Probar las rutas desde otra terminal

```powershell
$base = 'http://127.0.0.1:8000'
$cred = Get-Credential -Message 'Cuenta de pruebas API'
$id = $cred.UserName
$password = $cred.GetNetworkCredential().Password
$body = @{_IdUsuario=$id; _contrasena=$password} | ConvertTo-Json
$token = Invoke-RestMethod -Method Post -Uri "$base/api/ObtieneToken/" -ContentType 'application/json' -Body $body

$idUrl = [uri]::EscapeDataString($id)
$tokenUrl = [uri]::EscapeDataString($token)
$fecha = '2026-09-09' # Usar un día confirmado con datos.
Invoke-RestMethod "$base/api/obtieneEventos/?_IdUsuario=$idUrl&_token=$tokenUrl&_fecha=$fecha" | ConvertTo-Json -Depth 5

# Cambia datos: ejecutar solo sobre una cuenta de pruebas.
$nuevaCred = Get-Credential -UserName $id -Message 'Nueva contraseña de prueba'
$nueva = $nuevaCred.GetNetworkCredential().Password
$body = @{_IdUsuario=$id; _contrasenaActual=$password; _contrasenaNueva=$nueva} | ConvertTo-Json
Invoke-RestMethod -Method Put -Uri "$base/api/actualizaContrasena/" -ContentType 'application/json' -Body $body
# Repetir POST ObtieneToken con la contraseña nueva y consultar eventos con el token nuevo.
```

ObtieneToken: usuario inexistente 404, contraseña incorrecta 401, vencimiento 406, falta JSON 422. Eventos: usuario inexistente 401, token incorrecto 402, vencido 406, fecha inválida 405, parámetros faltantes 422. Se conservan los códigos heredados salvo el éxito de cambio de contraseña, ahora 200.

## Pruebas automatizadas

```powershell
& 'C:\AMBIENTES_VIRTUALES_PYTHON\env_api_charly\Scripts\python.exe' -m unittest discover -s tests -v
```

Resultado del ajuste a tres endpoints: 12 pruebas correctas. Incluyen el esquema exacto, bloqueo HTTP de las rutas desactivadas, JSON obligatorio en POST, eventos, persistencia, expiración, contraseña incorrecta, contraseña vacía, repetición de cambio e invalidación del token anterior. actualiza_token se sigue probando como función preservada, sin publicarlo por HTTP. Las pruebas usan SQLite en memoria; no escriben en MySQL remoto.

Para repetir la integración con MySQL real y un servidor HTTP local temporal:

```powershell
# Configurar DATABASE_URL antes de ejecutar.
$cred = Get-Credential -Message 'Cuenta API para integración local'
$env:API_USER = $cred.UserName
$env:API_PASSWORD = $cred.GetNetworkCredential().Password
try {
    & 'C:\AMBIENTES_VIRTUALES_PYTHON\env_api_charly\Scripts\python.exe' scripts/verifica_http_mysql.py
} finally {
    Remove-Item Env:API_USER, Env:API_PASSWORD -ErrorAction SilentlyContinue
}
```

La integración configura MySQL en modo de solo lectura. Obtiene el token por POST, comprueba eventos y prueba PUT con contraseña incorrecta. Usa el día más reciente: nuevas entradas entre conteo SQL y HTTP pueden producir diferencias legítimas. El script fue adaptado al nuevo contrato; las pruebas remotas descritas a continuación corresponden al contrato anterior.

## Evidencia previa del problema desplegado (10 de septiembre de 2026)

Con la misma cuenta y fecha, la API local corregida devolvió 201 para token y eventos. La última comprobación devolvió 367 grupos y 36,247 eventos, igual al conteo MySQL. La base recibe registros nuevos continuamente.

El despliegue en 3.209.38.82:8008 devolvió 201 al obtener token y 500 con Error No identificado!! al consultar eventos. Eso demostró que había datos y credenciales válidas. Se corrigieron ejecución SQL para SQLAlchemy 2, transacciones sin commit y serialización de resultados. MySQL remoto usa NO_ENGINE_SUBSTITUTION; ONLY_FULL_GROUP_BY no era la causa actual.

Los cambios siguen siendo locales; falta desplegarlos y verificar el esquema de tres endpoints en Coolify. No se ejecutaron cambios de contraseña ni renovaciones exitosas en la base remota.
