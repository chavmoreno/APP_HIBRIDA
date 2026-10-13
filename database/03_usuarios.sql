-- =====================================================================
-- Usuarios de aplicación con privilegios mínimos (nunca usar root desde la app).
-- ANTES DE EJECUTAR: reemplaza cada 'cambia-esta-clave' por una contraseña fuerte distinta
-- y usa las mismas en los archivos .env de api-gateway e inference-service.
-- Sólo se permiten conexiones desde la propia máquina (127.0.0.1 / localhost).
-- =====================================================================

-- Gateway: guarda y lee consultas
CREATE USER IF NOT EXISTS 'app_consultas'@'127.0.0.1' IDENTIFIED BY 'cambia-esta-clave';
CREATE USER IF NOT EXISTS 'app_consultas'@'localhost' IDENTIFIED BY 'cambia-esta-clave';
GRANT SELECT, INSERT ON consultas_db.consultas TO 'app_consultas'@'127.0.0.1';
GRANT SELECT, INSERT ON consultas_db.consultas TO 'app_consultas'@'localhost';

-- Gateway + inferencia: sólo pueden ESCRIBIR errores (no leerlos ni borrarlos)
CREATE USER IF NOT EXISTS 'app_errores'@'127.0.0.1' IDENTIFIED BY 'cambia-esta-clave';
CREATE USER IF NOT EXISTS 'app_errores'@'localhost' IDENTIFIED BY 'cambia-esta-clave';
GRANT INSERT ON errores_db.errores TO 'app_errores'@'127.0.0.1';
GRANT INSERT ON errores_db.errores TO 'app_errores'@'localhost';

-- Panel admin + worker de alertas: leer errores y marcar 'notificado'
CREATE USER IF NOT EXISTS 'app_errores_admin'@'127.0.0.1' IDENTIFIED BY 'cambia-esta-clave';
CREATE USER IF NOT EXISTS 'app_errores_admin'@'localhost' IDENTIFIED BY 'cambia-esta-clave';
GRANT SELECT, UPDATE (notificado) ON errores_db.errores TO 'app_errores_admin'@'127.0.0.1';
GRANT SELECT, UPDATE (notificado) ON errores_db.errores TO 'app_errores_admin'@'localhost';

FLUSH PRIVILEGES;
