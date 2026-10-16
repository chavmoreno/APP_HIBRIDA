#!/usr/bin/env bash
# =====================================================================
# Prepara la VM de Oracle Cloud Always Free (Ubuntu 24.04, Ampere A1 / ARM) para Stroke Risk App.
# Se puede repetir sin riesgo.
#
# Uso (dentro de la VM, desde la raíz del repositorio clonado):
#   sudo bash infra/oracle/instalar_vm.sh "ssh-ed25519 AAAA... stroke-tunel" tu-app.duckdns.org tu-correo@gmail.com
#
#   1.er argumento: llave PÚBLICA del PC de casa (%USERPROFILE%\.ssh\stroke_tunel.pub), la que usa
#                   scripts/tunel_mysql.bat para publicar MySQL de XAMPP en 127.0.0.1:3306 de esta VM.
#   2.º argumento:  dominio de DuckDNS que apunta a la IP pública de la VM.
#   3.er argumento: correo para Let's Encrypt (avisos de caducidad del certificado).
#   Al repetir el script (p. ej. tras subir un modelo nuevo) los argumentos son opcionales.
#
# Qué hace:
#   1. Instala Docker + Compose (y swap sólo si la VM tiene menos de 2 GB de RAM).
#   2. Abre los puertos 80/443 en el firewall interno de las imágenes Ubuntu de Oracle (iptables).
#   3. Genera los certificados TLS internos (CA propia) en infra/certs/.
#   4. Mueve a su sitio los archivos subidos a tu carpeta personal: gateway.env, inferencia.env,
#      firebase-service-account.json y model_v*.joblib; escribe DOMINIO/ACME_EMAIL en el .env de la raíz.
#   5. Crea el usuario "tunel", que SÓLO puede abrir el reenvío 127.0.0.1:3306 (sin shell ni terminal).
#   6. Construye y arranca los contenedores (docker compose up -d --build).
# =====================================================================
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive   # apt sin preguntas

[ "$(id -u)" -eq 0 ] || { echo "Ejecútalo con sudo."; exit 1; }
RAIZ="$(cd "$(dirname "$0")/../.." && pwd)"
USUARIO="${SUDO_USER:-root}"
CASA="$(getent passwd "$USUARIO" | cut -d: -f6)"
LLAVE="${1:-}"
DOMINIO="${2:-}"
ACME_EMAIL="${3:-}"
cd "$RAIZ"

# ---- 1. Docker (y swap si hay poca RAM) ----
echo "==> Paquetes"
apt-get update -q
apt-get install -y -q docker.io docker-compose-v2 git openssl
usermod -aG docker "$USUARIO"   # Para usar docker sin sudo (vale desde el siguiente inicio de sesión)

if [ "$(free -m | awk '/^Mem:/{print $2}')" -lt 2000 ] && ! swapon --show | grep -q .; then
  echo "==> Swap de 2 GB"
  fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
  echo "/swapfile none swap sw 0 0" >> /etc/fstab
fi

# ---- 2. Firewall interno: las imágenes Ubuntu de Oracle rechazan todo salvo SSH ----
# (La "Security List" de la VCN también debe permitir 80 y 443: se hace en la consola, ver el manual.)
REGLAS=/etc/iptables/rules.v4
for puerto in 80 443; do
  # Ahora mismo (antes del REJECT final)...
  iptables -C INPUT -p tcp -m state --state NEW --dport "$puerto" -j ACCEPT 2>/dev/null \
    || iptables -I INPUT -p tcp -m state --state NEW --dport "$puerto" -j ACCEPT
  # ...y tras reiniciar: se añade junto a la regla de SSH del archivo de Oracle (sin guardar las reglas de Docker)
  if [ -f "$REGLAS" ] && ! grep -q -- "--dport $puerto -j ACCEPT" "$REGLAS"; then
    sed -i "/--dport 22 -j ACCEPT/a -A INPUT -p tcp -m state --state NEW -m tcp --dport $puerto -j ACCEPT" "$REGLAS"
  fi
done

# ---- 3. Certificados internos (gateway e inferencia sólo sirven HTTPS) ----
CERTS="$RAIZ/infra/certs"
if [ ! -f "$CERTS/localhost.pem" ]; then
  echo "==> Certificados TLS internos"
  CA_KEY="$(mktemp)"   # La llave de la CA no se guarda: si hace falta, se regenera todo
  openssl req -x509 -newkey rsa:3072 -nodes -days 3650 -subj "/CN=Stroke App CA interna" \
    -keyout "$CA_KEY" -out "$CERTS/rootCA.pem"
  openssl req -newkey rsa:2048 -nodes -subj "/CN=localhost" \
    -keyout "$CERTS/localhost-key.pem" -out "$CERTS/localhost.csr"
  openssl x509 -req -in "$CERTS/localhost.csr" -CA "$CERTS/rootCA.pem" -CAkey "$CA_KEY" -CAcreateserial \
    -days 825 -out "$CERTS/localhost.pem" \
    -extfile <(printf "subjectAltName=DNS:localhost,IP:127.0.0.1,IP:::1\nextendedKeyUsage=serverAuth")
  shred -u "$CA_KEY"; rm -f "$CERTS/localhost.csr" "$CERTS/rootCA.srl"
fi
# Los contenedores corren como uid 10001: pueden leer la llave sin hacerla pública
chgrp 10001 "$CERTS/localhost-key.pem" && chmod 640 "$CERTS/localhost-key.pem"

# ---- 4. Archivos subidos a tu carpeta personal (scp desde el PC) ----
mover() {  # mover <origen> <destino> <modo>  (dueño: tu usuario; grupo 10001: lo leen los contenedores)
  if [ -f "$1" ]; then install -m "$3" -o "$USUARIO" -g 10001 "$1" "$2" && rm -f "$1" && echo "    $(basename "$1") → $2"; fi
}
echo "==> Secretos y modelo"
mkdir -p api-gateway/secrets
mover "$CASA/gateway.env" api-gateway/.env 600
mover "$CASA/inferencia.env" inference-service/.env 600
mover "$CASA/firebase-service-account.json" api-gateway/secrets/firebase-service-account.json 640
for m in "$CASA"/model_v*.joblib "$CASA"/model_v*.metadata.json; do mover "$m" "inference-service/models/$(basename "$m")" 644; done
# Dominio de DuckDNS y correo de Let's Encrypt para Caddy (docker compose lee el .env de la raíz)
if [ -n "$DOMINIO" ] && [ -n "$ACME_EMAIL" ]; then
  printf "DOMINIO=%s\nACME_EMAIL=%s\n" "$DOMINIO" "$ACME_EMAIL" > .env
  chown "$USUARIO" .env && chmod 600 .env
fi

# ---- 5. Usuario del túnel de MySQL (sólo reenvío remoto a 127.0.0.1:3306) ----
if [ -n "$LLAVE" ]; then
  case "$LLAVE" in ssh-ed25519\ *) ;; *) echo "La llave debe empezar por ssh-ed25519"; exit 1 ;; esac
  echo "==> Usuario 'tunel'"
  id tunel >/dev/null 2>&1 || useradd --create-home --shell /usr/sbin/nologin tunel
  install -d -m 700 -o tunel -g tunel /home/tunel/.ssh
  echo "restrict,port-forwarding,permitlisten=\"127.0.0.1:3306\" $LLAVE" > /home/tunel/.ssh/authorized_keys
  chown tunel:tunel /home/tunel/.ssh/authorized_keys && chmod 600 /home/tunel/.ssh/authorized_keys
  cat > /etc/ssh/sshd_config.d/50-stroke-tunel.conf <<'EOF'
# Túnel SSH inverso del PC de casa (MySQL de XAMPP → 127.0.0.1:3306 de la VM)
Match User tunel
    AllowTcpForwarding remote
    GatewayPorts no
    X11Forwarding no
    PermitTTY no
    ClientAliveInterval 30
    ClientAliveCountMax 3
Match all
EOF
  sshd -t && systemctl reload ssh
fi

# ---- 6. Contenedores ----
if [ -f api-gateway/.env ] && [ -f inference-service/.env ] && [ -f .env ]; then
  echo "==> docker compose up -d --build (la primera vez tarda unos minutos)"
  docker compose up -d --build
  docker compose ps
else
  echo "Faltan gateway.env/inferencia.env subidos o el dominio y el correo (2.º y 3.er argumento). Repite el script."
fi
echo "Listo."
