"""Bootstrap inline de CodeBuild: verificar paquete antes de ejecutar su codigo."""
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import zipfile


def safe_members(source):
    members = source.infolist()
    names = [item.filename for item in members]
    if len(names) != len(set(names)) or sum(item.file_size for item in members) > 512 * 1024 * 1024:
        raise ValueError('Paquete duplicado o demasiado grande')
    for item in members:
        path = PurePosixPath(item.filename)
        if path.is_absolute() or '..' in path.parts or '\\' in item.filename:
            raise ValueError('Ruta insegura dentro del paquete')
        if (item.external_attr >> 16) & 0o170000 == 0o120000:
            raise ValueError('No se permiten enlaces simbolicos')
    return members


def main():
    bucket, key, expected = (os.environ[x] for x in ['PIPELINE_BUCKET', 'BUNDLE_KEY', 'BUNDLE_SHA256'])
    if not re.fullmatch(r'codebuild/dev/bundles/[0-9]+/[a-f0-9]{40}-[0-9]+\.zip', key):
        raise SystemExit('Bundle key no autorizado')
    if not re.fullmatch(r'[a-f0-9]{64}', expected):
        raise SystemExit('SHA256 invalido')
    archive = Path('/tmp/abuelito-source.zip')
    subprocess.run(['aws', 's3', 'cp', 's3://' + bucket + '/' + key, str(archive)], check=True)
    if hashlib.sha256(archive.read_bytes()).hexdigest() != expected:
        raise SystemExit('El paquete privado no coincide con el hash autorizado')
    with zipfile.ZipFile(archive) as source:
        safe_members(source)
        source.extractall(os.environ['CODEBUILD_SRC_DIR'])
    archive.unlink()


if __name__ == '__main__':
    main()
