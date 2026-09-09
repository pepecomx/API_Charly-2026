@echo off
setlocal

cd /d "%~dp0"
set "VENV=C:\AMBIENTES_VIRTUALES_PYTHON\env_api_charly\Scripts"
set "PYTHON=%VENV%\python.exe"
set "API_TARGET=%API_TARGET%"
set "API_PORT=%API_PORT%"

if not exist "%PYTHON%" (
    echo ERROR: No se encontro el entorno virtual:
    echo        %PYTHON%
    exit /b 1
)

if "%API_TARGET%"=="" set "API_TARGET=main:app"
if "%API_PORT%"=="" set "API_PORT=8000"

echo Iniciando %API_TARGET% en http://127.0.0.1:%API_PORT%
"%PYTHON%" -m uvicorn "%API_TARGET%" --host 0.0.0.0 --port "%API_PORT%" --reload
exit /b %errorlevel%
