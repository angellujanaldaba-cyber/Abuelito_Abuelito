#!/usr/bin/env python3
"""Entrypoint dentro de CodeBuild; bootstrap privilegiado y deploy separados."""
import json
import os
from pathlib import Path
import re
import subprocess
import time


def main():
    metadata = json.loads(Path('pipeline-input.json').read_text())
    stage = os.environ['PIPELINE_STAGE']
    if stage not in ['bootstrap', 'deploy']:
        raise SystemExit('Etapa no autorizada')
    project = os.environ['CODEBUILD_BUILD_ID'].split(':', 1)[0]
    if project != 'abuelito-eks-' + stage:
        raise SystemExit('Proyecto CodeBuild no corresponde a la etapa')
    commit, run_id, attempt = (metadata[x] for x in ['source_commit', 'run_id', 'attempt'])
    if not re.fullmatch(r'[a-f0-9]{40}', commit) or not run_id.isdigit() or not attempt.isdigit():
        raise SystemExit('Identidad de paquete invalida')
    from invoke_codebuild import validate_input
    validate_input(metadata['release'], commit, run_id, attempt)
    Path('release.json').write_text(json.dumps(metadata['release']))
    Path('/tmp/abuelito-codebuild').mkdir(mode=0o700, exist_ok=True)
    os.environ.update(GITHUB_SHA=commit, GITHUB_RUN_ID=run_id, GITHUB_RUN_ATTEMPT=attempt,
                      KUBECONFIG=str(Path('/tmp/abuelito-codebuild/kubeconfig')))
    try:
        if stage == 'bootstrap':
            subprocess.run(['python3', 'deploy/scripts/bootstrap_database.py', '--pipeline'], check=True)
            result = json.loads(Path('bootstrap-result.json').read_text())
        else:
            subprocess.run(['python3', 'deploy/scripts/deploy_release.py'], check=True)
            result = json.loads(Path('deployment.json').read_text())
            # Solo metadata del balanceador: no crea ni consulta pedidos.
            deadline = time.monotonic() + 300
            while time.monotonic() < deadline:
                health = json.loads(subprocess.check_output(['aws', 'elbv2', 'describe-target-health',
                    '--target-group-arn', os.environ['ALB_TARGET_GROUP_ARN'], '--region', 'us-east-1']))['TargetHealthDescriptions']
                if len(health) >= 2 and all(h['TargetHealth']['State'] == 'healthy' for h in health):
                    break
                time.sleep(10)
            else:
                raise SystemExit('ALB no tiene los dos destinos sanos; no actualizar DNS')
            result['alb_targets'] = 'healthy'
            result['alb_dns_name'] = os.environ['ALB_DNS_NAME']
        result.update(stage=stage, source_commit=commit, run_id=run_id,
                      codebuild_id=os.environ['CODEBUILD_BUILD_ID'], functional_acceptance='pending_user')
        path = Path('private-result.json')
        path.write_text(json.dumps(result, indent=2))
        key = 'codebuild/dev/results/' + run_id + '/' + commit + '/' + stage + '-' + attempt + '.json'
        subprocess.run(['aws', 's3', 'cp', str(path), 's3://' + os.environ['PIPELINE_BUCKET'] + '/' + key,
                        '--sse', 'AES256'], check=True)
    finally:
        Path(os.environ['KUBECONFIG']).unlink(missing_ok=True)


if __name__ == '__main__':
    main()
