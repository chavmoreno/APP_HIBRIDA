-- =====================================================================
-- errores_db: log centralizado de errores (gateway, inferencia, frontend)
-- Compatible con MariaDB 10.4+ (XAMPP) y MySQL 8.
-- =====================================================================

CREATE DATABASE IF NOT EXISTS errores_db
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE errores_db;

CREATE TABLE IF NOT EXISTS errores (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  request_id    VARCHAR(64)   NULL COMMENT 'Correlaciona con consultas_db.consultas.request_id',
  origen        ENUM('gateway','inferencia','frontend') NOT NULL,
  severidad     ENUM('INFO','WARNING','ERROR','CRITICAL') NOT NULL,
  codigo_http   SMALLINT      NULL,
  tipo          VARCHAR(120)  NULL COMMENT 'Clase de la excepción / error JS',
  mensaje       TEXT          NOT NULL COMMENT 'Mensaje sanitizado (sin tokens ni datos de salud)',
  ruta          VARCHAR(255)  NULL,
  metodo        VARCHAR(10)   NULL,
  firebase_uid  VARCHAR(128)  NULL,
  user_agent    VARCHAR(255)  NULL,
  ip_hash       CHAR(64)      NULL COMMENT 'SHA-256(sal:IP); nunca la IP en claro',
  stack_trace   MEDIUMTEXT    NULL,
  contexto      LONGTEXT      NULL COMMENT 'JSON sanitizado',
  notificado    TINYINT(1)    NOT NULL DEFAULT 0 COMMENT '1 = alerta ya enviada (CRITICAL)',
  creado_en     DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (id),
  KEY idx_fecha (creado_en),
  KEY idx_severidad_notificado (severidad, notificado),  -- Worker de alertas
  KEY idx_origen (origen),
  KEY idx_request_id (request_id),
  CONSTRAINT chk_contexto_json CHECK (contexto IS NULL OR JSON_VALID(contexto))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Log de errores de toda la aplicación';
