#!/usr/bin/env python3
"""Despliega digests de release; solo verifica estado, no crea pedidos."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

REPOSITORY = "455982475279.dkr.ecr.us-east-1.amazonaws.com/abuelito-eks-web"

def validate_release(release):
    if release.get("release_type") == "historical-recovery":
        raise ValueError("La imagen historica requiere su workflow de recuperacion explicito")
    if not re.fullmatch(r"[a-f0-9]{40}", release.get("source_commit", "")):
        raise ValueError("Commit de release invalido")
    if release.get("architecture") != "linux/arm64":
        raise ValueError("Release debe ser ARM64")
    for name in ("web_image", "migrator_image"):
        if not re.fullmatch(re.escape(REPOSITORY) + r"@sha256:[a-f0-9]{64}", release.get(name, "")):
            raise ValueError("Digest ECR invalido: " + name)
    if not release.get("prisma_files_sha256"):
        raise ValueError("Falta identificar esquema y migraciones")
    return release

def validate_historical_release(release):
    """Ruta explicita de recuperacion; nunca atribuir el binario antiguo a un commit nuevo."""
    if (release.get("release_type") != "historical-recovery"
            or release.get("source_test") != "abuelito-prueba-001"
            or release.get("source_commit") is not None
            or not re.fullmatch(r"[a-f0-9]{40}", release.get("deployment_commit", ""))):
        raise ValueError("Identidad historica invalida")
    expected = {
        "web_image": REPOSITORY + "@sha256:6d91eb6c630d2a8f582de6d685f2530bb3d8f5078826d625bd84a7fb04f50ccb",
        "migrator_image": REPOSITORY + "@sha256:0ffe8e2c0e4688be40076b0556fd6a7f5b0a1bcb4f3476b80221000fc9ddceb2",
    }
    if any(release.get(k) != v for k, v in expected.items()):
        raise ValueError("Esta recuperacion solo admite los dos digests historicos validados")
    if release.get("architecture") != "linux/arm64" or not release.get("prisma_files_sha256"):
        raise ValueError("Arquitectura/migraciones historicas invalidas")
    return release

def main():
    raw = json.loads(Path("release.json").read_text())
    if sys.argv[1:] == ["--historical-recovery"]:
        release = validate_historical_release(raw)
    elif sys.argv[1:]:
        raise SystemExit("Argumentos no reconocidos")
    else:
        release = validate_release(raw)
    import hashlib
    for name, expected in release["prisma_files_sha256"].items():
        path = Path(name)
        if path.is_absolute() or ".." in path.parts or path.parts[0] != "prisma":
            raise SystemExit("Ruta Prisma invalida")
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise SystemExit("El codigo no coincide con las migraciones del build")
    identity = subprocess.check_output(["aws", "sts", "get-caller-identity",
                                        "--query", "Account", "--output", "text"], text=True).strip()
    if identity != "455982475279":
        raise SystemExit("Cuenta AWS inesperada")
    subprocess.run(["aws", "eks", "update-kubeconfig", "--name", "abuelito-eks",
                    "--region", "us-east-1", "--alias", "abuelito-ci",
                    "--kubeconfig", os.environ["KUBECONFIG"]], check=True)
    kube = ["kubectl", "--context", "abuelito-ci", "-n", "abuelito"]
    for secret in ("abuelito-config", "abuelito-migration-config"):
        # Solo consulta existencia, nunca imprime valores.
        subprocess.run(kube + ["get", "secret", secret, "-o", "name"], check=True)
    suffix = os.environ["GITHUB_RUN_ID"] + "-" + os.environ["GITHUB_RUN_ATTEMPT"]
    job_name = "abuelito-migrate-" + suffix
    job = {"apiVersion": "batch/v1", "kind": "Job",
           "metadata": {"name": job_name, "namespace": "abuelito"},
           "spec": {"backoffLimit": 0, "activeDeadlineSeconds": 600,
                    "ttlSecondsAfterFinished": 86400, "template": {"spec": {
                        "restartPolicy": "Never", "automountServiceAccountToken": False, "nodeSelector": {"kubernetes.io/arch": "arm64"},
                        "containers": [{"name": "migrator", "image": release["migrator_image"],
                                        "command": ["sh", "-c", "npx prisma migrate deploy && node -e \"$AFTER_MIGRATION_JS\""],
                                        "env": [{"name": "AFTER_MIGRATION_JS", "value":
                                                 "const {PrismaClient}=require('@prisma/client');const db=new PrismaClient();"
                                                 "db.$executeRawUnsafe('REVOKE ALL ON TABLE public._prisma_migrations FROM abuelito_app')"
                                                 ".then(()=>console.log('Migration metadata restricted')).catch(()=>{console.error('Permission cleanup failed');process.exitCode=1}).finally(()=>db.$disconnect());"},
                                                {"name": "DATABASE_URL", "valueFrom": {
                                            "secretKeyRef": {"name": "abuelito-migration-config", "key": "DATABASE_URL"}}}],
                                        "resources": {"requests": {"cpu": "100m", "memory": "256Mi"},
                                                      "limits": {"cpu": "1", "memory": "512Mi"}}}]}}}}
    subprocess.run(kube + ["create", "-f", "-"], input=json.dumps(job), text=True, check=True)
    for _ in range(120):
        status = json.loads(subprocess.check_output(kube + ["get", "job", job_name, "-o", "json"])).get("status", {})
        if status.get("succeeded"):
            break
        if status.get("failed"):
            raise SystemExit("Migracion fallo. Deployment no actualizado; revisar Job.")
        time.sleep(5)
    else:
        raise SystemExit("Migracion no termino. Deployment no actualizado.")
    # El namespace ya existe; el rol CI solo administra abuelito.
    template = Path("deploy/kubernetes/abuelito.yaml.template").read_text()
    template = template.split("---", 1)[1].replace("${ABUELITO_IMAGE}", release["web_image"])
    subprocess.run(kube + ["apply", "-f", "-"], input=template, text=True, check=True)
    subprocess.run(kube + ["rollout", "status", "deployment/abuelito", "--timeout=300s"], check=True)
    result = dict(release, environment="dev", migration_job=job_name,
                  deployment_status="ready", functional_acceptance="pending_user")
    Path("deployment.json").write_text(json.dumps(result, indent=2) + "\n")
    print("Desplegado. Las pruebas funcionales corresponden al usuario.")

if __name__ == "__main__":
    main()
