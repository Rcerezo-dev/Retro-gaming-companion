# Descarga chdman, rclone y adb en tools/
# Uso: .\scripts\download-tools.ps1

$ErrorActionPreference = "Stop"
$toolsDir = "$PSScriptRoot\..\tools"
$tmp = Join-Path ([System.IO.Path]::GetTempPath()) "retrovault_$([System.IO.Path]::GetRandomFileName())"
New-Item -ItemType Directory -Force -Path $tmp | Out-Null

function Get-Tool($label, $url, $dest) {
    Write-Host "[$label] Descargando..." -NoNewline
    Invoke-WebRequest -Uri $url -OutFile $dest -UseBasicParsing
    Write-Host " OK"
}

try {
    # ── rclone ────────────────────────────────────────────────────────────────
    if (Test-Path "$toolsDir\rclone.exe") {
        Write-Host "[rclone] Ya existe, omitido."
    } else {
        $zip = "$tmp\rclone.zip"
        Get-Tool "rclone" "https://downloads.rclone.org/rclone-current-windows-amd64.zip" $zip
        Expand-Archive $zip "$tmp\rclone" -Force
        $exe = Get-ChildItem "$tmp\rclone" -Recurse -Filter "rclone.exe" | Select-Object -First 1
        Copy-Item $exe.FullName "$toolsDir\rclone.exe"
        Write-Host "[rclone] → tools\rclone.exe"
        Write-Host "         Añade 'rclone = ""tools\\rclone.exe""' en [sync] de config.toml si no lo tienes en PATH."
    }

    # ── adb ───────────────────────────────────────────────────────────────────
    if (Test-Path "$toolsDir\adb.exe") {
        Write-Host "[adb] Ya existe, omitido."
    } else {
        $zip = "$tmp\platform-tools.zip"
        Get-Tool "adb" "https://dl.google.com/android/repository/platform-tools-latest-windows.zip" $zip
        Expand-Archive $zip "$tmp\adb" -Force
        Copy-Item "$tmp\adb\platform-tools\adb.exe" "$toolsDir\adb.exe"
        Write-Host "[adb] → tools\adb.exe"
    }

    # ── chdman ────────────────────────────────────────────────────────────────
    if (Test-Path "$toolsDir\chdman.exe") {
        Write-Host "[chdman] Ya existe, omitido."
    } else {
        Write-Host "[chdman] Buscando última versión en GitHub..." -NoNewline
        $release = Invoke-RestMethod "https://api.github.com/repos/mamedev/mame/releases/latest" -UseBasicParsing
        $tag = $release.tag_name   # e.g. "mame0274"
        Write-Host " $tag"

        # Busca un asset zip de tools (si existe release separado de herramientas)
        $asset = $release.assets | Where-Object { $_.name -match "tools" -and $_.name -match "\.zip$" } | Select-Object -First 1

        if ($asset) {
            $zip = "$tmp\mame_tools.zip"
            Get-Tool "chdman" $asset.browser_download_url $zip
            Expand-Archive $zip "$tmp\mame" -Force
            $exe = Get-ChildItem "$tmp\mame" -Recurse -Filter "chdman.exe" | Select-Object -First 1
            if ($exe) {
                Copy-Item $exe.FullName "$toolsDir\chdman.exe"
                Write-Host "[chdman] → tools\chdman.exe"
            }
        } else {
            # MAME solo distribuye instalador .exe (no zip de herramientas sueltas).
            # Intenta extraer con 7-Zip si está disponible.
            $exeAsset = $release.assets | Where-Object { $_.name -match "64bit\.exe$" } | Select-Object -First 1
            $sevenZip = Get-Command "7z" -ErrorAction SilentlyContinue

            if ($exeAsset -and $sevenZip) {
                $installer = "$tmp\mame.exe"
                Get-Tool "chdman" $exeAsset.browser_download_url $installer
                Write-Host "[chdman] Extrayendo con 7-Zip..."
                & 7z e $installer "chdman.exe" -o"$toolsDir" -y | Out-Null
                if (Test-Path "$toolsDir\chdman.exe") {
                    Write-Host "[chdman] → tools\chdman.exe"
                }
            } else {
                Write-Host ""
                Write-Host "[chdman] ⚠ Descarga manual necesaria."
                Write-Host "         1. Ve a: https://www.mamedev.org/tools/"
                Write-Host "         2. Descarga el instalador de MAME tools."
                Write-Host "         3. Extrae chdman.exe y colócalo en tools\"
                Write-Host "         (Solo necesario para convertir ROMs a CHD. Opcional para el resto de funciones.)"
            }
        }
    }

} finally {
    Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "Herramientas en tools\:"
Get-ChildItem $toolsDir -Filter "*.exe" | ForEach-Object { Write-Host "  $($_.Name)" }
