#!/usr/bin/env python3
"""Plan privado en S3; apply solo del plan guardado y del mismo commit."""
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

def run(args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)

def required(name):
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit("Falta configurar " + name)
    return value

def main():
    operation = required("OPERATION")
    if operation not in ("plan", "plan-destroy", "apply-plan"):
        raise SystemExit("Operacion invalida")
    bucket = required("TF_STATE_BUCKET")
    if not re.fullmatch(r"[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]", bucket):
        raise SystemExit("Bucket invalido")
    commit = required("GITHUB_SHA")
    run_id = required("GITHUB_RUN_ID")
    if not re.fullmatch(r"[a-f0-9]{40}", commit) or not run_id.isdigit():
        raise SystemExit("Identidad de ejecucion invalida")
    account = subprocess.check_output(["aws", "sts", "get-caller-identity",
                                       "--query", "Account", "--output", "text"], text=True).strip()
    if account != "455982475279":
        raise SystemExit("Cuenta AWS inesperada")
    networks = json.loads(required("TF_VAR_admin_cidrs"))
    if not isinstance(networks, list) or not networks:
        raise SystemExit("Configura CIDRs administrativos")
    for value in networks:
        network = ipaddress.ip_network(value)
        if network.version != 4 or network.prefixlen < 24:
            raise SystemExit("CIDR administrativo demasiado amplio")
    required("TF_VAR_admin_principal_arn")
    required("TF_VAR_acm_certificate_arn")
    if not os.environ.get("TF_VAR_ci_deploy_role_arn"):
        os.environ.pop("TF_VAR_ci_deploy_role_arn", None)
    os.environ["TF_IN_AUTOMATION"] = "1"
    tf = ["terraform", "-chdir=deploy/terraform"]
    run(tf + ["init", "-input=false", "-reconfigure",
              "-backend-config=bucket=" + bucket,
              "-backend-config=key=abuelito/dev/terraform.tfstate",
              "-backend-config=region=us-east-1", "-backend-config=encrypt=true",
              "-backend-config=use_lockfile=true"])
    run(tf + ["validate", "-no-color"])
    with tempfile.TemporaryDirectory(prefix="abuelito-plan-") as temporary:
        directory = Path(temporary)
        binary = directory / "plan.tfplan"
        metadata_path = directory / "plan.json"
        if operation.startswith("plan"):
            args = tf + ["plan", "-input=false", "-lock-timeout=120s",
                         "-out=" + str(binary), "-no-color"]
            if operation == "plan-destroy":
                args.append("-destroy")
            run(args)
            metadata = {"commit": commit, "run_id": run_id, "operation": operation,
                        "sha256": hashlib.sha256(binary.read_bytes()).hexdigest()}
            metadata_path.write_text(json.dumps(metadata))
            prefix = "s3://" + bucket + "/plans/dev/" + run_id + "/" + commit + "/"
            for file in (binary, metadata_path):
                run(["aws", "s3", "cp", str(file), prefix + file.name, "--sse", "AES256"])
            print("Plan privado guardado. Revisar este run antes de aplicar.")
        else:
            plan_run = required("PLAN_RUN_ID")
            if not plan_run.isdigit():
                raise SystemExit("PLAN_RUN_ID invalido")
            if required("CONFIRMATION") != "APPLY " + plan_run:
                raise SystemExit("Confirmacion requerida: APPLY seguido del ID del plan")
            prefix = "s3://" + bucket + "/plans/dev/" + plan_run + "/" + commit + "/"
            for file in (binary, metadata_path):
                run(["aws", "s3", "cp", prefix + file.name, str(file)])
            metadata = json.loads(metadata_path.read_text())
            if (metadata["commit"] != commit or metadata["run_id"] != plan_run
                    or metadata["operation"] not in ("plan", "plan-destroy")
                    or metadata["sha256"] != hashlib.sha256(binary.read_bytes()).hexdigest()):
                raise SystemExit("Identidad o integridad de plan invalida")
            run(tf + ["apply", "-input=false", "-no-color", str(binary)])

if __name__ == "__main__":
    main()
