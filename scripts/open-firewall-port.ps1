# open-firewall-port.ps1 — Abre el puerto 7777 en el Firewall de Windows
# Ejecutar UNA SOLA VEZ como Administrador:
#   Clic derecho en PowerShell → "Ejecutar como administrador"
#   .\scripts\open-firewall-port.ps1

$ruleName = "Retro Vault (LAN)"
$port = 7777

$existing = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "La regla '$ruleName' ya existe." -ForegroundColor Yellow
} else {
    New-NetFirewallRule `
        -DisplayName $ruleName `
        -Direction Inbound `
        -Action Allow `
        -Protocol TCP `
        -LocalPort $port `
        -Profile Private, Domain `
        -Description "Retro Vault — interfaz web accesible desde la red local (Anbernic, etc.)"
    Write-Host "Regla creada: '$ruleName' → TCP $port (inbound, red privada)" -ForegroundColor Green
}

Write-Host ""
Write-Host "Ahora puedes acceder desde la Anbernic en:" -ForegroundColor Cyan
Write-Host "  http://192.168.1.160:$port/" -ForegroundColor White
