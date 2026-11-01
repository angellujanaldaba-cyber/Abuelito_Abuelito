#!/bin/bash
# Ejecutar como root desde una sesion interactiva SSM, nunca con SendCommand/token.
set -euo pipefail
if [[ $(id -u) != 0 ]]; then echo 'Ejecutar con sudo desde SSM.'; exit 1; fi
if [[ ! -f /var/lib/abuelito-runner-ready ]]; then echo 'Bootstrap no termino; revisar cloud-init.'; exit 1; fi
if [[ -f /opt/actions-runner/.runner ]]; then echo 'Instancia ya registrada; no reutilizar.'; exit 1; fi
read -r -s -p 'Pega el token temporal de registro GitHub (entrada oculta): ' registration_token
printf '\n'
trap 'unset registration_token' EXIT
cd /opt/actions-runner
runuser -u runner -- ./config.sh --unattended --ephemeral \
  --url https://github.com/angellujanaldaba-cyber/Abuelito_Abuelito \
  --token "$registration_token" --name "abuelito-$(cat /proc/sys/kernel/random/uuid)" \
  --labels abuelito-dev --work _work
unset registration_token
systemctl start --no-block abuelito-runner.service
printf 'Runner iniciado para un solo job. La instancia se eliminara al terminar o a los 60 minutos.\n'
