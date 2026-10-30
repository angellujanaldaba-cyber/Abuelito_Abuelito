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

if __name__ == "__main__":
    unittest.main()
