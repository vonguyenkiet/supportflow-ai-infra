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
        for ctype in ["baselineCommit", "buildCommit"]:
            sha = comp.get(ctype, "")
            if not re.fullmatch(r"[0-9a-f]{40}", sha):
                raise ValueError(f"Invalid full commit SHA for {comp_name}.{ctype}: {sha}")

    # Verify immutable image digests or tags format in artifacts
    for comp_name, comp in manifest["components"].items():
        for art_name, art in comp.get("artifacts", {}).items():
            img = art.get("image", "")
            if not img.startswith("ghcr.io/supportflow-ai/"):
                raise ValueError(f"Invalid image repository for {comp_name}.{art_name}: {img}")
            status = art.get("publicationStatus")
            digest = art.get("digest")
            if status == "published":
                if not digest or not digest.startswith("sha256:"):
                    raise ValueError(f"Published artifact {comp_name}.{art_name} must have a valid sha256 digest")
            elif status in ("pending", "blocked"):
                if digest is not None:
                    raise ValueError(f"{status.capitalize()} artifact {comp_name}.{art_name} must have null digest")

    # Third party digests
    for name, ref in manifest["thirdPartyDependencies"].items():
        if "@sha256:" not in ref:
            raise ValueError(f"Third-party image {name} must be pinned with @sha256: digest")

    print(f"Validation successful: {manifest_path.name} matches schema and release rules.")


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "releases" / "release-1.0.0-rc1.json"
    validate_manifest(target)
