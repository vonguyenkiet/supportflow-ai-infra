"""Unit tests for release manifest JSON Schema Draft 2020-12 and business invariant validator."""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_release_manifest import ROOT, validate_manifest, main


class TestReleaseManifestValidator(unittest.TestCase):
    def setUp(self):
        self.canonical_path = ROOT / "releases" / "release-1.0.0-rc1.json"
        self.canonical_data = json.loads(self.canonical_path.read_text(encoding="utf-8"))
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

    def write_manifest(self, data: dict) -> Path:
        path = Path(self.temp_dir.name) / "test-manifest.json"
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return path

    def test_positive_canonical_manifest(self):
        """Positive test: canonical release manifest passes all schema and invariant checks."""
        manifest = validate_manifest(self.canonical_path)
        self.assertEqual(manifest["releaseId"], "rel-20261031-01")
        self.assertEqual(manifest["version"], "1.0.0-rc1")
        self.assertEqual(main([str(self.canonical_path)]), 0)

    def test_negative_missing_required_key(self):
        """Negative test: missing top-level required key fails JSON Schema validation."""
        data = copy.deepcopy(self.canonical_data)
        del data["releaseId"]
        path = self.write_manifest(data)
        with self.assertRaises(ValueError) as ctx:
            validate_manifest(path)
        self.assertIn("JSON Schema Draft 2020-12 validation failed", str(ctx.exception))
        self.assertEqual(main([str(path)]), 1)

    def test_negative_invalid_commit_sha(self):
        """Negative test: short or invalid commit SHA fails commit pattern validation."""
        data = copy.deepcopy(self.canonical_data)
        data["components"]["backend"]["buildCommit"] = "not-a-valid-40-hex-sha"
        path = self.write_manifest(data)
        with self.assertRaises(ValueError) as ctx:
            validate_manifest(path)
        self.assertTrue(
            "validation failed" in str(ctx.exception).lower() or "invalid full commit sha" in str(ctx.exception).lower()
        )
        self.assertEqual(main([str(path)]), 1)

    def test_negative_published_without_digest(self):
        """Negative test: published artifact without sha256 digest fails invariant check."""
        data = copy.deepcopy(self.canonical_data)
        data["components"]["backend"]["artifacts"]["api"]["digest"] = None
        path = self.write_manifest(data)
        with self.assertRaises(ValueError) as ctx:
            validate_manifest(path)
        self.assertIn("Published artifact", str(ctx.exception))
        self.assertEqual(main([str(path)]), 1)

    def test_negative_pending_with_fake_digest(self):
        """Negative test: pending or blocked artifact with a fake digest fails invariant check."""
        data = copy.deepcopy(self.canonical_data)
        data["components"]["aiService"]["artifacts"]["aiService"]["digest"] = "sha256:" + "a" * 64
        path = self.write_manifest(data)
        with self.assertRaises(ValueError) as ctx:
            validate_manifest(path)
        self.assertIn("Pending artifact", str(ctx.exception))
        self.assertEqual(main([str(path)]), 1)

    def test_negative_tag_mismatch_with_build_commit(self):
        """Negative test: artifact tag not matching sha-{buildCommit} fails invariant check."""
        data = copy.deepcopy(self.canonical_data)
        data["components"]["backend"]["artifacts"]["api"]["tag"] = "sha-0000000000000000000000000000000000000000"
        path = self.write_manifest(data)
        with self.assertRaises(ValueError) as ctx:
            validate_manifest(path)
        self.assertIn("Tag mismatch", str(ctx.exception))
        self.assertEqual(main([str(path)]), 1)

    def test_negative_unpinned_third_party_dependency(self):
        """Negative test: unpinned third-party image missing @sha256: fails invariant check."""
        data = copy.deepcopy(self.canonical_data)
        data["thirdPartyDependencies"]["postgres"] = "pgvector/pgvector:latest"
        path = self.write_manifest(data)
        with self.assertRaises(ValueError) as ctx:
            validate_manifest(path)
        self.assertIn("must be pinned with @sha256:", str(ctx.exception))
        self.assertEqual(main([str(path)]), 1)

    def test_negative_missing_tool_purpose(self):
        """Negative test: missing database toolPurpose fails validation."""
        data = copy.deepcopy(self.canonical_data)
        del data["databaseMigration"]["toolPurpose"]
        path = self.write_manifest(data)
        with self.assertRaises(ValueError) as ctx:
            validate_manifest(path)
        self.assertTrue(
            "validation failed" in str(ctx.exception).lower() or "toolpurpose" in str(ctx.exception).lower()
        )
        self.assertEqual(main([str(path)]), 1)


if __name__ == "__main__":
    unittest.main()
