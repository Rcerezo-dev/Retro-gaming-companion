# Descarga chdman, rclone, adb y 7-Zip en tools/
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

    # ── 7-Zip (para extraer .7z en el Inbox) ────────────────────────────────
    if (Test-Path "$toolsDir\7z.exe") {
        Write-Host "[7-Zip] Ya existe, omitido."
    } else {
        Write-Host "[7-Zip] Buscando última versión en GitHub..." -NoNewline
        $release = Invoke-RestMethod "https://api.github.com/repos/ip7z/7zip/releases/latest" -UseBasicParsing
        $tag = $release.tag_name   # e.g. "26.03"
        Write-Host " $tag"

        # El .msi permite extraer sin instalar (instalación administrativa,
        # no interactiva) -- el .exe es un NSIS autoextraíble sin ese modo.
        $asset = $release.assets | Where-Object { $_.name -match "-x64\.msi$" } | Select-Object -First 1

        if ($asset) {
            $msi = "$tmp\7zip.msi"
            Get-Tool "7-Zip" $asset.browser_download_url $msi
            $extractDir = "$tmp\7zip"
            Write-Host "[7-Zip] Extrayendo (instalación administrativa)..."
            Start-Process "msiexec.exe" -ArgumentList "/a `"$msi`" /qn TARGETDIR=`"$extractDir`"" -Wait
            $exe = Get-ChildItem $extractDir -Recurse -Filter "7z.exe" | Select-Object -First 1
            $dll = Get-ChildItem $extractDir -Recurse -Filter "7z.dll" | Select-Object -First 1
            if ($exe -and $dll) {
                Copy-Item $exe.FullName "$toolsDir\7z.exe"
                Copy-Item $dll.FullName "$toolsDir\7z.dll"
                Write-Host "[7-Zip] → tools\7z.exe (+ 7z.dll)"
            } else {
                Write-Host "[7-Zip] ⚠ No se encontró 7z.exe/7z.dll tras extraer el .msi."
            }
        } else {
            Write-Host ""
            Write-Host "[7-Zip] ⚠ Descarga manual necesaria."
            Write-Host "         1. Ve a: https://www.7-zip.org/download.html"
            Write-Host "         2. Instala 7-Zip (o copia 7z.exe + 7z.dll de una instalación existente)."
            Write-Host "         3. Colócalos en tools\"
            Write-Host "         (Solo necesario para extraer archivos .7z en el Inbox. Opcional para el resto de funciones.)"
        }
    }

} finally {
    Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "Herramientas en tools\:"
Get-ChildItem $toolsDir -Filter "*.exe" | ForEach-Object { Write-Host "  $($_.Name)" }
