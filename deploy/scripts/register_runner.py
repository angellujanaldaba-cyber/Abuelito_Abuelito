#!/usr/bin/env python3
"""Registra por SSM interactivo un runner efimero. Token solo en memoria/TTY oculto."""
import argparse
import json
import os
import pty
import re
import select
import signal
import subprocess
import termios
import time

REPO = "angellujanaldaba-cyber/Abuelito_Abuelito"


def aws(*args):
    return json.loads(subprocess.check_output(["aws", *args, "--region", "us-east-1", "--output", "json"]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instance-id", required=True)
    parser.add_argument("--plugin-bin", help="Directorio de session-manager-plugin si no esta en PATH")
    args = parser.parse_args()
    if not re.fullmatch(r"i-[a-f0-9]{17}", args.instance_id):
        raise SystemExit("Instance ID invalido")
    if args.plugin_bin:
        os.environ["PATH"] = args.plugin_bin + os.pathsep + os.environ["PATH"]
    if aws("sts", "get-caller-identity")["Account"] != "455982475279":
        raise SystemExit("Cuenta inesperada")
    instance = aws("ec2", "describe-instances", "--instance-ids", args.instance_id)["Reservations"][0]["Instances"][0]
    tags = {tag["Key"]: tag["Value"] for tag in instance.get("Tags", [])}
    vpc = aws("eks", "describe-cluster", "--name", "abuelito-eks")["cluster"]["resourcesVpcConfig"]["vpcId"]
    if (tags.get("Project") != "abuelito-runner" or instance["Architecture"] != "arm64"
            or instance.get("PublicIpAddress") or instance["VpcId"] != vpc
            or instance["State"]["Name"] != "running"):
        raise SystemExit("La instancia no es el runner privado esperado")
    command = ["aws", "ssm", "start-session", "--target", args.instance_id,
               "--region", "us-east-1", "--document-name", "AWS-StartInteractiveCommand",
               "--parameters", json.dumps({"command": ["sudo /usr/local/sbin/register-abuelito-runner"]})]
    pid, fd = pty.fork()
    if pid == 0:
        os.execvp(command[0], command)
    transcript = b""
    token = b""
    sent = False
    finished = False
    try:
        deadline = time.monotonic() + 180
        while time.monotonic() < deadline:
            readable, _, _ = select.select([fd], [], [], 1)
            if readable:
                try:
                    chunk = os.read(fd, 4096)
                except OSError:
                    break
                if not chunk:
                    break
                transcript = (transcript + chunk)[-32000:]
            if not sent and b"entrada oculta" in transcript:
                if termios.tcgetattr(fd)[3] & termios.ECHO:
                    # No enviar el token si el TTY aun permite eco de entrada.
                    continue
                token = subprocess.check_output(["gh", "api", "--method", "POST",
                    "repos/" + REPO + "/actions/runners/registration-token", "--jq", ".token"]).strip()
                if not re.fullmatch(rb"[A-Za-z0-9_]+", token):
                    raise RuntimeError("Formato de token inesperado")
                os.write(fd, token + b"\n")
                sent = True
            if b"Runner iniciado para un solo job" in transcript:
                finished = True
                break
            done, _ = os.waitpid(pid, os.WNOHANG)
            if done:
                pid = 0
                break
        if not finished:
            safe = transcript.replace(token, b"[REDACTED]") if token else transcript
            raise SystemExit("No se confirmo registro. Sesion SSM: " + safe[-1800:].decode(errors="replace"))
    finally:
        if pid:
            try:
                os.killpg(pid, signal.SIGTERM)
                os.waitpid(pid, 0)
            except ProcessLookupError:
                pass
        os.close(fd)
        token = b""
    print("Registro enviado por SSM; token no guardado. Confirmar Online con la API de GitHub.")


if __name__ == "__main__":
    main()
