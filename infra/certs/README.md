# Certificados TLS locales

Los servicios locales (gateway :8000 e inferencia :8001) **sólo se sirven por HTTPS**.
El gateway los lee desde esta carpeta; el contenedor de inferencia la monta como `/certs` (sólo lectura).
Genera aquí los certificados con [mkcert](https://github.com/FiloSottile/mkcert):

```bash
# Windows:  choco install mkcert   |  macOS: brew install mkcert  |  Linux: ver repositorio de mkcert
mkcert -install                                  # Crea y confía en una CA local
cd infra/certs
mkcert -cert-file localhost.pem -key-file localhost-key.pem localhost 127.0.0.1 ::1
# Copia la CA raíz para que el gateway y cloudflared verifiquen el certificado:
#   Windows (PowerShell):  Copy-Item "$(mkcert -CAROOT)\rootCA.pem" .
#   macOS/Linux:           cp "$(mkcert -CAROOT)/rootCA.pem" .
```

Archivos esperados (todos ignorados por git — **nunca los subas**):

| Archivo | Uso |
|---|---|
| `localhost.pem` | Certificado del servidor (gateway, inferencia en Docker y `npm run dev`) |
| `localhost-key.pem` | Llave privada del certificado |
| `rootCA.pem` | CA de mkcert: el gateway la usa para verificar a la inferencia; cloudflared, al gateway |

## Permisos para Docker en Linux

En Windows y macOS (Docker Desktop) no hay que hacer nada. En **Linux**, mkcert crea la llave con
permisos `0600` y el contenedor (que corre como el usuario sin privilegios `uid 10001`) no puede leerla.
Dale acceso sólo a ese grupo, sin hacerla pública:

```bash
sudo chgrp 10001 localhost-key.pem
chmod 640 localhost-key.pem
```

Si lo olvidas, el contenedor termina con el mensaje `Sin permiso de lectura sobre '/certs/localhost-key.pem'`.
