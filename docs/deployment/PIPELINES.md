# Pipelines de Abuelito

Estado del laboratorio: destruido el 31 de octubre; no recreado durante esta
preparacion. La automatizacion nueva del 3 de noviembre esta implementada para
validacion, sin prueba end-to-end en AWS. Ver PIPELINE-COMPLETO.md y
deploy/records/pipeline-automation-20261103.json.

| Funcion | Archivo |
|---|---|
| Validacion al push/PR y reutilizable | .github/workflows/ci.yml |
| Imagenes web/migrator ARM64 del mismo commit | .github/workflows/build-images.yml |
| Plan y aplicacion revisada | .github/workflows/infrastructure.yml |
| Base y aplicacion con CodeBuild privado | .github/workflows/private-execution.yml |
| Retirar workload conservando base IAM/S3 | .github/workflows/destroy-all.yml |
| Coordinador del despliegue completo | .github/workflows/deploy-all.yml |

El coordinador valida, genera plan, espera aprobacion, crea infraestructura,
construye imagenes, prepara PostgreSQL, migra, despliega y opcionalmente cambia
DNS. El usuario realiza las pruebas funcionales. Hacer push solo compila y valida.

La configuracion inicial IAM/S3 y, si se quiere DNS automatico, el Secret de
Cloudflare se establecen una vez antes del primer run. Esta preparacion no los
creo en AWS. La destruccion normal conserva IAM/S3; el retiro total administrativo
del 31 de octubre esta registrado por separado.

El pipeline nuevo sustituye los runners EC2 registrados a mano por ejecuciones
CodeBuild efimeras. Los workflows y la documentacion anteriores permanecen
en docs/deployment/legacy como evidencia historica, fuera de Actions.
Las imagenes y pruebas historicas no cambian ni se atribuyen a un commit falso.
