# build.ps1 — Retro Vault — PyInstaller build script
# Usage:  .\build.ps1
# Output: dist\RetroVault\RetroVault.exe
#
# Requires PyInstaller in the active Python environment.
# Install with:  pip install pyinstaller

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot

Write-Host "=== Retro Vault — Build ===" -ForegroundColor Cyan

# ── 1. Detect Python ──────────────────────────────────────────────────────────
$CondaEnv = "C:\Users\rammu\anaconda3\envs\rom_manager"
$Python = if (Test-Path "$CondaEnv\python.exe") {
    "$CondaEnv\python.exe"
} else {
    "python"
}
Write-Host "Python: $Python" -ForegroundColor Gray

# ── 2. Ensure PyInstaller is available ────────────────────────────────────────
$PyInstaller = if (Test-Path "$CondaEnv\Scripts\pyinstaller.exe") {
    "$CondaEnv\Scripts\pyinstaller.exe"
} else {
    "pyinstaller"
}

try {
    & $PyInstaller --version | Out-Null
} catch {
    Write-Host "PyInstaller not found. Installing..." -ForegroundColor Yellow
    & $Python -m pip install pyinstaller
}

# ── 3. Clean previous build ───────────────────────────────────────────────────
$DistDir = Join-Path $Root "dist\RetroVault"
if (Test-Path $DistDir) {
    Write-Host "Cleaning previous dist..." -ForegroundColor Gray
    Remove-Item $DistDir -Recurse -Force
}

# ── 4. Run PyInstaller ────────────────────────────────────────────────────────
Write-Host "Running PyInstaller..." -ForegroundColor Cyan
& $PyInstaller "$Root\RetroVault.spec" --noconfirm --clean

if ($LASTEXITCODE -ne 0) {
    Write-Host "PyInstaller failed (exit $LASTEXITCODE)" -ForegroundColor Red
    exit $LASTEXITCODE
}

# ── 5. Copy config.toml template ─────────────────────────────────────────────
$ConfigDest = Join-Path $DistDir "config.toml"
if (-not (Test-Path $ConfigDest)) {
    $ConfigSrc = Join-Path $Root "config.toml.example"
    if (Test-Path $ConfigSrc) {
        Copy-Item $ConfigSrc $ConfigDest
        Write-Host "Copied config.toml.example → dist\RetroVault\config.toml" -ForegroundColor Gray
    }
}

# ── 6. Report ─────────────────────────────────────────────────────────────────
$ExePath = Join-Path $DistDir "RetroVault.exe"
if (Test-Path $ExePath) {
    $Size = [math]::Round((Get-Item $ExePath).Length / 1MB, 1)
    Write-Host ""
    Write-Host "Build OK" -ForegroundColor Green
    Write-Host "  Exe : $ExePath  ($Size MB)" -ForegroundColor Green
    Write-Host "  Dir : $DistDir" -ForegroundColor Green
    Write-Host ""
    Write-Host "To run:" -ForegroundColor Cyan
    Write-Host "  cd dist\RetroVault" -ForegroundColor White
    Write-Host "  .\RetroVault.exe serve --tray" -ForegroundColor White
} else {
    Write-Host "Build completed but RetroVault.exe not found — check PyInstaller output above." -ForegroundColor Red
    exit 1
}
