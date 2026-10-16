# Encender y apagar la app

Guía rápida para usar Stroke Risk App sólo cuando la necesites (presentaciones, revisiones del profesor) y
apagarla el resto del tiempo. Instalación completa: [`docs/manual_instalacion.md`](docs/manual_instalacion.md).

## Qué pieza hace qué

| Pieza | Dónde | Qué pasa si está apagada |
|---|---|---|
| Página web y Swagger | Firebase Hosting (`https://app-hibrida-511815.web.app` y `/swagger/`) | Siempre disponibles, no se apagan solas |
| API + modelo (contenedores Docker) | VM de Oracle (`https://stroke-salva.duckdns.org`) | La página carga, pero no puede predecir ni mostrar el histórico |
| Base de datos | XAMPP en el PC | La API predice, pero **no guarda** consultas ni muestra el histórico |
| Túnel de MySQL | Ventana de `scripts\tunel_mysql.bat` en el PC | Igual que si XAMPP estuviera apagado |

> Apagar sólo el PC **no** apaga la app: la página y las predicciones siguen funcionando en la nube, sólo que sin
> guardar nada. Para que deje de funcionar del todo hay que detener los contenedores (sección "Apagar").

Para entrar a la VM desde PowerShell (el `ssh` viene con Windows):

```powershell
ssh -i $env:USERPROFILE\.ssh\stroke_admin ubuntu@159.54.154.188
```

## Encender (con tu PC prendida)

1. **XAMPP**: abre el panel y pulsa **Start** en **MySQL**.
2. **Túnel**: en el Explorador de archivos, doble clic en `scripts\tunel_mysql.bat` (no lo abras con el navegador).
   Deja la ventana negra abierta mientras uses la app.
3. **Contenedores** (sólo si los apagaste): entra a la VM y ejecuta
   ```bash
   cd APP_HIBRIDA && docker compose up -d && docker compose ps
   ```
   Espera a que `stroke-inferencia` diga `(healthy)` (unos 20 s).
   Si apagaste la VM entera: primero consola de Oracle → **Compute → Instances → stroke-vm → Start**. Los
   contenedores arrancan solos con ella, salvo que antes los hayas detenido con `docker compose stop`; en ese caso
   ejecuta también el comando de arriba.
4. **Comprobar**:
   - `https://stroke-salva.duckdns.org/api/health` → `{"estado":"ok"}`
   - Abre `https://app-hibrida-511815.web.app`, inicia sesión, haz una consulta y revisa el **Histórico**.

## Apagar

Elige el nivel:

| Quieres… | Haz esto | Cómo volver |
|---|---|---|
| Dejar de guardar datos (pausa corta) | Cierra la ventana del túnel y pulsa **Stop** en MySQL de XAMPP | Pasos 1 y 2 de "Encender" |
| **Que la app deje de funcionar** (recomendado entre sesiones) | Entra a la VM y ejecuta `cd APP_HIBRIDA && docker compose stop`. Luego cierra el túnel y detén MySQL | Pasos 1, 2 y 3 de "Encender" |
| Apagar también la VM | Consola de Oracle → **stroke-vm → Stop** | **Start** en la consola (paso 3) |

Recomendación: usa `docker compose stop` y deja la VM encendida. Apagar la VM no ahorra dinero (es gratis igual) y
al volver a encenderla Oracle a veces responde *"Out of capacity"* para las VM ARM gratuitas, lo que te haría esperar.
La IP pública se conserva al detener y arrancar la VM; sólo se pierde si la **eliminas** (*Terminate*).

Con los contenedores detenidos la página sigue abriendo, pero no puede iniciar consultas.

## ¿Me va a costar algo?

**No, si mantienes la configuración actual.** Ningún servicio usado tiene costo:

| Servicio | Por qué es gratis | Lo único que podría cobrar |
|---|---|---|
| Oracle Cloud | VM `VM.Standard.A1.Flex` de 1 OCPU / 6 GB, disco de arranque, VCN e IP pública entran en *Always Free* (hasta 2 OCPU / 12 GB, 200 GB de disco y 10 TB/mes de salida) | Crear recursos **sin** la etiqueta *Always Free-eligible*: más VM o más grandes, bases de datos, balanceadores de carga, volúmenes fuera de tu región de origen o más de 5 respaldos de volumen |
| Firebase | Plan **Spark**: Hosting (10 GB de almacenamiento, 360 MB/día de descarga) y Authentication con correo y Google | Nada: Spark no tiene tarjeta asociada. Si llegas al límite, el servicio se detiene en vez de cobrar. Sólo cobraría si cambias a plan **Blaze** |
| DuckDNS | Gratuito | — |
| Let's Encrypt (HTTPS) | Gratuito; Caddy renueva el certificado solo mientras los contenedores estén encendidos (si los apagas más de ~2 meses, al encenderlos lo renueva en segundos) | — |
| Google Cloud Shell | Gratuito | — |
| Tu PC | Sólo la luz | — |

Para estar tranquilo:

1. En Oracle, **Billing & Cost Management → Budgets**: deja un presupuesto de **USD 1** con alerta a tu correo.
   La alerta avisa; no detiene el gasto.
2. Revisa **Billing & Cost Management → Cost Analysis** de vez en cuando: debe marcar **0.00**.
3. Si pasaste la cuenta a **Pay As You Go**, Oracle sólo cobra lo que supere *Always Free*. Si no la pasaste,
   no te puede cobrar, pero puede detener la VM si pasa 7 días sin uso (vuelve con **Start**, paso 3).
4. En Firebase no cambies a **Blaze**. En Google Cloud (`console.cloud.google.com/billing`), si en algún momento
   activaste una cuenta de facturación de prueba, comprueba que no tengas máquinas virtuales creadas.

## Al terminar el proyecto (borrar todo)

Si ya no la vas a usar, elimínala para no dejar nada abierto:

1. **Oracle**: **Compute → Instances → stroke-vm → Terminate**, marcando *Permanently delete the attached boot volume*.
   Después, **Networking → Virtual cloud networks →** borra `stroke-vcn` (y `vcn-2026…` si quedó del primer intento).
2. **Firebase**: Configuración del proyecto → **Eliminar proyecto** (borra la página y las cuentas de usuarios).
3. **DuckDNS**: botón **delete domain** de `stroke-salva`.
4. **PC**: borra la carpeta `secrets\` y las llaves `%USERPROFILE%\.ssh\stroke_admin*` y `stroke_tunel*`. En XAMPP puedes
   borrar las bases `consultas_db` y `errores_db` desde phpMyAdmin.
