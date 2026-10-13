# Bases de datos (MySQL/MariaDB en XAMPP)

| Script | Qué crea |
|---|---|
| `01_consultas_db.sql` | BD `consultas_db` y tabla `consultas` (entrada + resultado de cada consulta) |
| `02_errores_db.sql` | BD `errores_db` y tabla `errores` (log centralizado) |
| `03_usuarios.sql` | Usuarios `app_consultas`, `app_errores`, `app_errores_admin` con privilegios mínimos |

Ejecútalos en orden desde phpMyAdmin (pestaña **SQL**) o con:

```bash
# Windows (XAMPP):  C:\xampp\mysql\bin\mysql.exe -u root -p < 01_consultas_db.sql
mysql -u root -p < 01_consultas_db.sql
mysql -u root -p < 02_errores_db.sql
mysql -u root -p < 03_usuarios.sql   # ¡antes cambia las contraseñas!
```

Seguridad: en `C:\xampp\mysql\bin\my.ini`, sección `[mysqld]`, deja `bind-address=127.0.0.1`
para que MySQL sólo acepte conexiones locales. Pon contraseña al usuario `root`.

Diccionario de datos completo: [`docs/arquitectura.md`](../docs/arquitectura.md#modelo-de-datos).
