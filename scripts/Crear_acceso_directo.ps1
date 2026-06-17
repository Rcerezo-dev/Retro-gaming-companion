# Crear_acceso_directo.ps1
# Crea un acceso directo en el Escritorio para lanzar ROM Manager sin abrir terminal.
# Uso: click derecho sobre este archivo → "Ejecutar con PowerShell"

$desktop  = [Environment]::GetFolderPath("Desktop")
$lnk      = "$desktop\ROM Manager.lnk"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
# Este script vive en scripts/; la raíz del proyecto es la carpeta padre.
$projectRoot = Split-Path -Parent $scriptDir

$wsh       = New-Object -ComObject WScript.Shell
$shortcut  = $wsh.CreateShortcut($lnk)
$shortcut.TargetPath      = "cmd.exe"
$shortcut.Arguments       = "/c `"$projectRoot\scripts\rommgr.cmd`""
$shortcut.WorkingDirectory = $projectRoot
$shortcut.WindowStyle     = 7          # 7 = minimized (la ventana CMD no molesta)
$shortcut.Description     = "ROM Manager — Retro Gaming Library"

# Intentar asignar un icono si existe en el proyecto
$iconCandidates = @(
    "$projectRoot\icon.ico",
    "$projectRoot\scripts\icon.ico",
    "$projectRoot\assets\icon.ico"
)
foreach ($ic in $iconCandidates) {
    if (Test-Path $ic) { $shortcut.IconLocation = $ic; break }
}

$shortcut.Save()
Write-Host ""
Write-Host "  Acceso directo creado:" -ForegroundColor Green
Write-Host "  $lnk" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Haz doble clic en 'ROM Manager' en el Escritorio para arrancar la app." -ForegroundColor White
Write-Host "  La interfaz web se abrira en http://127.0.0.1:7777" -ForegroundColor Gray
Write-Host ""
Read-Host "  Pulsa Enter para cerrar"
