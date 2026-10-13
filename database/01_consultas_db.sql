-- =====================================================================
-- consultas_db: consultas hechas por los usuarios y resultado del modelo
-- Compatible con MariaDB 10.4+ (XAMPP) y MySQL 8.
-- Ejecutar en phpMyAdmin (pestaña SQL) o:  mysql -u root -p < 01_consultas_db.sql
-- =====================================================================

CREATE DATABASE IF NOT EXISTS consultas_db
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE consultas_db;

CREATE TABLE IF NOT EXISTS consultas (
  id                BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  request_id        VARCHAR(64)     NOT NULL COMMENT 'X-Request-ID de la petición (trazabilidad con errores_db)',
  firebase_uid      VARCHAR(128)    NOT NULL COMMENT 'uid de Firebase Auth del dueño de la consulta',

  -- ---- Datos de entrada (mismos nombres que el dataset de Kaggle) ----
  gender            ENUM('Male','Female') NOT NULL,
  age               DECIMAL(5,2)    NOT NULL,
  hypertension      TINYINT(1)      NOT NULL,
  heart_disease     TINYINT(1)      NOT NULL,
  ever_married      ENUM('Yes','No') NOT NULL,
  work_type         ENUM('Private','Self-employed','Govt_job','children','Never_worked') NOT NULL,
  residence_type    ENUM('Urban','Rural') NOT NULL,
  avg_glucose_level DECIMAL(6,2)    NULL COMMENT 'NULL = no informado (el modelo imputa la mediana)',
  bmi               DECIMAL(5,2)    NULL COMMENT 'NULL = no informado (el modelo imputa la mediana)',
  smoking_status    ENUM('formerly smoked','never smoked','smokes','Unknown') NULL COMMENT 'NULL = moda',

  -- ---- Resultado del modelo ----
  probabilidad      DECIMAL(6,5)    NOT NULL COMMENT 'Probabilidad calibrada 0..1',
  clase_predicha    TINYINT(1)      NOT NULL,
  nivel_riesgo      ENUM('bajo','moderado','alto') NOT NULL,
  umbral            DECIMAL(6,5)    NOT NULL,
  modelo_version    VARCHAR(20)     NOT NULL,

  creado_en         DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (id),
  KEY idx_usuario_fecha (firebase_uid, creado_en),  -- Histórico por usuario
  KEY idx_request_id (request_id),
  CONSTRAINT chk_probabilidad CHECK (probabilidad BETWEEN 0 AND 1),
  CONSTRAINT chk_edad CHECK (age BETWEEN 0 AND 120)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Consultas de riesgo de stroke y su resultado';
