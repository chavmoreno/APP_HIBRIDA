# Certificados TLS internos

El gateway (:8000) y la inferencia (:8001) **sólo se sirven por HTTPS**, también dentro de la VM.
Los contenedores montan esta carpeta como `/certs` (sólo lectura).

**No hay que generarlos a mano:** `infra/oracle/instalar_vm.sh` los crea en la VM la primera vez con `openssl`
(una CA propia de 10 años y un certificado de servidor de 825 días para `localhost`, `127.0.0.1` y `::1`),
y destruye la llave de la CA. Caddy usa `rootCA.pem` para verificar al gateway (nunca sin verificar).

Archivos (todos ignorados por git — **nunca los subas**):

| Archivo | Uso |
|---|---|
| `localhost.pem` | Certificado del servidor (gateway e inferencia) |
| `localhost-key.pem` | Llave privada: grupo `10001` y permisos `640` para que la lean los contenedores sin hacerla pública |
| `rootCA.pem` | CA interna: el gateway la usa para verificar a la inferencia; el healthcheck de Docker a la inferencia y Caddy al gateway |

Para renovarlos: borra los tres archivos y repite `sudo bash infra/oracle/instalar_vm.sh`, luego `docker compose restart`.
