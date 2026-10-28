#!/usr/bin/env python3
"""Build the signed-feed manifest from skills/.

The manifest is the only thing the plugin trusts after the signature check:
path, sha256 and size for every playbook, plus tombstones.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate  # noqa: E402


def build(out_dir: Path, base: str, min_plugin: str, generated: str | None) -> dict:
    errors = 0
    skills: dict[str, dict] = {}
    for path in sorted(validate.SKILLS_DIR.glob("*.md")):
        issues, warnings, meta, body = validate.validate_skill(path)
        for message in issues:
            print(f"error: {path.name}: {message}")
        for message in warnings:
            print(f"warning: {path.name}: {message}")
        if issues:
            errors += len(issues)
            continue
        raw = path.read_bytes()
        skills[path.stem] = {
            "title": meta["title"],
            "category": meta["category"],
            "summary": meta["summary"],
            "author": meta.get("author", "community"),
            "license": meta.get("license", "CC-BY-4.0"),
            "version": int(meta.get("version", "1")),
            "updated": meta.get("updated", datetime.now(timezone.utc).strftime("%Y-%m-%d")),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
            "path": f"skills/{path.name}",
        }
    if errors:
        raise SystemExit(f"refusing to build: {errors} validation error(s)")

    tombstones = set(validate.load_tombstones())
    overlap = tombstones.intersection(skills)
    if overlap:
        raise SystemExit("tombstoned slugs are still present: " + ", ".join(sorted(overlap)))

    manifest = {
        "schema": 1,
        "generated": generated or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "min_plugin": min_plugin,
        "base": base.rstrip("/") + "/",
        "skills": skills,
        "deleted": sorted(tombstones),
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / "manifest.json"
    target.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {target} ({target.stat().st_size} bytes, {len(skills)} skill(s), {len(tombstones)} tombstone(s))")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="dist")
    parser.add_argument("--base", default="https://raw.githubusercontent.com/hidden0705/wp-mcp-skills/main/")
    parser.add_argument("--min-plugin", default="2.7.0")
    parser.add_argument("--generated", default=None, help="ISO-8601 timestamp for reproducible builds")
    args = parser.parse_args()
    build(Path(args.out), args.base, args.min_plugin, args.generated)


if __name__ == "__main__":
    main()
