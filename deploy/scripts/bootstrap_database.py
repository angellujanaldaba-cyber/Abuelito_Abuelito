#!/usr/bin/env python3
"""Bootstrap de roles/Secrets en RDS nuevo; no migra tablas ni crea pedidos."""
import base64
import json
import os
from pathlib import Path
import secrets
import sys
import subprocess
import time
from urllib.parse import quote, urlsplit

ROOT = Path(__file__).resolve().parents[2]
REF = ROOT / "deploy/records/runner-activation-20261031.json"
KUBECONFIG = ROOT / ".private/runner-activation-kubeconfig"


def aws(*args):
    return json.loads(subprocess.check_output(["aws", *args, "--region", "us-east-1", "--output", "json"]))


def main():
    pipeline = sys.argv[1:] == ["--pipeline"]
    if sys.argv[1:] and not pipeline:
        raise SystemExit("Argumentos invalidos")
    expected = {"identifier": "abuelito-eks-db", "resource_id": os.environ["DB_RESOURCE_ID"]} if pipeline else json.loads(REF.read_text())["database"]
    config = Path(os.environ["KUBECONFIG"]) if pipeline else KUBECONFIG
    output = Path("bootstrap-result.json") if pipeline else ROOT / "deploy/records/database-bootstrap-20261031.json"
    release = json.loads(Path("release.json").read_text()) if pipeline else None
    if pipeline:
        from deploy_release import validate_release
        validate_release(release)
    if aws("sts", "get-caller-identity")["Account"] != "455982475279":
        raise SystemExit("Cuenta inesperada")
    db = aws("rds", "describe-db-instances", "--db-instance-identifier", expected["identifier"])["DBInstances"][0]
    if db["DbiResourceId"] != expected["resource_id"] or db["DBInstanceStatus"] != "available":
        raise SystemExit("RDS no corresponde a la instancia nueva registrada/disponible")
    host = db["Endpoint"]["Address"]
    private = config.parent
    private.mkdir(mode=0o700, exist_ok=True)
    private.chmod(0o700)
    subprocess.run(["aws", "eks", "update-kubeconfig", "--name", "abuelito-eks", "--region", "us-east-1",
                    "--kubeconfig", str(config), "--alias", "abuelito-eks-dev"], check=True, stdout=subprocess.DEVNULL)
    config.chmod(0o600)
    kube = ["kubectl", "--kubeconfig", str(config), "-n", "abuelito"]

    def apply(obj):
        # No imprimir JSON: Secret values solo se transmiten por stdin al API.
        subprocess.run(kube + ["apply", "-f", "-"], input=json.dumps(obj), text=True, check=True)

    def secret(name, values):
        apply({"apiVersion": "v1", "kind": "Secret", "metadata": {"name": name, "namespace": "abuelito"},
               "type": "Opaque", "data": {k: base64.b64encode(v.encode()).decode() for k, v in values.items()}})

    def url(user, password):
        return "postgresql://" + quote(user, safe="") + ":" + quote(password, safe="") + "@" + host + ":5432/abuelito?schema=public&sslmode=require"

    apply({"apiVersion": "v1", "kind": "Namespace", "metadata": {"name": "abuelito"}})
    job_name = "abuelito-roles-" + db["DbiResourceId"].lower().removeprefix("db-")
    old = subprocess.run(kube + ["get", "job", job_name, "-o", "json"], capture_output=True, text=True)
    if old.returncode == 0:
        if not json.loads(old.stdout).get("status", {}).get("succeeded"):
            raise SystemExit("Bootstrap existente sin exito; revisar antes de repetir")
        for name, user in [("abuelito-config", "abuelito_app"), ("abuelito-migration-config", "abuelito_migrator")]:
            value = json.loads(subprocess.check_output(kube + ["get", "secret", name, "-o", "json"]))
            parsed = urlsplit(base64.b64decode(value["data"]["DATABASE_URL"]).decode())
            if parsed.hostname != host or parsed.username != user or parsed.path != "/abuelito":
                raise SystemExit("Secret existente no corresponde a la base/usuario esperado")
        subprocess.run(kube + ["delete", "secret", "abuelito-bootstrap-admin", "--ignore-not-found"], check=True)
        record = {"database_resource_id": db["DbiResourceId"], "endpoint": host, "name": "abuelito",
                  "engine": db["Engine"], "engine_version": db["EngineVersion"], "multi_az": db["MultiAZ"],
                  "instance_created_at": db["InstanceCreateTime"], "bootstrap_job": job_name, "status": "already_initialized_and_verified", "credentials": "Kubernetes Secrets; no passwords in artifact"}
        output.write_text(json.dumps(record, indent=2) + "\n")
        print("Bootstrap ya completado y Secrets verificados.")
        return
    # Si quedaron Secrets sin el Job, no rotar ni sobrescribir por suposicion.
    for name in ("abuelito-config", "abuelito-migration-config", "abuelito-bootstrap-admin"):
        exists = subprocess.run(kube + ["get", "secret", name, "-o", "name"], capture_output=True)
        if exists.returncode == 0:
            raise SystemExit("Existe un Secret sin bootstrap completado: revisar estado antes de continuar")
    admin = json.loads(aws("secretsmanager", "get-secret-value", "--secret-id", db["MasterUserSecret"]["SecretArn"])["SecretString"])
    app_password, migration_password = secrets.token_hex(24), secrets.token_hex(24)
    secret("abuelito-bootstrap-admin", {"DATABASE_URL": url(admin["username"], admin["password"]),
                                        "APP_PASSWORD": app_password, "MIGRATOR_PASSWORD": migration_password})
    js = """
const {PrismaClient}=require('@prisma/client');const db=new PrismaClient();
(async()=>{
 const app=process.env.APP_PASSWORD,mig=process.env.MIGRATOR_PASSWORD;
 if(!/^[a-f0-9]{48}$/.test(app)||!/^[a-f0-9]{48}$/.test(mig))throw Error('password format');
 const tables=await db.$queryRawUnsafe("SELECT tablename FROM pg_tables WHERE schemaname='public'");
 if(tables.length)throw Error('expected empty new database');
 const roles=await db.$queryRawUnsafe("SELECT rolname FROM pg_roles WHERE rolname IN ('abuelito_app','abuelito_migrator')");
 if(roles.length)throw Error('roles already exist');
 await db.$executeRawUnsafe("CREATE ROLE abuelito_migrator LOGIN PASSWORD '"+mig+"'");
 await db.$executeRawUnsafe("CREATE ROLE abuelito_app LOGIN PASSWORD '"+app+"'");
 await db.$executeRawUnsafe('GRANT CONNECT ON DATABASE abuelito TO abuelito_app, abuelito_migrator');
 await db.$executeRawUnsafe('REVOKE CREATE ON SCHEMA public FROM PUBLIC');
 await db.$executeRawUnsafe('GRANT USAGE, CREATE ON SCHEMA public TO abuelito_migrator');
 await db.$executeRawUnsafe('GRANT USAGE ON SCHEMA public TO abuelito_app');
 // RDS permite al administrador hacerse miembro de los roles que acaba de crear.
 await db.$executeRawUnsafe('GRANT abuelito_migrator TO abuelito_admin');
 await db.$executeRawUnsafe('ALTER DEFAULT PRIVILEGES FOR ROLE abuelito_migrator IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO abuelito_app');
 await db.$executeRawUnsafe('ALTER DEFAULT PRIVILEGES FOR ROLE abuelito_migrator IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO abuelito_app');
 await db.$executeRawUnsafe('REVOKE abuelito_migrator FROM abuelito_admin');
 console.log('Roles and default business privileges configured; database remains empty.');
})().catch(()=>{console.error('Database bootstrap failed; inspect role state before retry.');process.exitCode=1}).finally(()=>db.$disconnect());
"""
    image = release["migrator_image"] if pipeline else json.loads((ROOT / "deploy/records/aws-images.json").read_text())["images"]["migrator"]["uri"]
    apply({"apiVersion": "batch/v1", "kind": "Job", "metadata": {"name": job_name, "namespace": "abuelito"},
           "spec": {"backoffLimit": 0, "activeDeadlineSeconds": 300, "template": {"spec": {
               "restartPolicy": "Never", "automountServiceAccountToken": False,
               "nodeSelector": {"kubernetes.io/arch": "arm64"}, "containers": [{
                   "name": "bootstrap", "image": image, "command": ["node", "-e", js],
                   "envFrom": [{"secretRef": {"name": "abuelito-bootstrap-admin"}}],
                   "resources": {"requests": {"cpu": "100m", "memory": "256Mi"}, "limits": {"cpu": "1", "memory": "512Mi"}}}]}}}})
    try:
        for _ in range(75):
            status = json.loads(subprocess.check_output(kube + ["get", "job", job_name, "-o", "json"])).get("status", {})
            if status.get("succeeded"):
                break
            if status.get("failed"):
                raise SystemExit("Bootstrap fallo; no reintentar ni cambiar passwords sin revisar roles")
            time.sleep(5)
        else:
            raise SystemExit("Bootstrap no termino dentro del tiempo esperado")
        secret("abuelito-config", {"DATABASE_URL": url("abuelito_app", app_password)})
        secret("abuelito-migration-config", {"DATABASE_URL": url("abuelito_migrator", migration_password)})
        record = {"database_resource_id": db["DbiResourceId"], "endpoint": host, "name": "abuelito", "bootstrap_job": job_name,
                  "engine": db["Engine"], "engine_version": db["EngineVersion"], "multi_az": db["MultiAZ"],
                  "instance_created_at": db["InstanceCreateTime"], "application_user": "abuelito_app", "migration_user": "abuelito_migrator", "migrations": "pending deployment pipeline",
                  "credentials": "Kubernetes Secrets; no administrator credential retained", "functional_tests": "user only; none performed"}
        output.write_text(json.dumps(record, indent=2) + "\n")
    finally:
        subprocess.run(kube + ["delete", "secret", "abuelito-bootstrap-admin", "--ignore-not-found"], check=True)
    print("Usuarios y Secrets listos; migraciones pendientes del pipeline.")


if __name__ == "__main__":
    main()
