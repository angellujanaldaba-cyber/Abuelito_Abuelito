# Base permanente de CI/CD

Terraform separado del laboratorio: crea tres roles IAM OIDC y un bucket S3
privado, cifrado AES256, versionado, con bloqueo de acceso publico y TLS obligatorio.
No crea EKS, RDS, ECR, ALB ni NAT. El proveedor OIDC existente se referencia sin modificarlo.
Los planes privados expiran a los siete dias; el state no tiene expiracion.
El bucket tiene prevent_destroy y force_destroy=false.

Cuenta 455982475279, region us-east-1. Trust OIDC exacto para este repositorio y
cada environment de GitHub, restringido a main por la configuracion de GitHub.
No se otorga AdministratorAccess. La administracion de red necesita IDs generados:
los permisos EC2 limitan acciones de red y region, pero abarcan redes de esa region.
El rol de infraestructura es privilegiado y requiere revision humana del environment.
No puede modificar los roles abuelito-ci-* ni leer el secreto administrador de RDS.

Primera instalacion: init sin backend.tf, plan y aplicar SOLO el plan revisado.
Despues se agrega backend.tf y se migra el state a abuelito/bootstrap/terraform.tfstate.
Para futuras sesiones con backend.tf presente:

```sh
terraform -chdir=deploy/bootstrap init
terraform -chdir=deploy/bootstrap plan
```

Solo un operador con permisos administra esta carpeta. El rol CI de infraestructura
accede exclusivamente al state del laboratorio y sus planes, no al state de bootstrap.
Destruir deploy/terraform no destruye estos roles ni el bucket.

Los permisos fueron validados con IAM Access Analyzer. La conexion OIDC se comprueba
con el workflow manual aws-connection.yml sin crear infraestructura. Un plan futuro
puede revelar permisos adicionales de APIs dependientes: revisar el error y ampliar
solo lo necesario; no sustituir estas politicas por AdministratorAccess.
