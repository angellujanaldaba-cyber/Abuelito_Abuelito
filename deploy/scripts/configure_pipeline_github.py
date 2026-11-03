#!/usr/bin/env python3
"""Configura environments/variables GitHub; no crea recursos AWS ni lee passwords."""
import argparse
import ipaddress
import json
import re
import subprocess

REPO = 'angellujanaldaba-cyber/Abuelito_Abuelito'
OWNER = REPO.split('/')[0]
BASE = 'repos/' + REPO


def api(path, method='GET', payload=None, missing=False):
    command = ['gh', 'api', path, '--method', method]
    if payload is not None: command += ['--input', '-']
    result = subprocess.run(command, input=json.dumps(payload) if payload is not None else None,
                            capture_output=True, text=True)
    if result.returncode:
        if missing and 'HTTP 404' in result.stderr: return None
        raise SystemExit('GitHub API fallo para ' + path + ': ' + result.stderr)
    return json.loads(result.stdout) if result.stdout.strip() else {}


def variables(env):
    return {x['name']: x['value'] for x in api(BASE + '/environments/' + env + '/variables?per_page=100')['variables']}


def set_variable(env, name, value):
    subprocess.run(['gh', 'variable', 'set', name, '--repo', REPO, '--env', env, '--body', value], check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--admin-cidr', help='IPv4 publica autorizada, preferentemente /32')
    parser.add_argument('--zone-id', help='Zone ID de miguelinfra.com; nunca el token')
    args = parser.parse_args()
    caller = api('user')
    if caller['login'].lower() != OWNER.lower(): raise SystemExit('Autenticarse como propietario del repositorio esperado')
    if args.zone_id and not re.fullmatch('[a-f0-9]{32}', args.zone_id): raise SystemExit('Zone ID invalido')
    if args.admin_cidr:
        network = ipaddress.ip_network(args.admin_cidr)
        if network.version != 4 or network.prefixlen < 24: raise SystemExit('CIDR debe ser IPv4 /24 o mas restrictivo')
    for env in ['dev-plan', 'dev-build', 'dev-infrastructure', 'dev-deploy', 'dev-dns']:
        current = api(BASE + '/environments/' + env, missing=True) or {}
        rules = current.get('protection_rules', [])
        review = next((r for r in rules if r['type'] == 'required_reviewers'), {})
        reviewers = [{'type': x['type'], 'id': x['reviewer']['id']} for x in review.get('reviewers', [])]
        if env not in ['dev-plan', 'dev-build'] and not reviewers:
            reviewers = [{'type': 'User', 'id': caller['id']}]
        timer = next((r.get('wait_timer', 0) for r in rules if r['type'] == 'wait_timer'), 0)
        api(BASE + '/environments/' + env, 'PUT', {
            'reviewers': reviewers, 'prevent_self_review': review.get('prevent_self_review', False),
            'wait_timer': timer, 'deployment_branch_policy': {'protected_branches': False, 'custom_branch_policies': True}})
        policies = api(BASE + '/environments/' + env + '/deployment-branch-policies')['branch_policies']
        if any(p['name'] != 'main' for p in policies):
            raise SystemExit('Revisar las reglas existentes: ' + env + ' permite otra rama')
        if not policies:
            api(BASE + '/environments/' + env + '/deployment-branch-policies', 'POST', {'name': 'main', 'type': 'branch'})
    old = variables('dev-infrastructure')
    networks = json.dumps([args.admin_cidr]) if args.admin_cidr else old.get('ADMIN_CIDRS_JSON')
    if not networks: raise SystemExit('Falta --admin-cidr; no se adivinara la IP')
    for value in json.loads(networks):
        n = ipaddress.ip_network(value)
        if n.version != 4 or n.prefixlen < 24: raise SystemExit('CIDR existente demasiado amplio')
    bucket = 'abuelito-eks-tfstate-455982475279-us-east-1'
    role = 'arn:aws:iam::455982475279:role/abuelito-ci-'
    shared = {'TF_STATE_BUCKET': bucket, 'ADMIN_CIDRS_JSON': networks,
              'ADMIN_PRINCIPAL_ARN': 'arn:aws:iam::455982475279:user/abuelito-dev',
              'ACM_CERTIFICATE_ARN': 'arn:aws:acm:us-east-1:455982475279:certificate/be017180-4466-4df4-8c71-c531169ccddd'}
    for env in ['dev-plan', 'dev-infrastructure']:
        for name, value in shared.items(): set_variable(env, name, value)
    set_variable('dev-plan', 'AWS_PLAN_ROLE_ARN', role + 'plan')
    set_variable('dev-infrastructure', 'AWS_INFRA_ROLE_ARN', role + 'infrastructure')
    set_variable('dev-build', 'AWS_BUILD_ROLE_ARN', role + 'build')
    set_variable('dev-deploy', 'AWS_DEPLOY_ROLE_ARN', role + 'deploy')
    set_variable('dev-deploy', 'TF_STATE_BUCKET', bucket)
    if args.zone_id: set_variable('dev-dns', 'CLOUDFLARE_ZONE_ID', args.zone_id)
    dnsvars = variables('dev-dns')
    secret_names = {s['name'] for s in api(BASE + '/environments/dev-dns/secrets?per_page=100')['secrets']}
    ready = bool(dnsvars.get('CLOUDFLARE_ZONE_ID')) and 'CLOUDFLARE_API_TOKEN' in secret_names
    subprocess.run(['gh', 'variable', 'set', 'DNS_AUTOMATION_READY', '--repo', REPO, '--body', str(ready).lower()], check=True)
    print('Environments/variables preparados; sin recursos AWS creados. DNS metadata ready:', ready)


if __name__ == '__main__': main()
