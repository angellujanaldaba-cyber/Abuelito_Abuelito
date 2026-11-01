import copy
import unittest
from deploy_release import REPOSITORY, validate_release

class ReleaseIdentityTests(unittest.TestCase):
    def setUp(self):
        self.release = {
            "source_commit": "a" * 40, "architecture": "linux/arm64",
            "web_image": REPOSITORY + "@sha256:" + "b" * 64,
            "migrator_image": REPOSITORY + "@sha256:" + "c" * 64,
            "prisma_files_sha256": {"prisma/schema.prisma": "d" * 64},
        }

    def test_immutable_release_is_accepted(self):
        self.assertEqual(validate_release(self.release), self.release)

    def test_mutable_tag_is_rejected(self):
        self.release["web_image"] = REPOSITORY + ":latest"
        with self.assertRaises(ValueError):
            validate_release(self.release)

    def test_other_account_is_rejected(self):
        self.release["migrator_image"] = self.release["migrator_image"].replace("455982475279", "000000000000")
        with self.assertRaises(ValueError):
            validate_release(self.release)

    def test_wrong_architecture_is_rejected(self):
        self.release["architecture"] = "linux/amd64"
        with self.assertRaises(ValueError):
            validate_release(self.release)

    def test_unknown_source_is_rejected(self):
        self.release["source_commit"] = "unknown"
        with self.assertRaises(ValueError):
            validate_release(self.release)


class HistoricalRecoveryTests(unittest.TestCase):
    def setUp(self):
        import json
        from pathlib import Path
        self.release = json.loads((Path(__file__).resolve().parents[1] / 'records/recovery-release.json').read_text())
        self.release['deployment_commit'] = 'a' * 40

    def test_exact_historical_pair_is_accepted(self):
        from deploy_release import validate_historical_release
        self.assertEqual(validate_historical_release(self.release), self.release)

    def test_other_digest_cannot_be_used_as_historical(self):
        from deploy_release import validate_historical_release
        self.release['web_image'] = REPOSITORY + '@sha256:' + 'a' * 64
        with self.assertRaises(ValueError): validate_historical_release(self.release)

    def test_fabricated_image_source_commit_is_rejected(self):
        from deploy_release import validate_historical_release
        self.release['source_commit'] = 'a' * 40
        with self.assertRaises(ValueError): validate_historical_release(self.release)
        with self.assertRaises(ValueError): validate_release(self.release)

    def test_historical_record_is_not_accepted_as_a_new_build(self):
        with self.assertRaises((ValueError, TypeError)): validate_release(self.release)

if __name__ == "__main__":
    unittest.main()
