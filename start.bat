@echo off
setlocal
cd /d "%~dp0"

REM ============================================================
REM  Cinema API - Lanzador para Windows
REM  Doble clic para arrancar la API y abrir la documentacion.
REM  Uso:  start.bat [puerto]      (por defecto 8000)
REM ============================================================

set "PORT=%~1"
if "%PORT%"=="" set "PORT=8000"

echo ============================================
echo    Cinema API  -  Iniciando servidor
echo ============================================
echo.

REM --- 1. Localizar Python -------------------------------------------------
where python >nul 2>nul
if errorlevel 1 (
    where py >nul 2>nul
    if errorlevel 1 (
        echo [ERROR] No se encontro Python.
        echo         Instala Python 3.10+ desde https://www.python.org/downloads/
        echo         y marca la casilla "Add Python to PATH".
        pause
        exit /b 1
    )
    set "PY=py"
) else (
    set "PY=python"
)

REM --- 2. Crear entorno virtual si no existe -------------------------------
if not exist ".venv\Scripts\python.exe" (
    echo [1/3] Creando entorno virtual ^(.venv^)...
    %PY% -m venv .venv
    if errorlevel 1 (
        echo [ERROR] No se pudo crear el entorno virtual.
        pause
        exit /b 1
    )
) else (
    echo [1/3] Entorno virtual ya existente.
)

REM --- 3. Instalar/actualizar dependencias ---------------------------------
echo [2/4] Instalando dependencias...
".venv\Scripts\python.exe" -m pip install --quiet --disable-pip-version-check -r backend\requirements.txt
if errorlevel 1 (
    echo [ERROR] Fallo al instalar las dependencias.
    pause
    exit /b 1
)

REM --- 4. Compilar el frontend (React + Vite) si hace falta ------------------
if exist "frontend\dist\index.html" (
    echo [3/4] Frontend ya compilado ^(frontend\dist^).
) else (
    where npm >nul 2>nul
    if errorlevel 1 (
        echo [3/4] [AVISO] No se encontro Node/npm: el frontend no se compilara.
        echo             Instala Node.js 18+ y ejecuta: cd frontend ^&^& npm install ^&^& npm run build
    ) else (
        echo [3/4] Compilando frontend ^(React + Vite^)...
        pushd frontend
        if not exist "node_modules" call npm install --no-audit --no-fund
        call npm run build
        popd
    )
)

REM --- 5. Abrir la web en el navegador (salvo NO_BROWSER=1) -----------------
if not "%NO_BROWSER%"=="1" (
    start "" powershell -NoProfile -Command "Start-Sleep -Seconds 3; Start-Process 'http://127.0.0.1:%PORT%/'"
)

REM --- 6. Arrancar el servidor (desde la carpeta backend\) -----------------
echo [4/4] Arrancando la API en http://127.0.0.1:%PORT%
echo.
echo     Web (cartelera y entradas):  http://127.0.0.1:%PORT%/
echo     Documentacion (Swagger):     http://127.0.0.1:%PORT%/docs
echo     ReDoc:                       http://127.0.0.1:%PORT%/redoc
echo.
echo     Pulsa CTRL+C en esta ventana para detener el servidor.
echo     Recuerda importar "backend\Cinema-API.postman_collection.json" en Postman.
echo.

cd /d "%~dp0backend"
"..\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port %PORT% --reload

endlocal
