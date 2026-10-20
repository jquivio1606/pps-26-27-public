# ============================================================
#  Cinema API - Lanzador para PowerShell
#  Uso:  .\start.ps1 -Port 8000
#        .\start.ps1 -Port 8000 -NoBrowser
#  Si PowerShell bloquea el script, ejecuta antes:
#     Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
# ============================================================
param(
    [int]$Port = 8000,
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "   Cinema API  -  Iniciando servidor"        -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# --- 1. Localizar Python -------------------------------------------------
$py = (Get-Command python -ErrorAction SilentlyContinue) ?? (Get-Command py -ErrorAction SilentlyContinue)
if (-not $py) {
    Write-Host "[ERROR] No se encontro Python. Instala Python 3.10+." -ForegroundColor Red
    exit 1
}

# --- 2. Crear entorno virtual si no existe -------------------------------
$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "[1/3] Creando entorno virtual (.venv)..."
    & $py.Source -m venv .venv
} else {
    Write-Host "[1/3] Entorno virtual ya existente."
}

# --- 3. Instalar/actualizar dependencias ---------------------------------
Write-Host "[2/4] Instalando dependencias..."
& $venvPython -m pip install --quiet --disable-pip-version-check -r backend\requirements.txt

# --- 4. Compilar el frontend (React + Vite) si hace falta -----------------
$distIndex = Join-Path $PSScriptRoot "frontend\dist\index.html"
if (Test-Path $distIndex) {
    Write-Host "[3/4] Frontend ya compilado (frontend\dist)."
} else {
    $npm = Get-Command npm -ErrorAction SilentlyContinue
    if ($npm) {
        Write-Host "[3/4] Compilando frontend (React + Vite)..."
        Push-Location (Join-Path $PSScriptRoot "frontend")
        if (-not (Test-Path "node_modules")) {
            & npm install --no-audit --no-fund
        }
        & npm run build
        Pop-Location
    } else {
        Write-Host "[3/4] [AVISO] No se encontro Node/npm: el frontend no se compilara." -ForegroundColor Yellow
        Write-Host "            Instala Node.js 18+ y ejecuta: cd frontend; npm install; npm run build"
    }
}

# --- 5. Abrir la web en el navegador -------------------------------------
if (-not $NoBrowser) {
    Start-Job -ScriptBlock {
        param($url)
        Start-Sleep -Seconds 3
        Start-Process $url
    } -ArgumentList "http://127.0.0.1:$Port/" | Out-Null
}

# --- 6. Arrancar el servidor (desde la carpeta backend\) -----------------
Write-Host "[4/4] Arrancando la API en http://127.0.0.1:$Port" -ForegroundColor Green
Write-Host "     Web:     http://127.0.0.1:$Port/"
Write-Host "     Swagger: http://127.0.0.1:$Port/docs"
Write-Host "     Pulsa CTRL+C para detener el servidor."
Set-Location -Path (Join-Path $PSScriptRoot "backend")
& $venvPython -m uvicorn app.main:app --host 127.0.0.1 --port $Port --reload
