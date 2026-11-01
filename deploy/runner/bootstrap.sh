#!/bin/bash
# Sin tokens ni credenciales en user-data. Registro interactivo posterior por SSM.
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
# Limite de vida incluso si no se registra un trabajo o falla la instalacion.
shutdown -h +60
apt-get update
apt-get install -y ca-certificates curl tar gzip unzip python3 gh jq iptables libicu74
useradd --create-home --shell /bin/bash runner
install -d -o runner -g runner /opt/actions-runner
# El usuario del job no puede obtener credenciales del perfil SSM desde IMDS.
iptables -I OUTPUT -m owner --uid-owner runner -d 169.254.169.254 -j REJECT
curl --fail --location --retry 3 https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip -o /tmp/awscli.zip
unzip -q /tmp/awscli.zip -d /tmp
/tmp/aws/install
version=v1.37.0
curl --fail --location --retry 3 "https://dl.k8s.io/release/$version/bin/linux/arm64/kubectl" -o /tmp/kubectl
curl --fail --location --retry 3 "https://dl.k8s.io/release/$version/bin/linux/arm64/kubectl.sha256" -o /tmp/kubectl.sha256
printf '%s  /tmp/kubectl\n' "$(cat /tmp/kubectl.sha256)" | sha256sum --check
install -m 0755 /tmp/kubectl /usr/local/bin/kubectl
curl --fail --location --retry 3 https://github.com/actions/runner/releases/download/v2.338.2/actions-runner-linux-arm64-2.338.2.tar.gz -o /tmp/runner.tar.gz
printf '%s  /tmp/runner.tar.gz\n' '670adb2f268fe21dcbb58b3db0e0aa9d5b3bddfe2c651481336e561ff86de945' | sha256sum --check
tar -xzf /tmp/runner.tar.gz -C /opt/actions-runner
chown -R runner:runner /opt/actions-runner
cat > /etc/systemd/system/abuelito-runner.service <<'UNIT'
[Unit]
Description=Abuelito single-job GitHub runner
After=network-online.target
Wants=network-online.target
[Service]
Type=simple
User=runner
WorkingDirectory=/opt/actions-runner
ExecStartPre=+/usr/sbin/iptables -C OUTPUT -m owner --uid-owner runner -d 169.254.169.254 -j REJECT
ExecStart=/opt/actions-runner/run.sh
# Se elimina la instancia y el disco al terminar; no reutilizar el host del job.
ExecStopPost=+/usr/sbin/shutdown -h now
RuntimeMaxSec=3300
TimeoutStopSec=30
NoNewPrivileges=true
ProtectSystem=full
[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
# No iniciar ni habilitar hasta registrar --ephemeral. Sin Docker ni sudo para runner.
cat > /usr/local/sbin/register-abuelito-runner <<'REGISTER'
${register_script}
REGISTER
chmod 0700 /usr/local/sbin/register-abuelito-runner
touch /var/lib/abuelito-runner-ready
