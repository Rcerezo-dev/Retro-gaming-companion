# build.ps1 — Retro Vault — PyInstaller build script
# Usage:  .\build.ps1
# Output: dist\RetroVault\RetroVault.exe
#
# Requires PyInstaller in the active Python environment.
# Install with:  pip install pyinstaller

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot

Write-Host "=== Retro Vault — Build ===" -ForegroundColor Cyan

# ── 1. Detect the rom_manager Python environment ──────────────────────────────
# No hardcoded username/path: discover the conda env dynamically so the build
# works on any machine. If it can't be found we warn loudly instead of silently
# falling back to a bare `python`, which would mask a missing/incomplete env.
$EnvName = "rom_manager"

function Find-CondaEnv {
    param([string]$Name)

    # 1) An already-activated conda env wins (respects `conda activate`).
    if ($env:CONDA_PREFIX -and (Test-Path (Join-Path $env:CONDA_PREFIX "python.exe"))) {
        return $env:CONDA_PREFIX
    }

    # 2) Common conda roots for the current user — derived from the environment,
    #    never a literal username.
    $roots = @(
        (Join-Path $env:USERPROFILE "anaconda3"),
        (Join-Path $env:USERPROFILE "miniconda3"),
        (Join-Path $env:USERPROFILE "miniforge3"),
        (Join-Path $env:LOCALAPPDATA "anaconda3"),
        (Join-Path $env:LOCALAPPDATA "miniconda3"),
        "C:\ProgramData\anaconda3",
        "C:\ProgramData\miniconda3"
    )
    foreach ($r in $roots) {
        $candidate = Join-Path $r "envs\$Name"
        if (Test-Path (Join-Path $candidate "python.exe")) {
            return $candidate
        }
    }

    # 3) Ask conda itself, if it's on PATH.
    if (Get-Command conda -ErrorAction SilentlyContinue) {
        try {
            $prefix = (& conda run -n $Name python -c "import sys; print(sys.prefix)" 2>$null |
                Select-Object -Last 1)
            if ($prefix -and (Test-Path (Join-Path $prefix "python.exe"))) {
                return $prefix
            }
        } catch { }
    }

    return $null
}

$CondaEnv = Find-CondaEnv -Name $EnvName
if ($CondaEnv) {
    $Python = Join-Path $CondaEnv "python.exe"
    Write-Host "Python env: $CondaEnv" -ForegroundColor Gray
} else {
    $Python = "python"
    Write-Host "WARNING: conda env '$EnvName' not found." -ForegroundColor Yellow
    Write-Host "         Falling back to bare 'python' on PATH — the build will use" -ForegroundColor Yellow
    Write-Host "         whatever that resolves to; verify it has the dependencies." -ForegroundColor Yellow
}

# ── 2. Ensure PyInstaller is available ────────────────────────────────────────
$PyInstaller = if ($CondaEnv -and (Test-Path (Join-Path $CondaEnv "Scripts\pyinstaller.exe"))) {
    Join-Path $CondaEnv "Scripts\pyinstaller.exe"
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
