# setup.ps1 - Instalador automático RASTRILLA
Set-Location $PSScriptRoot
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host ""
Write-Host "  +==========================================+"
Write-Host "  |   Intereses Moratorios - RASTRILLA      |"
Write-Host "  |   Instalador automatico                 |"
Write-Host "  +==========================================+"
Write-Host ""

# ── 1. Verificar / instalar Python ──────────────────────────────────────────
$python = $null

try {
    $python = (Get-Command python -ErrorAction Stop).Source
    $ver = & python --version 2>&1
    Write-Host "  [OK] Python encontrado: $ver"
} catch {
    Write-Host "  Python no encontrado. Descargando instalador..."
    Write-Host "  (puede tardar unos minutos segun tu internet)"
    Write-Host ""

    $installer = "$env:TEMP\python_installer.exe"
    $url = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"

    try {
        Invoke-WebRequest -Uri $url -OutFile $installer -UseBasicParsing
    } catch {
        Write-Host ""
        Write-Host "  ERROR: No se pudo descargar Python."
        Write-Host "  Verificá tu conexion a internet e intentá de nuevo."
        Read-Host "`n  Presiona Enter para salir"
        exit 1
    }

    Write-Host "  Instalando Python para este usuario (no requiere admin)..."
    Start-Process -FilePath $installer `
        -ArgumentList "/quiet", "InstallAllUsers=0", "PrependPath=1", "Include_test=0", "Include_launcher=1" `
        -Wait
    Remove-Item $installer -Force -ErrorAction SilentlyContinue

    # Refrescar PATH en la sesion actual
    $env:PATH = [System.Environment]::GetEnvironmentVariable("Path", "User") `
              + ";" + [System.Environment]::GetEnvironmentVariable("Path", "Machine")

    # Buscar python.exe manualmente si PATH todavia no lo ve
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        $found = Get-ChildItem "$env:LOCALAPPDATA\Programs\Python" -Recurse -Filter "python.exe" -ErrorAction SilentlyContinue |
                 Select-Object -First 1
        if ($found) {
            $env:PATH = $found.DirectoryName + ";" + $env:PATH
        }
    }

    try {
        $python = (Get-Command python -ErrorAction Stop).Source
        $ver = & python --version 2>&1
        Write-Host "  [OK] Python instalado: $ver"
    } catch {
        Write-Host ""
        Write-Host "  ERROR: Python se instalo pero no se pudo detectar."
        Write-Host "  Cerrad esta ventana, abrí una nueva y ejecutá 'ejecutar.bat'."
        Read-Host "`n  Presiona Enter para salir"
        exit 1
    }
}

# ── 2. Instalar dependencias ─────────────────────────────────────────────────
Write-Host ""
Write-Host "  Instalando dependencias de la aplicacion..."

& python -m pip install -r "$PSScriptRoot\requirements.txt" --quiet 2>&1 | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "  ERROR: Fallo la instalacion de dependencias."
    Write-Host "  Verificá tu conexion a internet e intentá de nuevo."
    Read-Host "`n  Presiona Enter para salir"
    exit 1
}

Write-Host "  [OK] Dependencias instaladas."

# ── 3. Lanzar la app ─────────────────────────────────────────────────────────
Write-Host ""
Write-Host "  Abriendo la aplicacion en el navegador..."
Write-Host "  Para cerrar: cerra esta ventana o presiona Ctrl+C"
Write-Host ""

& python -m streamlit run "$PSScriptRoot\app.py" --server.headless false
