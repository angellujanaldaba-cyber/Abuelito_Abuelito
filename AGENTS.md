# Abuelito: instrucciones de continuidad

- La aplicacion vive en la raiz y la infraestructura EKS en deploy/. Leer docs/deployment/PIPELINES.md y deploy/records/ antes de desplegar.
- AWS del laboratorio anterior fue destruido el 2026-10-29. Snapshot final conservado. No asumir que EKS, ECR o RDS existen.
- La version historica aceptada esta identificada por digest en deploy/records/aws-images.json. No confundirla con futuras imagenes construidas desde Git.
- No subir .env, state, planes Terraform, kubeconfig, respaldos, archivos de evidencia de clientes ni credenciales.
- No reactivar el workflow de ECS archivado. Publicacion/deploy/infra son manuales; push ejecuta solo compilacion y validacion.
- Los targets Docker son runner (web) y migrator (Prisma), ambos ARM64.
- El usuario realiza pruebas funcionales. No crear pedidos ni ejecutar pruebas funcionales automaticas.
- Antes de apply revisar cuenta 455982475279, region us-east-1, plan exacto y autorizacion correspondiente. El trabajo de pipelines no autoriza recrear AWS.
- Siempre registrar commit, ambos digests, hashes de migraciones, destino de base y resultado manual. No inventar evidencia faltante.

- 2026-10-31: bootstrap CI creado en deploy/bootstrap: tres roles abuelito-ci-* y bucket privado abuelito-eks-tfstate-455982475279-us-east-1; state bootstrap remoto separado. Ver deploy/records/ci-bootstrap-20261031.json. OIDC build y CI validados; comprobacion infrastructure requiere revision humana del environment. Runner privado aun no configurado. EKS/RDS siguen destruidos.

- Runner de un solo uso preparado en deploy/runner (Ubuntu ARM64, sin IP/SSH, SSM, --ephemeral, termina instancia al salir o a los 60 min). NO creado: necesita red EKS destruida. No registrar tokens en state/user-data/Git ni SendCommand. Administrar con operador y state separado; retirar runner antes de EKS/VPC. OIDC infrastructure run 41263432028 confirmado success tras aprobacion del usuario.

- ESTADO ACTUAL: el usuario autorizo recuperar el laboratorio y activar el runner el 31 de octubre. Apply: 63 recursos del laboratorio + 8 del runner, state remoto; comprobaciones posteriores sin diferencias. EKS ACTIVE, 2 nodos ARM64 Ready en a/b, RDS 16.15 Multi-AZ disponible, addons ACTIVE. Runner 21 registrado Online/efimero (instancia i-03a37d98e2e8b8074); puede ya haber terminado por trabajo o limite de 60 min: consultar estado real. Registro canonico deploy/records/runner-activation-20261031.json.
- La nueva base no tiene migraciones/usuarios de aplicacion inicializados; imagenes no republicadas y Abuelito NO redesplegado. DNS no cambiado. Snapshot historico conservado. NO confundir el registro historico funcional del 29 de octubre con esta infraestructura nueva. Runner-check 41268962652 espera aprobacion dev-deploy; no autoaprobar.

- Recuperacion de Abuelito autorizada por usuario: imagenes originales republicadas sin reconstruir, hashes Prisma verificados dentro del migrator. Usuarios abuelito_app/abuelito_migrator y Secrets listos en RDS nueva; secreto admin temporal eliminado. Ver database-bootstrap-20261031.json y recovery-release.json. Source commit de imagen historica sigue null; deployment_commit es del procedimiento, no del binario.
- Recover run 41270677490, commit dd6db57da240c03af4989809a27ec21dad4f6607, espera revision humana dev-deploy. Runner22/i-0231b8926a15345f8 registrado Online para este deploy; efimero60min. No autoaprobar. Todavia no migraciones ni rollout; no marcar como desplegado hasta comprobar run. DNS no modificado; pruebas funcionales usuario. Registro aws-recovery-20261031.json.
