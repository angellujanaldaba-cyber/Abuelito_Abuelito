# Recrear Abuelito despues de destruir AWS

Usuario autorizo el 29 de octubre guardar imagenes y archivos y despues destruir el laboratorio; el usuario posteriormente pidio conservar el snapshot final de RDS.

## Copias que hay que conservar

- backups/abuelito-recreacion-20261029.tar.gz: copia FINAL recomendada para recrear, con codigo y configuracion actualizados, sin state historico ni planes anteriores. AWS ya fue eliminado y verificado; es correcto iniciar state nuevo desde esta copia.
- backups/abuelito-imagenes-20261029.tar: imagen web y migrator exactas usadas en local y AWS.
- backups/abuelito-archivos-20261029.tar.gz: codigo local y archivos de infraestructura antes de destruir. Incluye state privado de ese momento: no subir a Git ni usar ese state historico para crear recursos nuevos.
- backups/respaldo-20261029.json: hashes e informe de verificacion, cuando termine la exportacion.
- Esta carpeta de trabajo actual, incluyendo el state vacio final y sus registros de destruccion.

Las copias locales no protegen contra perdida de la Mac; conservar otra copia en almacenamiento privado si se desea.

## Recreacion desde esta misma Mac

1. Conservar el workspace ACTUAL despues de destroy. Su state vacio confirma que ya no administra recursos existentes. El state dentro del archivo es historico, no restaurarlo encima sin investigar.
2. Cargar las imagenes si no estan en Docker:

```sh
docker image load --input backups/abuelito-imagenes-20261029.tar
```

3. Confirmar cuenta 455982475279, region us-east-1, IP autorizada actual y existencia del certificado ACM compartido. Comparar IDs con release/aws-images.json. No reconstruir las imagenes para esta recreacion.
4. Revisar db_skip_final_snapshot: actualmente false por decision explicita del usuario: conservar snapshot final. Elegir un db_final_snapshot_identifier nuevo antes de otra recreacion/destruccion, porque abuelito-eks-final-20261029 quedara ocupado.
5. Terraform init, validate y plan NUEVO. No aplicar planes guardados del despliegue ni de la destruccion anterior. Revisar el alcance y costo, luego aplicar con autorizacion correspondiente.
6. Ejecutar scripts/publicar-validada.py: recreado ECR, republica los dos artefactos existentes y verifica sus digests.
7. Ejecutar scripts/desplegar-eks.py: crea conexion privada a la NUEVA base, aplica las cinco migraciones, usuario limitado y dos replicas. La base empieza vacia.
8. Revisar estados Ready y salud ALB, obtener el NUEVO destino DNS y actualizar el CNAME dev de Cloudflare. El certificado ACM compartido no se elimina al destruir este laboratorio.
9. El usuario realiza las pruebas funcionales. Registrar resultado y nuevas direcciones en release/aws-deployment.json.

No se ejecutan pruebas funcionales automaticas ni se recuperan pedidos viejos. EKS, ALB y RDS tendran nuevos IDs/endpoints. CloudWatch puede crear logs fuera de Terraform: revisar esos residuos al eliminar.


Decision final del usuario: conservar el snapshot abuelito-eks-final-20261029. La receta de recreacion anterior crea una base vacia; restaurar el snapshot requiere adaptar Terraform explicitamente y revisar usuario/credenciales y migraciones antes de ejecutar bootstrap. El snapshot tiene cargos de almacenamiento.
