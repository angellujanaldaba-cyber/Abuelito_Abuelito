#!/usr/bin/env python3
"""Cambiar solo el CNAME dev tras rollout sano; no consulta ni crea pedidos."""
import argparse
import json
import os
from pathlib import Path
import re
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

NAME = 'dev.miguelinfra.com'


def validate_target(value):
    if not re.fullmatch(r'abuelito-eks-[a-z0-9-]+\.us-east-1\.elb\.amazonaws\.com', value):
        raise ValueError('Destino fuera del ALB autorizado')
    return value


def removable(record, expected):
    return record.get('type') == 'CNAME' and record.get('name') == NAME and record.get('content', '').rstrip('.') == expected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['publish', 'remove'])
    parser.add_argument('--result')
    args = parser.parse_args()
    zone = os.environ.get('CLOUDFLARE_ZONE_ID', '')
    token = os.environ.get('CLOUDFLARE_API_TOKEN', '')
    if not re.fullmatch(r'[a-f0-9]{32}', zone) or not token:
        raise SystemExit('Configurar Zone ID y token DNS limitado en dev-dns')
    if args.operation == 'publish':
        result = json.loads(Path(args.result).read_text())
        if (result.get('source_commit') != os.environ['GITHUB_SHA']
                or result.get('run_id') != os.environ['GITHUB_RUN_ID']
                or result.get('deployment_status') != 'ready' or result.get('alb_targets') != 'healthy'):
            raise SystemExit('No publicar DNS sin resultado sano del mismo commit/run')
        expected = validate_target(result['alb_dns_name'])
    else:
        expected = validate_target(os.environ['EXPECTED_ALB'])

    def api(method, suffix, payload=None):
        request = Request('https://api.cloudflare.com/client/v4/zones/' + zone + '/dns_records' + suffix,
                          method=method, data=json.dumps(payload).encode() if payload else None,
                          headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'})
        try:
            with urlopen(request, timeout=30) as response:
                data = json.load(response)
        except HTTPError as error:
            # No volcar respuestas/cabeceras que puedan contener datos sensibles.
            raise SystemExit('Cloudflare devolvio HTTP ' + str(error.code)) from None
        if not data.get('success'):
            raise SystemExit('Cloudflare rechazo el cambio DNS')
        return data.get('result')

    records = api('GET', '?' + urlencode({'name': NAME}))
    if len(records) > 1 or (records and records[0]['type'] != 'CNAME'):
        raise SystemExit('Registro DNS inesperado; no reemplazar otros tipos ni varios registros')
    if args.operation == 'publish':
        payload = {'type': 'CNAME', 'name': NAME, 'content': expected, 'ttl': 60, 'proxied': False}
        if records:
            api('PUT', '/' + records[0]['id'], payload)
        else:
            api('POST', '', payload)
        print('CNAME dev actualizado al ALB sano; DNS only.')
    elif records:
        if not removable(records[0], expected):
            raise SystemExit('El CNAME cambio de destino; no eliminar el registro de otro despliegue')
        api('DELETE', '/' + records[0]['id'])
        print('CNAME del ALB retirado eliminado.')
    else:
        print('CNAME ya ausente.')


if __name__ == '__main__':
    main()
