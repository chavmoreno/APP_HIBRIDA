# Bases de datos (MySQL/MariaDB en XAMPP)

| Script | Qué crea |
|---|---|
| `01_consultas_db.sql` | BD `consultas_db` y tabla `consultas` (entrada + resultado de cada consulta) |
| `02_errores_db.sql` | BD `errores_db` y tabla `errores` (log centralizado) |
| `03_usuarios.sql` | Usuarios `app_consultas`, `app_errores`, `app_errores_admin` con privilegios mínimos |
| `04_usuario_docker.sql` | *(Opcional)* `app_errores` para conexiones desde el contenedor de inferencia. Necesario en Linux; en Docker Desktop sólo si MariaDB rechaza la conexión |

Ejecútalos en orden desde phpMyAdmin (pestaña **SQL**) o con:

```bash
# Windows (XAMPP):  C:\xampp\mysql\bin\mysql.exe -u root -p < 01_consultas_db.sql
mysql -u root -p < 01_consultas_db.sql
mysql -u root -p < 02_errores_db.sql
mysql -u root -p < 03_usuarios.sql   # ¡antes cambia las contraseñas!
```

Seguridad: en `C:\xampp\mysql\bin\my.ini`, sección `[mysqld]`, deja `bind-address=127.0.0.1`
para que MySQL sólo acepte conexiones locales. Pon contraseña al usuario `root`.

Funcionan con el MariaDB que trae XAMPP (10.4 o superior; compruébalo con `SELECT VERSION();`).

El microservicio de inferencia corre en Docker y llega a esta base como `host.docker.internal`.
Ver la sección *Docker y MySQL de XAMPP* en [`docs/manual_instalacion.md`](../docs/manual_instalacion.md).

Diccionario de datos completo: [`docs/arquitectura.md`](../docs/arquitectura.md#modelo-de-datos).
