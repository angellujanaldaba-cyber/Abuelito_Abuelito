# Pipeline completo propuesto el 3 de noviembre de 2026

Estado: implementado para validacion; NO ejecutado de punta a punta contra AWS.
El laboratorio permanece destruido. No confundir sintaxis/tests/CI correctos con
una prueba real de creacion, migracion, despliegue y destruccion.

## Como se usa despues de la configuracion inicial

En Actions abrir Deploy complete Abuelito environment, rama main, escribir
DEPLOY dev y ejecutar. El flujo llama a workflows reutilizables:

1. CI: compila Next.js, valida Terraform y ejecuta controles de identidad y limites.
2. Plan: usa un rol de lectura y guarda el plan binario privado en S3. El texto
   revisable aparece en el run; el binario no se sube a artefactos publicos.
3. Apply: espera revision dev-infrastructure y aplica exactamente el plan de ese
   commit/run/tipo/hash. Terraform rechaza planes con state obsoleto.
4. Imagenes: construye runner/web y migrator ARM64 del mismo commit, publica
   digests inmutables en ECR y adjunta release.json.
5. PostgreSQL: espera dev-infrastructure y ejecuta un proyecto CodeBuild privado
   con acceso administrador limitado a esta RDS/EKS. Crea namespace, usuarios y
   Secrets; elimina el Secret administrador temporal. No requiere la Mac.
6. Aplicacion: espera dev-deploy y ejecuta OTRO proyecto CodeBuild, sin lectura
   del secreto administrador y con acceso Kubernetes limitado a abuelito. Aplica
   migraciones como abuelito_migrator, restringe _prisma_migrations, despliega dos
   replicas y espera Ready y dos destinos ALB sanos.
7. DNS opcional: espera dev-dns y actualiza solo dev.miguelinfra.com al ALB de ese
   resultado sano, mismo commit y run. Conserva DNS only. Las pruebas de pedidos
   siguen siendo del usuario: no creamos pedidos ni declaramos aceptacion automatica.

Esto elimina la creacion/registro manual de runners. CodeBuild ejecuta contenedores
ARM64 temporales en las subredes privadas; la infraestructura define sus proyectos,
roles, grupos de logs y acceso de red. No usa un PAT GitHub ni una EC2 persistente
para ejecutar los trabajos. El compute de cada build se inicia/retira por AWS.
Los proyectos, roles y logs si permanecen hasta destruir el workload.

## Preparacion inicial que no puede autenticar magicamente desde cero

El 31 de octubre se borraron tambien IAM/S3. Antes del primer run es necesario
recrear deploy/bootstrap con una identidad administradora existente, revisando
su plan. Esa fase establece confianza GitHub-AWS y el bucket que usara Terraform;
no se ha aplicado en este trabajo. Nunca restaurar el state historico activo.
Ver deploy/bootstrap/README.md. Ahora crea cuatro roles OIDC separados:

| Environment | Rol | Revision humana |
|---|---|---|
| dev-plan | abuelito-ci-plan | Sin mutaciones de infraestructura; escribe planes/lock, no state |
| dev-infrastructure | abuelito-ci-infrastructure | Apply y bootstrap de base requieren aprobacion |
| dev-build | abuelito-ci-build | Solo ECR de Abuelito |
| dev-deploy | abuelito-ci-deploy | Inicia solo el proyecto privado de deploy |
| dev-dns | Sin rol AWS | Token Cloudflare, aprobacion antes de cambiar DNS |

En la Mac se ejecuta una vez configure_pipeline_github.py para environments y
variables, autenticado con gh como propietario. Ejemplo desde la raiz:

```sh
python3 deploy/scripts/configure_pipeline_github.py --admin-cidr TU_IP_PUBLICA/32
```

Esto NO crea AWS. La IP debe actualizarse cuando cambie. Los environments se
restringen a main y conservan revisores existentes; los nuevos de escritura usan
al propietario como revisor. No autoaprobar ejecuciones desde scripts del agente.

Para DNS automatico: crear un token Cloudflare limitado a Zone/DNS/Edit solo de
miguelinfra.com. Guardarlo una vez en el Secret CLOUDFLARE_API_TOKEN de dev-dns,
no en el chat ni en archivos. Configurar CLOUDFLARE_ZONE_ID en ese environment,
o ejecutar el helper con --zone-id ID. Volver a ejecutar el helper despues de
guardar el Secret: comprueba su nombre, nunca lee su valor, y marca
DNS_AUTOMATION_READY. La validez/permisos del token se comprueban al usarlo.

publish_dns=true es el predeterminado. Si no se configura DNS, el coordinador
falla antes de crear infraestructura; se puede desmarcar para validar AWS solamente.
Eso no debe presentarse como una publicacion completa del dominio.

## Destruccion normal por pipeline

Abrir Destroy Abuelito workload (preserve CI foundation), escribir DESTROY dev.
Se genera plan-destroy, se espera aprobacion y se aplica solo ese plan. RDS conserva
snapshot final. Se eliminan workload y proyectos CodeBuild; el log performance
que puede crear el addon tambien se limpia. DNS se elimina solo si aun coincide
con el ALB capturado antes de destruir: no borra un destino cambiado por alguien.

La base bootstrap IAM/S3 se CONSERVA deliberadamente para autenticar el siguiente
run y conservar el state. Tiene almacenamiento facturable; no es borrado total
de la cuenta. Si se quiere retirar tambien esa base, se necesita el procedimiento
administrativo separado de archivo de states y retiro de bucket/roles, como el
realizado el 31 de octubre. No prometer despliegue desde cero sin esa confianza inicial.

ECR sigue force_delete=true: el destroy normal borra sus imagenes. El codigo y
release.json quedan en GitHub/artefactos temporales, pero el binario no sobrevive
por existir su digest. Antes de destruir una version irreproducible conservarla
en respaldo externo. La pareja historica ya tiene su archivo Docker privado.
Los nuevos builds se pueden reconstruir del commit, aunque dependencias/base
actualizables pueden producir otro digest. No prometer binarios identicos sin
reproducibilidad de todas las entradas.

## Identidad, permisos y fallos

Los bundles incluyen solo git archive del commit limpio, el release y el ID del
run. S3 es privado/cifrado/versionado; CodeBuild verifica SHA256 antes de extraer,
rechaza rutas escapadas/enlaces y luego ejecuta el codigo. Resultados se guardan
privados en S3 y se descargan como JSON sin passwords. Bundles/resultados expiran
a los 30 dias; los planes a los 7; el state no tiene expiracion.

Los roles de CodeBuild llevan un permissions boundary creado en bootstrap. El rol
de infraestructura no puede quitarlo ni modificarlo; no puede usar una politica
inline de esos roles para concederse permisos IAM ilimitados. El secreto admin
queda limitado por ARN de la instancia en su etiqueta de sistema RDS.

El rol de plan no puede aplicar ni escribir el state. El rol GitHub de deploy no
lee credenciales RDS ni inicia el proyecto de bootstrap. El ejecutor de bootstrap
si tiene privilegios elevados para preparar la base: tratar su aprobacion y el
codigo del commit con esa responsabilidad. Los builds se limitan a 30 minutos;
si el job se cancela, el helper intenta detenerlos. Una cancelacion de red/proceso
puede dejar la ejecucion hasta su timeout: comprobar el build antes de reintentar.

Bootstrap soporta una RDS nueva/vacia y repeticiones con Job completado y Secrets
coincidentes. No admite automaticamente una restauracion de snapshot sin esos
usuarios/Secrets ni repara un bootstrap parcial. Se detiene para revisar el caso,
sin rotar credenciales por suposicion. Migraciones fallidas no actualizan la app;
rollout fallido no declara exito y no revierte cambios SQL automaticamente.

Los workflows historicos de runners EC2 se guardan en docs/deployment/legacy/.
Sus runs exitosos siguen siendo evidencia del 31 de octubre, no del flujo nuevo.
Los archivos deploy/runner se conservan como referencia, no son usados por el
coordinador nuevo. Las imagenes historicas y pruebas de aceptacion no se cambian.

## Referencias de diseno

- [CodeBuild sin repositorio conectado](https://docs.aws.amazon.com/codebuild/latest/userguide/no-source.html)
- [Acceso de CodeBuild a una VPC](https://docs.aws.amazon.com/codebuild/latest/userguide/enabling-vpc-access-in-projects.html)
- [Permisos para interfaces de red](https://docs.aws.amazon.com/codebuild/latest/userguide/auth-and-access-control-iam-identity-based-access-control.html)
- [Workflows reutilizables de GitHub](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows)
