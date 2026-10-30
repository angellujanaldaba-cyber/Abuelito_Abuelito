ESTADO ACTUAL (2026-10-29): AWS destruido por solicitud del usuario. 61 recursos eliminados y state sin recursos administrados. Snapshot abuelito-eks-final-20261029 conservado. El despliegue que se describe abajo es historico. Recreacion: RESTAURAR-DESPLIEGUE.md.

# Abuelito: referencia del despliegue AWS

Fecha: 29 de octubre de 2026. Ambiente dev. Usuario confirmo pedidos 1 y 2 mediante acceso temporal a EKS y pedido 3 desde el dominio publico.

## Archivos que se deben conservar

| Archivo o recurso | Para que sirve | Donde conservar |
|---|---|---|
| release/aws-deployment.json | Identidad del despliegue que funciona: imagenes, cluster, base y validacion | Git |
| release/aws-images.json | URI y digest inmutable de web y migrator | Git; los paquetes se conservan en ECR |
| release/aws-inventory.json | Inventario de los 61 recursos, sin valores secretos | Git o repositorio privado de infraestructura |
| local/prueba-001.json | Referencia de la prueba local que dio origen al despliegue | Git |
| Codigo, Dockerfile y package-lock.json | Fuente y dependencias para futuras versiones | Repositorio de aplicacion |
| prisma/schema.prisma y prisma/migrations | Estructura y evolucion de la base | Repositorio de aplicacion |
| terraform/*.tf y .terraform.lock.hcl | Infraestructura y seleccion del proveedor | Repositorio de infraestructura |
| kubernetes/abuelito-aws.yaml | Despliegue exacto por digest y Service | Git |
| terraform/terraform.tfstate | Relacion entre Terraform y los recursos que existen | Privado; migrar a S3 cifrado y con bloqueo |
| .private/kubeconfig, local/.env, tfvars y planes | Acceso y configuracion privada | Fuera de Git; almacenar de forma protegida |
| Secret abuelito-config de EKS | Conexion de la aplicacion a RDS | Gestor de secretos; no copiar su valor a Git |
| Secreto administrador RDS | Credencial administrada y rotada por RDS | AWS Secrets Manager |
| Respaldos y snapshots | Recuperacion de los DATOS | Almacenamiento privado; no Git |

Para otra conversacion compartir release/aws-deployment.json, release/aws-images.json y esta guia. No compartir passwords, state, .env ni kubeconfig.
Un registro JSON identifica artefactos, no contiene la imagen ni los datos.

El codigo local tiene cambios sin commit y no se ha demostrado que un commit concreto produzca la imagen web actual. El artefacto desplegado SI esta identificado por digest y fue validado por el usuario. No inventar un commit para esta version. Antes de nuevas construcciones, versionar el codigo revisado.

## Tecnologias y recursos utilizados

| Capa | Tecnologia y configuracion |
|---|---|
| Aplicacion | Next.js 16.0.3, React 19.2.0, Node.js 20 en Alpine; servidor puerto 3000 |
| Acceso a datos | Prisma 6.19.0, cinco migraciones SQL |
| Empaquetado | Docker, linux/arm64; imagen web y herramienta migrator separadas |
| Infraestructura | Terraform 1.16.0; proveedor AWS 6.70.0 fijado en .terraform.lock.hcl |
| Cuenta / region | 455982475279 / us-east-1 |
| Red | Una VPC 10.42.0.0/16, dos zonas us-east-1a/us-east-1b, dos subredes publicas y dos privadas |
| Salida a internet | Un Internet Gateway; dos NAT Gateway y dos Elastic IP, uno por zona |
| Kubernetes | EKS 1.37; nodos observados 1.37.1; cluster abuelito-eks |
| Capacidad | Dos grupos administrados, un nodo t4g.small On-Demand ARM64 por zona, 20 GiB por nodo |
| Aplicacion en Kubernetes | Namespace abuelito, Deployment de dos replicas repartidas por zona, probes y Service NodePort 30080 |
| Entrada | ALB publico en ambas zonas, target group con nodos registrados mediante sus grupos Auto Scaling |
| Gestion del ALB | Terraform; NO usamos AWS Load Balancer Controller, Ingress ni Helm |
| HTTPS | Certificado ACM existente para *.miguelinfra.com; listener 443 y redireccion 80 a 443 |
| DNS | Cloudflare; CNAME dev a abuelito-eks-1987555837.us-east-1.elb.amazonaws.com, DNS only |
| Registro de imagenes | ECR abuelito-eks-web, etiquetas inmutables y escaneo al publicar |
| Base | RDS PostgreSQL 16.15, instancia db.t4g.micro Multi-AZ con standby, 20 GiB gp3 cifrados |
| Acceso a base | Privado, puerto 5432 permitido desde nodos EKS; usuario de aplicacion abuelito_app con permisos sobre tablas de negocio |
| Respaldo | RDS automatico 7 dias, snapshot final al destroy; el snapshot final permanece fuera del state |
| Credenciales | Administrador en Secrets Manager; DATABASE_URL de aplicacion en Secret Kubernetes |
| IAM | Roles de cluster, nodos y CloudWatch; Access Entry para abuelito-dev; Pod Identity para agente de monitoreo |
| Monitoreo | CloudWatch Observability add-on v7.0.0-eksbuild.1 y Pod Identity Agent v1.4.1-eksbuild.3 |
| Visibilidad | Container Insights, Application Signals segun defaults del add-on, logs de control plane y contenedores, dashboard abuelito-eks |
| Alarmas | ALB sin destinos sanos, errores 5xx y poco espacio RDS; sin correo/SNS configurado |

Los 61 son recursos administrados directamente por Terraform. EKS, Auto Scaling, RDS y CloudWatch crean otros componentes administrados; no es el total de objetos AWS/Kubernetes.
En Multi-AZ clasico de RDS el standby sirve para failover; no es una replica de lectura para la aplicacion.
Monitoreo esta instalado: no se ha validado exhaustivamente cada metrica, log o instrumentacion de Application Signals.

## Version actualmente validada

- Web: 455982475279.dkr.ecr.us-east-1.amazonaws.com/abuelito-eks-web@sha256:6d91eb6c630d2a8f582de6d685f2530bb3d8f5078826d625bd84a7fb04f50ccb
- Migrator: 455982475279.dkr.ecr.us-east-1.amazonaws.com/abuelito-eks-web@sha256:0ffe8e2c0e4688be40076b0556fd6a7f5b0a1bcb4f3476b80221000fc9ddceb2
- RDS: abuelito-eks-db.caxyy48u4z9b.us-east-1.rds.amazonaws.com, base abuelito.
- Dominio: https://dev.miguelinfra.com

## Limites actuales

Estado Terraform aun local; pipeline nuevo aun no conectado. No hay pruebas confirmadas de recuperacion, perdida de zona, failover RDS ni persistencia despues de reinicio.
La aplicacion fue validada en su flujo de pedido; eso no certifica seguridad o funcionalidad de todas sus pantallas.
Costo fijo estimado al desplegar: USD 225/mes mas consumo variable. Para detener cobros planificar destroy; snapshots conservados pueden seguir generando cargos.
