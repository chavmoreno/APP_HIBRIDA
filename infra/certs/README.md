# Certificados TLS locales

Los servicios locales (gateway :8000 e inferencia :8001) **sólo se sirven por HTTPS**.
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
| `localhost.pem` | Certificado del servidor (gateway, inferencia y `npm run dev`) |
| `localhost-key.pem` | Llave privada del certificado |
| `rootCA.pem` | CA de mkcert: el gateway la usa para verificar a la inferencia; cloudflared, al gateway |
