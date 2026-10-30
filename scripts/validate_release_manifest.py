import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "release-manifest.schema.json"


def validate_manifest(manifest_path: Path):
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    # Required top-level keys
    for key in schema["required"]:
        if key not in manifest:
            raise ValueError(f"Missing required key: {key}")

    # Check commit SHAs
    for comp_name in ["backend", "web", "aiService", "infrastructure"]:
        comp = manifest["components"].get(comp_name)
        if not comp:
            raise ValueError(f"Missing component: {comp_name}")
        commit = comp.get("commit", "")
        if not re.fullmatch(r"[0-9a-f]{40}", commit):
            raise ValueError(f"Invalid full commit SHA for {comp_name}: {commit}")

    # Verify immutable image digests or tags format
    for comp_name, comp in manifest["components"].items():
        for img_role, img_ref in comp.get("images", {}).items():
            if not isinstance(img_ref, str) or not img_ref.startswith("ghcr.io/supportflow-ai/"):
                raise ValueError(f"Invalid image repository for {comp_name}.{img_role}: {img_ref}")

    # Third party digests
    for name, ref in manifest["thirdPartyDependencies"].items():
        if "@sha256:" not in ref:
            raise ValueError(f"Third-party image {name} must be pinned with @sha256: digest")

    print(f"Validation successful: {manifest_path.name} matches schema and release rules.")


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "releases" / "release-1.0.0-rc1.json"
    validate_manifest(target)
