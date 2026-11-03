#!/usr/bin/env python3
"""Lanza una ejecucion privada desde GitHub; no guarda credenciales en el paquete."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import tempfile
import time
import zipfile


def aws(*args):
    return json.loads(subprocess.check_output(['aws', *args, '--region', 'us-east-1', '--output', 'json']) or b'{}')


def validate_input(release, commit, run_id, attempt):
    from deploy_release import validate_release
    validate_release(release)
    if not re.fullmatch(r'[a-f0-9]{40}', commit) or release['source_commit'] != commit:
        raise ValueError('El build y los scripts deben ser del mismo commit')
    if not run_id.isdigit() or not attempt.isdigit():
        raise ValueError('Identidad de ejecucion invalida')
    return {'source_commit': commit, 'run_id': run_id, 'attempt': attempt, 'release': release}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['bootstrap', 'deploy'])
    parser.add_argument('--release', required=True)
    args = parser.parse_args()
    bucket = os.environ['TF_STATE_BUCKET']
    commit, run_id, attempt = (os.environ[x] for x in ['GITHUB_SHA', 'GITHUB_RUN_ID', 'GITHUB_RUN_ATTEMPT'])
    metadata = validate_input(json.loads(Path(args.release).read_text()), commit, run_id, attempt)
    if aws('sts', 'get-caller-identity')['Account'] != '455982475279':
        raise SystemExit('Cuenta inesperada')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    if head != commit or subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=no']).strip():
        raise SystemExit('El checkout no es el commit limpio esperado')
    source = subprocess.check_output(['git', 'archive', '--format=zip', commit])
    with tempfile.TemporaryDirectory(prefix='abuelito-bundle-') as directory:
        archive = Path(directory) / 'source.zip'
        archive.write_bytes(source)
        with zipfile.ZipFile(archive, 'a', zipfile.ZIP_DEFLATED) as bundle:
            if 'pipeline-input.json' in bundle.namelist():
                raise SystemExit('Nombre reservado en el codigo fuente')
            bundle.writestr('pipeline-input.json', json.dumps(metadata))
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        key = 'codebuild/dev/bundles/' + run_id + '/' + commit + '-' + attempt + '.zip'
        subprocess.run(['aws', 's3', 'cp', str(archive), 's3://' + bucket + '/' + key, '--sse', 'AES256'], check=True)
    project = 'abuelito-eks-' + args.stage
    override = [{'name': 'BUNDLE_KEY', 'value': key, 'type': 'PLAINTEXT'},
                {'name': 'BUNDLE_SHA256', 'value': digest, 'type': 'PLAINTEXT'}]
    build_id = None
    complete = False
    def cancel(*_):
        raise KeyboardInterrupt('Ejecucion cancelada')
    signal.signal(signal.SIGTERM, cancel)
    try:
        build = aws('codebuild', 'start-build', '--project-name', project,
                    '--environment-variables-override', json.dumps(override),
                    '--idempotency-token', run_id + '-' + attempt + '-' + args.stage)['build']
        build_id = build['id']
        print('CodeBuild privado iniciado: ' + build_id, flush=True)
        deadline = time.monotonic() + 42 * 60
        while time.monotonic() < deadline:
            builds = aws('codebuild', 'batch-get-builds', '--ids', build_id)['builds']
            if len(builds) != 1:
                raise SystemExit('No se encontro la ejecucion privada esperada')
            current = builds[0]
            if current['buildComplete']:
                complete = True
                if current['buildStatus'] != 'SUCCEEDED':
                    raise SystemExit('CodeBuild ' + current['buildStatus'] + '; revisar logs privados: ' + current.get('logs', {}).get('deepLink', build_id))
                break
            print('CodeBuild: ' + current.get('currentPhase', 'en espera'), flush=True)
            time.sleep(15)
        else:
            raise SystemExit('Tiempo de espera agotado')
    finally:
        if build_id and not complete:
            aws('codebuild', 'stop-build', '--id', build_id)
    result_key = 'codebuild/dev/results/' + run_id + '/' + commit + '/' + args.stage + '-' + attempt + '.json'
    result_path = Path(args.stage + '-result.json')
    subprocess.run(['aws', 's3', 'cp', 's3://' + bucket + '/' + result_key, str(result_path)], check=True)
    result = json.loads(result_path.read_text())
    if result.get('source_commit') != commit or result.get('run_id') != run_id or result.get('stage') != args.stage:
        raise SystemExit('Resultado de otra version o ejecucion')
    print('Ejecucion privada completada; resultado sin credenciales: ' + str(result_path))


if __name__ == '__main__':
    main()
