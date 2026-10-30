import json
import re
import sys
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "release-manifest.schema.json"


def validate_manifest(manifest_path: Path):
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    # 1. JSON Schema Draft 2020-12 full schema validation
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(manifest), key=lambda e: e.path)
    if errors:
        error_msgs = "\n".join(f"  - {'/'.join(str(p) for p in err.path)}: {err.message}" for err in errors)
        raise ValueError(f"JSON Schema Draft 2020-12 validation failed for {manifest_path.name}:\n{error_msgs}")

    # 2. Check commit SHAs and workflow references
    for comp_name in ["backend", "web", "aiService", "infrastructure"]:
        comp = manifest["components"].get(comp_name)
        if not comp:
            raise ValueError(f"Missing component: {comp_name}")
        for ctype in ["baselineCommit", "sourceCommit", "buildCommit"]:
            sha = comp.get(ctype, "")
            if not re.fullmatch(r"[0-9a-f]{40}", sha):
                raise ValueError(f"Invalid full commit SHA for {comp_name}.{ctype}: {sha}")
        if not comp.get("workflowRunUrl") or not comp.get("workflowRunId"):
            raise ValueError(f"Missing workflowRunUrl or workflowRunId for {comp_name}")

    # 3. Verify immutable image digests and tag-to-buildCommit invariants in artifacts
    for comp_name, comp in manifest["components"].items():
        build_sha = comp["buildCommit"]
        expected_tag = f"sha-{build_sha}"
        for art_name, art in comp.get("artifacts", {}).items():
            img = art.get("image", "")
            if not img.startswith("ghcr.io/supportflow-ai/"):
                raise ValueError(f"Invalid image repository for {comp_name}.{art_name}: {img}")
            tag = art.get("tag", "")
            if tag != expected_tag:
                raise ValueError(f"Tag mismatch for {comp_name}.{art_name}: expected {expected_tag}, got {tag}")
            status = art.get("publicationStatus")
            digest = art.get("digest")
            if status == "published":
                if not digest or not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
                    raise ValueError(f"Published artifact {comp_name}.{art_name} must have a valid sha256:<64 hex> digest: {digest}")
            elif status in ("pending", "blocked"):
                if digest is not None:
                    raise ValueError(f"{status.capitalize()} artifact {comp_name}.{art_name} must have null digest")

    # 4. Third party digests
    for name, ref in manifest["thirdPartyDependencies"].items():
        if "@sha256:" not in ref:
            raise ValueError(f"Third-party image {name} must be pinned with @sha256: digest")

    # 5. Database tool purpose clarity
    db_tool = manifest.get("databaseMigration", {})
    if not db_tool.get("toolPurpose"):
        raise ValueError("databaseMigration.toolPurpose must clearly describe the migration/seeding tool")

    print(f"Validation successful: {manifest_path.name} matches JSON Schema Draft 2020-12 and release rules.")
    return manifest


def main(argv=None):
    target = Path(argv[0]) if argv else ROOT / "releases" / "release-1.0.0-rc1.json"
    try:
        validate_manifest(target)
        return 0
    except Exception as exc:
        print(f"VALIDATION FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
