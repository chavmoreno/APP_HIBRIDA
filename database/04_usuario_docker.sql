-- =====================================================================
-- Acceso del microservicio de inferencia (contenedor Docker) a errores_db.
--
-- ¿Cuándo hace falta?
--  * Windows / macOS con Docker Desktop: normalmente NO. Docker Desktop reenvía las conexiones a
--    host.docker.internal desde la propia máquina, y el usuario 'app_errores'@'127.0.0.1' de 03_usuarios.sql basta.
--    Ejecútalo sólo si el log del contenedor muestra:
--      Host 'X.X.X.X' is not allowed to connect to this MariaDB server
--    y en ese caso reemplaza '172.%' por la red de esa IP (p. ej. '192.168.65.%').
--  * Linux con Docker Engine: SÍ. El contenedor llega desde la red puente de Docker (172.16.0.0/12).
--    Además, MariaDB debe escuchar en esa interfaz (ver docs/manual_instalacion.md, sección Docker).
--
-- ANTES DE EJECUTAR: usa la MISMA contraseña que app_errores en inference-service/.env.
-- El usuario sólo puede INSERTAR en errores_db.errores (no lee, no borra).
-- =====================================================================

CREATE USER IF NOT EXISTS 'app_errores'@'172.%' IDENTIFIED BY 'cambia-esta-clave';
GRANT INSERT ON errores_db.errores TO 'app_errores'@'172.%';
FLUSH PRIVILEGES;
