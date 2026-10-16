# Bases de datos (MySQL/MariaDB en XAMPP)

La base de datos es **lo único que corre en el PC de casa**. Los contenedores de la VM de Oracle Cloud llegan a ella
por el túnel SSH inverso que abre el PC (`scripts\tunel_mysql.bat`): para MySQL esas conexiones vienen de `127.0.0.1`,
así que los usuarios locales de `03_usuarios.sql` sirven tal cual y MySQL nunca se expone a la red.

| Script | Qué crea |
|---|---|
| `01_consultas_db.sql` | BD `consultas_db` y tabla `consultas` (entrada + resultado de cada consulta) |
| `02_errores_db.sql` | BD `errores_db` y tabla `errores` (log centralizado) |
| `03_usuarios.sql` | Usuarios `app_consultas`, `app_errores`, `app_errores_admin` con privilegios mínimos |

Ejecútalos en orden desde phpMyAdmin (pestaña **SQL**) o con:

```powershell
Get-Content 01_consultas_db.sql | C:\xampp\mysql\bin\mysql.exe -u root -p
Get-Content 02_errores_db.sql   | C:\xampp\mysql\bin\mysql.exe -u root -p
Get-Content 03_usuarios.sql     | C:\xampp\mysql\bin\mysql.exe -u root -p   # ¡antes cambia las contraseñas!
```

Seguridad: en `C:\xampp\mysql\bin\my.ini`, sección `[mysqld]`, deja `bind-address=127.0.0.1`
(`scripts\configurar_xampp_mysql.ps1` lo corrige si hace falta). Pon contraseña al usuario `root`
(`scripts\restablecer_root_xampp.ps1` la restablece si la olvidaste).

Funcionan con el MariaDB que trae XAMPP (10.4 o superior; compruébalo con `SELECT VERSION();`).

Diccionario de datos completo: [`docs/arquitectura.md`](../docs/arquitectura.md#5-modelo-de-datos).
