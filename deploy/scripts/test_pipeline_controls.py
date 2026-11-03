import copy
import importlib.util
import io
import json
from pathlib import Path
import unittest
import zipfile

from cloudflare_dns import NAME, removable, validate_target
from infrastructure import validate_plan_metadata
from invoke_codebuild import validate_input

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('fetch_bundle', ROOT / 'deploy/codebuild/fetch_bundle.py')
fetch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetch)


class PlanTests(unittest.TestCase):
    def setUp(self):
        self.metadata = dict(schema=1, account='455982475279', region='us-east-1',
                             state_key='abuelito/dev/terraform.tfstate', commit='a'*40,
                             run_id='123', operation='plan', sha256='b'*64)

    def verify(self, metadata):
        return validate_plan_metadata(metadata, 'a'*40, '123', 'b'*64, 'plan')

    def test_plan_identity(self):
        self.verify(self.metadata)

    def test_modified_commit_run_digest_account_or_state_rejected(self):
        for field in ['commit', 'run_id', 'sha256', 'account', 'state_key', 'region', 'schema']:
            with self.subTest(field=field):
                changed = dict(self.metadata, **{field: 'different'})
                with self.assertRaises(ValueError): self.verify(changed)

    def test_destroy_plan_cannot_be_applied_as_deploy(self):
        with self.assertRaises(ValueError): self.verify(dict(self.metadata, operation='plan-destroy'))


class BundleTests(unittest.TestCase):
    def archive(self, name):
        data = io.BytesIO()
        with zipfile.ZipFile(data, 'w') as z: z.writestr(name, 'test')
        data.seek(0)
        return zipfile.ZipFile(data)

    def test_normal_file_allowed(self):
        with self.archive('deploy/scripts/codebuild_execute.py') as z: fetch.safe_members(z)

    def test_escaping_paths_rejected(self):
        for name in ['../escape', '/tmp/escape', 'deploy/../../escape', 'deploy\\escape']:
            with self.subTest(name=name), self.archive(name) as z:
                with self.assertRaises(ValueError): fetch.safe_members(z)

    def test_symlink_rejected(self):
        data = io.BytesIO()
        with zipfile.ZipFile(data, 'w') as z:
            item = zipfile.ZipInfo('link');item.external_attr = 0o120777 << 16;z.writestr(item, '/tmp')
        data.seek(0)
        with zipfile.ZipFile(data) as z:
            with self.assertRaises(ValueError): fetch.safe_members(z)

    def test_build_commit_must_match_bundle(self):
        release = dict(source_commit='a'*40, architecture='linux/arm64',
                       web_image='455982475279.dkr.ecr.us-east-1.amazonaws.com/abuelito-eks-web@sha256:'+'b'*64,
                       migrator_image='455982475279.dkr.ecr.us-east-1.amazonaws.com/abuelito-eks-web@sha256:'+'c'*64,
                       prisma_files_sha256={'prisma/schema.prisma':'d'*64})
        validate_input(release, 'a'*40, '123', '1')
        with self.assertRaises(ValueError): validate_input(release, 'e'*40, '123', '1')
        with self.assertRaises(ValueError): validate_input(release, 'a'*40, '../run', '1')


class DNSTests(unittest.TestCase):
    def test_only_our_alb_is_allowed(self):
        self.assertEqual(validate_target('abuelito-eks-123.us-east-1.elb.amazonaws.com'), 'abuelito-eks-123.us-east-1.elb.amazonaws.com')
        for target in ['evil.example', 'abuelito-eks-123.us-west-2.elb.amazonaws.com', 'other-123.us-east-1.elb.amazonaws.com']:
            with self.assertRaises(ValueError): validate_target(target)

    def test_destroy_does_not_delete_changed_record(self):
        record = dict(type='CNAME', name=NAME, content='abuelito-eks-123.us-east-1.elb.amazonaws.com')
        self.assertTrue(removable(record, record['content']))
        self.assertFalse(removable(record, 'abuelito-eks-456.us-east-1.elb.amazonaws.com'))
        self.assertFalse(removable(dict(record, name='www.miguelinfra.com'), record['content']))


class PermissionBoundaries(unittest.TestCase):
    def setUp(self):
        self.resources = json.loads((ROOT / 'deploy/bootstrap/main.tf.json').read_text())['resource']

    def actions(self, role):
        policy = json.loads(self.resources['aws_iam_role_policy'][role]['policy'])
        return {action for s in policy['Statement'] for action in s['Action']}

    def test_plan_role_cannot_create_or_apply_resources(self):
        actions = self.actions('plan')
        for action in ['ec2:CreateVpc', 'rds:CreateDBInstance', 's3:DeleteBucket', 'iam:PassRole']:
            self.assertNotIn(action, actions)
        statements = json.loads(self.resources['aws_iam_role_policy']['plan']['policy'])['Statement']
        state = 'arn:aws:s3:::abuelito-eks-tfstate-455982475279-us-east-1/abuelito/dev/terraform.tfstate'
        self.assertFalse(any('s3:PutObject' in s['Action'] and state in s['Resource'] for s in statements))

    def test_deploy_role_does_not_read_admin_secret(self):
        actions = self.actions('deploy')
        self.assertNotIn('secretsmanager:GetSecretValue', actions)
        doc = self.resources['aws_iam_role_policy']['deploy']['policy']
        self.assertNotIn('abuelito-eks-bootstrap', doc)
        self.assertNotIn('iam:PassRole', actions)

    def test_codebuild_roles_require_immutable_permissions_boundary(self):
        support = json.loads(self.resources['aws_iam_role_policy']['infra_support']['policy'])
        for mode in ['bootstrap', 'deploy']:
            arn = 'arn:aws:iam::455982475279:role/abuelito-eks-codebuild-' + mode
            statements = [s for s in support['Statement'] if 'iam:CreateRole' in s['Action'] and arn in s['Resource']]
            self.assertTrue(statements)
            self.assertTrue(all('iam:PermissionsBoundary' in s.get('Condition', {}).get('ArnEquals', {}) for s in statements))
            boundary = json.loads(self.resources['aws_iam_policy']['boundary_' + mode]['policy'])
            self.assertFalse(any(a.startswith('iam:') for s in boundary['Statement'] for a in s['Action']))
        actions = self.actions('infra_support')
        self.assertNotIn('iam:DeleteRolePermissionsBoundary', actions)
        self.assertNotIn('iam:PutRolePermissionsBoundary', actions)


if __name__ == '__main__': unittest.main()
