# Pipelines de Abuelito (un repositorio)

Aplicacion en la raiz; Terraform en deploy/terraform; Kubernetes en deploy/kubernetes; evidencia historica en deploy/records.
El laboratorio anterior fue destruido el 29 de octubre. El usuario autorizo su recuperacion el 31 de octubre; consultar deploy/records/runner-activation-20261031.json para esa activacion. Preparar workflows y hacer push no recrea AWS por si solo.

## Workflows

| Archivo | Disparador | Comportamiento |
|---|---|---|
| ci.yml | push y pull request | Compila Next.js, valida Terraform y comprueba identificadores de release; no hace llamadas funcionales ni crea pedidos |
| build-images.yml | Manual, desde main | Recibe commit completo, construye runner y migrator ARM64, publica en ECR y guarda release.json con digests y hashes de Prisma |
| infrastructure.yml | Manual, desde main | Genera plan normal o de destruccion y lo guarda privado en S3; apply-plan aplica solo un plan guardado del mismo commit |
| deploy-eks.yml | Manual, desde main | Verifica el run de build, toma sus digests, ejecuta migraciones en Job unico, actualiza Deployment y espera Ready |

El workflow anterior de ECS fue archivado en ecs-workflow-anterior.yml.disabled. Ya no debe estar en .github/workflows.
Las actions estan fijadas por SHA; actualizar deliberadamente y revisar deploy/records/action-pins.json.
No hay despliegue automatico al hacer push. Las pruebas funcionales las realiza el usuario despues del rollout.

## 1. Autenticacion y proteccion en GitHub

Usar OIDC con roles separados (no claves AWS permanentes).
Crear environments dev-build, dev-infrastructure y dev-deploy, restringidos a la rama protegida main. Configurar required reviewers si el plan y la visibilidad del repo lo permiten.
Las condiciones if de YAML NO sustituyen las restricciones del environment y del rol.
El subject de confianza debe ser exacto, por ejemplo para build:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Federated": "arn:aws:iam::455982475279:oidc-provider/token.actions.githubusercontent.com"},
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {"StringEquals": {
      "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
      "token.actions.githubusercontent.com:sub": "repo:angellujanaldaba-cyber/Abuelito_Abuelito:environment:dev-build"
    }}
  }]
}
```

Cambiar el environment para los roles infra y deploy; no usar comodines para todos los repos.
Build necesita ecr:GetAuthorizationToken y uploads/PutImage al repositorio abuelito-eks-web.
Infra necesita permisos de los recursos definidos en Terraform y acceso al backend/planes S3. No se asigno AdministratorAccess automaticamente.
Deploy necesita eks:DescribeCluster, un Access Entry al namespace abuelito y conectividad de red. No necesita leer credenciales RDS del administrador ni publicar imagenes.

## 2. Variables de GitHub (no passwords)

| Environment | Variable | Valor |
|---|---|---|
| dev-build | AWS_BUILD_ROLE_ARN | ARN de rol OIDC de publicacion |
| dev-infrastructure | AWS_INFRA_ROLE_ARN | ARN de rol OIDC de Terraform |
| dev-infrastructure | TF_STATE_BUCKET | Bucket privado existente de state/planes |
| dev-infrastructure | ADMIN_CIDRS_JSON | Lista JSON de IPv4 autorizadas, preferentemente /32 |
| dev-infrastructure | ADMIN_PRINCIPAL_ARN | Usuario/rol IAM administrador real |
| dev-infrastructure | ACM_CERTIFICATE_ARN | Certificado emitido en us-east-1 para dev.miguelinfra.com |
| dev-infrastructure | AWS_DEPLOY_ROLE_ARN | Rol OIDC de deploy que recibira Access Entry limitado |
| dev-deploy | AWS_DEPLOY_ROLE_ARN | Mismo rol de deploy |

Configurados el 31 de octubre de 2026: roles abuelito-ci-build, abuelito-ci-infrastructure y abuelito-ci-deploy; variables de los tres environments; bucket abuelito-eks-tfstate-455982475279-us-east-1. Codigo en deploy/bootstrap. ADMIN_CIDRS_JSON usa la IP observada 177.245.183.167/32: actualizarla si cambia la conexion. Consultar el registro de activacion para el estado del laboratorio y runner; las variables por si solas no prueban su disponibilidad.

El workflow manual aws-connection.yml comprueba OIDC (dev-build) y, para dev-infrastructure, lectura del backend. El segundo requiere la aprobacion humana del environment. No crea recursos.

## 3. Backend Terraform antes del primer plan

Crear un bucket dedicado privado, cifrado y versionado. Activar bloqueo nativo con use_lockfile=true.
El workflow guarda state en abuelito/dev/terraform.tfstate y planes privados en plans/dev/RUN_ID/COMMIT/. Nunca sube planes binarios como artefactos publicos de GitHub.
Configurar ciclo de vida para expirar planes antiguos, conservando la politica necesaria de versiones del state.
Para state/lock: ListBucket y GetObject/PutObject; DeleteObject solo necesario para el lock. Para planes, acceso de escritura/lectura a plans/dev/.

El backend S3 del laboratorio se inicializo vacio tras destruir la instalacion anterior. La recuperacion autorizada del 31 de octubre usa ese mismo backend: ahora debe conservarse su state activo. Nunca aplicar un state vacio sobre el entorno existente ni restaurar encima el state historico del 29 de octubre.

## 4. Crear infraestructura (cuando se autoricen costos)

En Actions, ejecutar Terraform con operation=plan desde main. Revisar el plan en el run.
Luego ejecutar operation=apply-plan, plan_run_id=ID anterior y confirmation=APPLY ID.
Debe seguir siendo el mismo commit de main. Si main cambio, generar otro plan. Terraform tambien rechaza un plan cuyo state quedo obsoleto.
El snapshot final recibe un nombre por ejecucion; no reutilizar el identificador historico abuelito-eks-final-20261029.
No se configura ni modifica Cloudflare automaticamente.

## 5. Build de versiones nuevas

Versionar primero el codigo que se quiere construir. Ejecutar Build con ese SHA completo.
Targets explicitos: runner para web, migrator para Prisma. Etiquetas incluyen commit, numero de ejecucion e intento; el despliegue usa el digest del release, nunca latest.
Conservar release.json fuera de la retencion temporal de Actions como registro duradero de una version aceptada, por ejemplo commit en deploy/records/releases o Release de GitHub.
La imagen validada el 29 de octubre NO queda sustituida por un build nuevo. Sus digests y respaldo local siguen registrados.

## 6. Primer arranque de base y ejecutor de deploy

El workflow deploy presupone namespace abuelito y dos Secrets preconfigurados:

- abuelito-config/DATABASE_URL: usuario de negocio abuelito_app.
- abuelito-migration-config/DATABASE_URL: usuario dedicado que pueda aplicar migraciones en esa base. No reutilizar permanentemente el administrador RDS.

Un operador debe preparar inicialmente esos usuarios, permisos y secretos desde la red privada. Para una base nueva, las migraciones necesitan permisos para crear y modificar la estructura. Para base existente, verificar propiedad de tablas. Configurar privilegios por defecto del propietario de migraciones para las nuevas tablas/secuencias y permisos de negocio del usuario app; no conceder DDL a la aplicacion.
La creacion de esos usuarios no se automatiza con el rol CI ni se copian passwords al repositorio.
Los scripts manuales originales del chat no son el pipeline generico: tienen bootstrap y nombres historicos. No usarlos ciegamente para sucesivas versiones.

Configuracion del runner de un solo uso en deploy/runner/README.md; activacion y maquina concretas en deploy/records/runner-activation-20261031.json. Destruir deploy/runner antes de EKS/VPC para retirar su regla de acceso.

El job deploy necesita runner dedicado Linux ARM64 con labels self-hosted, linux, ARM64, abuelito-dev; herramientas python3, AWS CLI, kubectl y gh; acceso privado a EKS y salida a GitHub.
No abrir el API de EKS a 0.0.0.0/0 para runners compartidos. No ejecutar pull requests no confiables en ese runner.

## 7. Desplegar y volver atras

Despues de un build exitoso, ejecutar Deploy con build_run_id y confirmation=DEPLOY ID. Valida que el run provenga del workflow esperado, de main y haya finalizado correctamente.
Se descarga release.json de ese run, se recupera el commit identificado y se comprueban hashes Prisma.
Si falla el Job de migracion, NO actualiza el Deployment. Migraciones pueden haber quedado parcialmente aplicadas: investigarlas antes de reintentar.
Si falla el rollout, el workflow falla y no declara exito. No revierte la base automaticamente.
Para rollback de aplicacion elegir un release anterior compatible con la estructura actual. No volver a ejecutar migraciones viejas como si deshicieran las nuevas.
El usuario hace las pruebas de catalogo, pedido y consulta; documentar su resultado en el registro de release.

## Destruccion

Terraform: plan-destroy -> revisar -> apply-plan de ese mismo run. Conserva snapshot final. ECR force_delete sigue habilitado: guardar imagenes fuera del repo ECR antes de borrar el laboratorio.
Los pipelines no borran snapshots ni el bucket remoto por su cuenta.

## Recuperar las dos imagenes historicas aceptadas

recover-validated.yml es una ruta manual especifica para abuelito-prueba-001;
no reemplaza build-images.yml ni permite elegir otros digests. Usa
 deploy/records/recovery-release.json, con las dos imagenes exactas y los hashes
del esquema/cinco migraciones comprobados dentro del migrator. La imagen web
historica no tiene un commit de origen demostrado: source_commit permanece null.
deployment_commit identifica el codigo del procedimiento/manifiestos ejecutado
en esta recuperacion; no atribuye la imagen antigua a ese commit.

Un operador vuelve a publicar las mismas imagenes sin reconstruirlas. Luego ejecuta
python3 deploy/scripts/bootstrap_database.py desde la Mac con identidad admin,
contra el DbiResourceId registrado de la base nueva. Este bootstrap exige base
vacia, crea abuelito_app/abuelito_migrator y privilegios por defecto, deja dos
Secrets DATABASE_URL y elimina el secreto temporal de administrador. No crea
pedidos ni aplica migraciones. No reintentar sobre un fallo parcial sin revisar.

Crear y registrar un runner nuevo. En Actions ejecutar Recover historically
validated Abuelito images con confirmation=RECOVER abuelito-prueba-001 y aprobar
 dev-deploy. El Job aplica migraciones con el usuario dedicado, restringe la tabla
_prisma_migrations y solo despues actualiza las dos replicas. La aplicacion usa
el usuario de negocio, sin CREATE en public. Las pruebas funcionales las hace
el usuario; su aprobacion anterior no certifica automaticamente esta base nueva.

El DNS de Cloudflare debe actualizarse manualmente al ALB de la recuperacion,
una vez revisado el despliegue. No se modifica mediante estos workflows.
