# Runner privado ARM64, de un solo uso

Estado actual: recursos retirados por solicitud del usuario; ver deploy/records/destruction-20261031.json. La activacion previa esta en deploy/records/runner-activation-20261031.json.
El runner es temporal: un registro Online no garantiza que siga conectado despues
del trabajo o de su limite de vida. Necesita VPC/subred privada/NAT/API privado de
EKS; no usar la VPC default para sustituir esa red.

Esta carpeta usa un state S3 separado: abuelito/runner/terraform.tfstate.
Un operador la administra con su identidad AWS; el rol CI de infraestructura
NO tiene permisos de RunInstances ni de administrar este state.

## Comportamiento

Ubuntu 24.04 ARM64 oficial de Canonical, t4g.small, disco gp3 cifrado de 12 GiB,
sin IP publica, sin SSH ni reglas entrantes. Acceso del operador por SSM.
Salida HTTP/HTTPS por el NAT existente; acceso 443 al security group del API EKS.
El perfil EC2 solo tiene AmazonSSMManagedInstanceCore, sin acceso a RDS ni EKS.
El usuario runner no tiene sudo ni Docker y tiene bloqueado IMDS con iptables.
El job obtiene permisos EKS mediante el rol OIDC dev-deploy, tras aprobacion humana.

El runner se registra --ephemeral, ejecuta un solo job y termina la instancia y
su disco al salir. Se termina tambien a los 60 minutos desde el arranque. Los
logs del workflow quedan en GitHub; los logs locales desaparecen con el disco.
La siguiente ejecucion requiere una instancia nueva. Terraform detectara que la
anterior fue terminada y propondra crearla otra vez. No usar --replace en una
instancia que siga ejecutando un trabajo.

La AMI y el paquete actions/runner estan fijados. Se comprobo el SHA256 publicado
en la release oficial 2.338.2; kubectl 1.37.0 verifica su checksum. AWS CLI v2 se
instala desde su distribucion oficial HTTPS y las otras herramientas desde Ubuntu.
Revisar/actualizar el runner cuando GitHub lo requiera. No se realizaron pruebas
de arranque porque la red aun no existe; terraform validate no prueba cloud-init.

## Crear despues de autorizar y recrear el laboratorio

Desde la raiz, con deploy/terraform inicializado contra su state S3:

```sh
terraform -chdir=deploy/terraform output -json runner_network > deploy/runner/network.auto.tfvars.json
terraform -chdir=deploy/runner init
terraform -chdir=deploy/runner plan -out=runner.tfplan
# Revisar que solo cree runner, IAM/SSM y la regla de API; despues:
terraform -chdir=deploy/runner apply runner.tfplan
```

network.auto.tfvars.json y los planes/state estan ignorados por Git.
Esperar a que la instancia aparezca en Systems Manager > Session Manager.
Abrir una sesion y ejecutar `sudo cloud-init status --wait` antes del registro.
Si falla la preparacion, revisar /var/log/cloud-init-output.log; no registrar.

## Registro automatizado por sesion interactiva

Alternativa al registro manual: desde la Mac con AWS CLI, gh autenticado y
session-manager-plugin instalado, ejecutar desde la raiz:

```sh
python3 deploy/scripts/register_runner.py --instance-id ID_REAL
```

Valida cuenta, etiquetas, ARM64, VPC y ausencia de IP publica. Genera el token
solo cuando aparece el prompt oculto; lo mantiene en memoria y lo envia por
SSM interactivo. No usa SendCommand ni registra el token en sus parametros.
No imprime el token ni lo escribe en disco. Si el plugin esta fuera de PATH,
agregar --plugin-bin DIRECTORIO_DEL_PLUGIN.

El workflow manual runner-check.yml comprueba ARM64, OIDC, DNS/TLS privado de
EKS y permiso de lectura de Deployments. Requiere aprobacion dev-deploy; no
crea pedidos ni despliega la aplicacion. Consume el unico job de la instancia:
al terminar el chequeo, la instancia se elimina. Crear otra para un Deploy real.

## Registrar sin claves permanentes

En la Mac, iniciar sesion gh como propietario del repo y copiar un token temporal:

```sh
gh api --method POST repos/angellujanaldaba-cyber/Abuelito_Abuelito/actions/runners/registration-token --jq .token | pbcopy
```

El token vence en una hora. No pegarlo en el chat, Git, user-data, parametros
Terraform, SendCommand ni archivos de logs. En la sesion interactiva SSM:

```sh
sudo /usr/local/sbin/register-abuelito-runner
```

Pegar en el prompt oculto. Despues borrar el portapapeles en la Mac con `pbcopy < /dev/null`.
No se configura un PAT permanente en AWS. El usuario runner no puede ejecutar este
script root; el operador inicia el servicio una vez registrado.

Confirmar en Settings > Actions > Runners que aparezca Online, Linux, ARM64 y
abuelito-dev. Solo entonces lanzar Deploy manual con el ID de un build valido y
aprobar dev-deploy. No ejecutar pull requests en esta maquina: CI usa runners de
GitHub y deploy solo workflow_dispatch del repositorio original y rama main.
Repositorio publico: revisar cambios de workflows y codigo antes de aprobar;
la aprobacion y --ephemeral no sustituyen esa revision.

Antes del primer Deploy siguen siendo necesarios namespace, usuarios PostgreSQL
y los dos Secrets de conexion descritos en docs/deployment/PIPELINES.md.
No se crearon pedidos ni se ejecutaron pruebas funcionales.

## Retirar

La instancia se elimina automaticamente. Para retirar tambien perfil/rol/SG/regla
API: plan-destroy de deploy/runner, revisar y aplicar ANTES de destruir EKS/VPC.
No eliminar el bucket remoto ni el snapshot historico como parte de esta limpieza.
