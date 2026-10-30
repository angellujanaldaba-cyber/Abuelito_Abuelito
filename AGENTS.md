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
