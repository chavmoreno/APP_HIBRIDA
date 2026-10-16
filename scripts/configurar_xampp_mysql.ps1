<#
.SYNOPSIS
    Configura MySQL (MariaDB) de XAMPP para que sólo acepte conexiones locales y diagnostica por qué no arranca.

.DESCRIPTION
    1. Hace una copia de seguridad de my.ini (my.ini.respaldo-AAAAMMDD-HHMMSS).
    2. Quita cualquier línea "bind-address" activa (también las mal escritas, como "bind-adress")
       y las que estén en una sección equivocada.
    3. Escribe una única línea "bind-address=127.0.0.1" justo debajo de [mysqld].
    4. Muestra las últimas líneas de error de mysql_error.log para diagnosticar si MySQL sigue sin arrancar.

    No borra ninguna base de datos ni toca la carpeta data.

.PARAMETER XamppDir
    Carpeta de instalación de XAMPP (por defecto C:\xampp).

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\configurar_xampp_mysql.ps1
#>
param(
    [string]$XamppDir = "C:\xampp"
)

$ErrorActionPreference = "Stop"

# ---- Rutas de XAMPP ----
$ini = Join-Path $XamppDir "mysql\bin\my.ini"
$logError = Join-Path $XamppDir "mysql\data\mysql_error.log"

if (-not (Test-Path $ini)) {
    Write-Host "No se encontró $ini. Si XAMPP está en otra carpeta usa: -XamppDir D:\xampp" -ForegroundColor Red
    exit 1
}

# ---- MySQL debe estar detenido para editar la configuración ----
if (Get-Process -Name "mysqld" -ErrorAction SilentlyContinue) {
    Write-Host "MySQL está corriendo. Pulsa 'Stop' en el panel de XAMPP y vuelve a ejecutar este script." -ForegroundColor Yellow
    exit 1
}

# ---- 1. Copia de seguridad ----
$respaldo = "$ini.respaldo-" + (Get-Date -Format "yyyyMMdd-HHmmss")
Copy-Item $ini $respaldo
Write-Host "Copia de seguridad: $respaldo" -ForegroundColor Green

# ---- 2. Leer y limpiar líneas bind-address existentes ----
$lineas = [System.IO.File]::ReadAllLines($ini)
# Coincide con bind-address / bind_address / bind-adress (errores de escritura comunes), sólo líneas activas (sin #)
$patronBind = '^\s*bind[-_]ad+r?es+\s*='
$quitadas = @($lineas | Where-Object { $_ -match $patronBind })
$limpias = @($lineas | Where-Object { $_ -notmatch $patronBind })
foreach ($l in $quitadas) { Write-Host "Línea eliminada: $l" -ForegroundColor DarkYellow }

# ---- 3. Insertar bind-address debajo de [mysqld] ----
$indice = -1
for ($i = 0; $i -lt $limpias.Count; $i++) {
    if ($limpias[$i] -match '^\s*\[mysqld\]\s*$') { $indice = $i; break }
}
if ($indice -lt 0) {
    Write-Host "No se encontró la sección [mysqld] en my.ini. No se modificó nada (el respaldo queda en $respaldo)." -ForegroundColor Red
    exit 1
}
$nuevas = New-Object System.Collections.Generic.List[string]
for ($i = 0; $i -lt $limpias.Count; $i++) {
    $nuevas.Add($limpias[$i])
    if ($i -eq $indice) { $nuevas.Add("bind-address=127.0.0.1") }  # Sólo conexiones desde esta máquina
}

# Se guarda sin BOM para que MySQL lea el archivo sin problemas
[System.IO.File]::WriteAllLines($ini, $nuevas.ToArray(), (New-Object System.Text.UTF8Encoding $false))
Write-Host "my.ini actualizado: 'bind-address=127.0.0.1' quedó debajo de [mysqld]." -ForegroundColor Green

# ---- 4. Diagnóstico: últimos errores registrados por MySQL ----
if (Test-Path $logError) {
    Write-Host "`nÚltimas líneas de mysql_error.log (por si MySQL sigue sin arrancar):" -ForegroundColor Cyan
    Get-Content $logError -Tail 25 | ForEach-Object {
        if ($_ -match '\[ERROR\]') { Write-Host $_ -ForegroundColor Red } else { Write-Host $_ }
    }
}

Write-Host "`nListo. Ahora pulsa 'Start' en MySQL en el panel de XAMPP." -ForegroundColor Green
Write-Host "Si vuelve a fallar, copia las líneas en rojo de arriba y envíalas." -ForegroundColor Green
Write-Host "Para deshacer el cambio: copia $respaldo sobre $ini" -ForegroundColor DarkGray
