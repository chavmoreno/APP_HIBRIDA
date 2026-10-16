<#
.SYNOPSIS
    Restablece la contraseña de root de MySQL (MariaDB) de XAMPP sin conocer la anterior.

.DESCRIPTION
    1. Pide la contraseña nueva dos veces (no se muestra en pantalla ni queda en el historial).
    2. Arranca un MySQL temporal con --skip-grant-tables escuchando SOLO en 127.0.0.1.
    3. Pone la misma contraseña a root@localhost, root@127.0.0.1 y root@::1 y apaga el servidor temporal.

    No borra ninguna base de datos. Antes de ejecutarlo pulsa "Stop" en MySQL en el panel de XAMPP.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\restablecer_root_xampp.ps1
#>
param(
    [string]$XamppDir = "C:\xampp"
)

$ErrorActionPreference = "Stop"
$mysqld = Join-Path $XamppDir "mysql\bin\mysqld.exe"
$mysql = Join-Path $XamppDir "mysql\bin\mysql.exe"
$ini = Join-Path $XamppDir "mysql\bin\my.ini"

# ---- MySQL debe estar detenido (el temporal usa el mismo puerto y los mismos datos) ----
if (Get-Process -Name "mysqld" -ErrorAction SilentlyContinue) {
    Write-Host "MySQL está corriendo. Pulsa 'Stop' en el panel de XAMPP y vuelve a ejecutar este script." -ForegroundColor Yellow
    exit 1
}

# ---- 1. Contraseña nueva (oculta) ----
function Leer-Clave([string]$texto) {
    $segura = Read-Host $texto -AsSecureString
    return [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($segura))
}
$clave = Leer-Clave "Contraseña nueva para root"
if ($clave.Length -lt 8) { Write-Host "Usa al menos 8 caracteres." -ForegroundColor Red; exit 1 }
if ($clave -ne (Leer-Clave "Repítela")) { Write-Host "Las contraseñas no coinciden." -ForegroundColor Red; exit 1 }
# Escapa \ y ' para meterla en un literal SQL
$claveSql = $clave.Replace('\', '\\').Replace("'", "\'")

# ---- 2. MySQL temporal sin permisos, sólo en loopback ----
$log = Join-Path $env:TEMP "mysqld_restablecer_root.log"
Remove-Item $log -ErrorAction SilentlyContinue
$proc = Start-Process $mysqld -PassThru -WindowStyle Hidden -RedirectStandardError $log `
    -ArgumentList "--defaults-file=$ini", "--skip-grant-tables", "--bind-address=127.0.0.1", "--console"
$listo = $false
for ($i = 0; $i -lt 30 -and -not $listo; $i++) {
    Start-Sleep 1
    $listo = (Test-Path $log) -and (Select-String -Path $log -Pattern "ready for connections" -Quiet)
}
if (-not $listo) {
    Stop-Process -Id $proc.Id -ErrorAction SilentlyContinue
    Write-Host "El MySQL temporal no arrancó. Revisa $log" -ForegroundColor Red
    exit 1
}

# ---- 3. Cambiar la contraseña en las tres cuentas root y apagar (por stdin: no queda en la línea de comandos) ----
@"
FLUSH PRIVILEGES;
ALTER USER IF EXISTS 'root'@'localhost' IDENTIFIED BY '$claveSql';
ALTER USER IF EXISTS 'root'@'127.0.0.1' IDENTIFIED BY '$claveSql';
ALTER USER IF EXISTS 'root'@'::1' IDENTIFIED BY '$claveSql';
FLUSH PRIVILEGES;
SHUTDOWN;
"@ | & $mysql -u root -h 127.0.0.1
$proc.WaitForExit(30000) | Out-Null

Write-Host "`nListo. Pulsa 'Start' en MySQL en el panel de XAMPP y entra con la contraseña nueva." -ForegroundColor Green
