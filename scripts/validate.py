#!/usr/bin/env python3
"""Validate every playbook in skills/.

Exit code 1 on an error. Warnings are printed as GitHub annotations so a
reviewer sees them in the pull request.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
TOMBSTONES = ROOT / "tombstones.json"

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
CATEGORIES = {"Core", "Operations", "Growth", "WooCommerce", "Elementor"}
REQUIRED = ("title", "category", "summary")
ALLOWED_KEYS = {
    "title",
    "category",
    "summary",
    "author",
    "license",
    "updated",
    "version",
    "override",
}
DATE_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
URL_RE = re.compile(r"https?://([A-Za-z0-9.-]+)")

SECRET_PATTERNS = [
    (re.compile(r"ghp_[A-Za-z0-9]{20,}"), "a GitHub personal access token"),
    (re.compile(r"github_pat_[A-Za-z0-9_]{20,}"), "a GitHub fine-grained token"),
    (re.compile(r"sk_live_[A-Za-z0-9]{10,}"), "a live Stripe key"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "an AWS access key"),
    (re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"), "a Slack token"),
    (re.compile(r"AIza[0-9A-Za-z_-]{35}"), "a Google API key"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "a private key"),
    (
        re.compile(r"(?i)\b(password|passwd|secret|api[_-]?key)\s*[:=]\s*['\"][^'\"]{6,}['\"]"),
        "a hard-coded secret",
    ),
]

DANGEROUS_PATTERNS = [
    (re.compile(r"\bdb\s+drop\b", re.I), "`wp db drop` destroys the database"),
    (re.compile(r"\bDROP\s+TABLE\b", re.I), "DROP TABLE destroys data"),
    (re.compile(r"rm\s+-rf\s+/(?:\s|$)", re.I), "`rm -rf /` destroys the server"),
    (re.compile(r"curl[^\n|]*\|\s*(?:ba)?sh", re.I), "piping curl into a shell"),
    (re.compile(r"wget[^\n|]*\|\s*(?:ba)?sh", re.I), "piping wget into a shell"),
    (re.compile(r"eval\s*\(\s*base64_decode", re.I), "eval(base64_decode()) hides code"),
    (re.compile(r"chmod\s+777\s+/"), "world-writable root path"),
]

SOFT_PATTERNS = [
    (re.compile(r"\bwp\s+eval\b"), "`wp eval` executes PHP; make the need explicit"),
    (re.compile(r"\bsearch-replace\b"), "search-replace rewrites data; document --dry-run"),
    (re.compile(r"--force\b"), "--force skips a safeguard; explain why it is needed"),
]

# Documentation hosts a playbook may link to. Anything else is a warning so a
# reviewer can catch a real customer domain before it is published.
ALLOWED_HOSTS = {
    "example.com",
    "example.org",
    "example.net",
    "example.test",
    "localhost",
    "127.0.0.1",
    "wordpress.org",
    "developer.wordpress.org",
    "make.wordpress.org",
    "api.wordpress.org",
    "woocommerce.com",
    "woocommerce.github.io",
    "elementor.com",
    "developers.elementor.com",
    "developer.mozilla.org",
    "w3.org",
    "schema.org",
    "developers.google.com",
    "support.google.com",
    "pagespeed.web.dev",
    "web.dev",
    "github.com",
    "raw.githubusercontent.com",
    "php.net",
    "nginx.org",
    "httpd.apache.org",
    "mariadb.com",
    "dev.mysql.com",
    "letsencrypt.org",
    "wordfence.com",
    "stripe.com",
    "docs.stripe.com",
    "paypal.com",
    "developer.paypal.com",
    "cloudflare.com",
    "developers.cloudflare.com",
    "wp-cli.org",
}


def parse_front_matter(text: str) -> tuple[dict[str, str], str]:
    """Return (meta, body). Supports the small YAML subset the feed uses."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if not text.startswith("---"):
        raise ValueError("file must start with '---' front matter")
    end = text.find("\n---", 3)
    if end == -1:
        raise ValueError("front matter has no closing '---' line")
    head = text[3:end]
    body = text[end + 4 :].lstrip("\n")
    meta: dict[str, str] = {}
    for number, line in enumerate(head.splitlines(), start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"line {number}: expected 'key: value'")
        key, value = line.split(":", 1)
        key = key.strip()
        if key in meta:
            raise ValueError(f"line {number}: duplicate key '{key}'")
        meta[key] = value.strip().strip("\"'")
    return meta, body


def validate_skill(path: Path) -> tuple[list[str], list[str], dict[str, str], str]:
    errors: list[str] = []
    warnings: list[str] = []
    meta: dict[str, str] = {}
    body = ""
    slug = path.stem

    if not SLUG_RE.match(slug):
        errors.append(f"filename '{path.name}' is not a valid slug (a-z, 0-9, -)")

    try:
        meta, body = parse_front_matter(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        return [str(exc)], [], {}, ""

    for key in REQUIRED:
        if not meta.get(key):
            errors.append(f"front matter is missing '{key}'")
    for key in meta:
        if key not in ALLOWED_KEYS:
            errors.append(f"unknown front matter key '{key}'")

    title = meta.get("title", "")
    summary = meta.get("summary", "")
    category = meta.get("category", "")
    if title and not 3 <= len(title) <= 80:
        errors.append("title must be 3-80 characters")
    if summary and not 20 <= len(summary) <= 200:
        errors.append("summary must be 20-200 characters")
    if category and category not in CATEGORIES:
        errors.append(f"category '{category}' is not one of: {', '.join(sorted(CATEGORIES))}")
    if meta.get("license") and meta["license"] != "CC-BY-4.0":
        errors.append("license must be CC-BY-4.0")
    if meta.get("updated") and not DATE_RE.match(meta["updated"]):
        errors.append("updated must be YYYY-MM-DD")
    if meta.get("version") and not meta["version"].isdigit():
        errors.append("version must be a positive integer")
    if meta.get("override") and meta["override"].lower() not in {"true", "false"}:
        errors.append("override must be true or false")

    if not body.startswith("# "):
        errors.append("body must start with a '# ' heading")
    if not 200 <= len(body) <= 12000:
        errors.append(f"body is {len(body)} characters; the limit is 200-12000")

    full = path.read_text(encoding="utf-8")
    for pattern, label in SECRET_PATTERNS:
        if pattern.search(full):
            errors.append(f"looks like {label}")
    for pattern, label in DANGEROUS_PATTERNS:
        if pattern.search(full):
            errors.append(f"blocked: {label}")
    for pattern, label in SOFT_PATTERNS:
        if pattern.search(full):
            warnings.append(label)

    for match in EMAIL_RE.finditer(full):
        address = match.group(0)
        if not address.endswith(("@example.com", "@example.org", "@example.net", "@example.test")):
            errors.append(f"email address '{address}' must not be published")

    for host in URL_RE.findall(full):
        clean = host.lower().rstrip(".")
        if clean in ALLOWED_HOSTS or clean.endswith(".example.com"):
            continue
        warnings.append(f"non-allowlisted domain in a URL: {host}")

    return errors, warnings, meta, body


def load_tombstones() -> list[str]:
    if not TOMBSTONES.is_file():
        return []
    data = json.loads(TOMBSTONES.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("tombstones.json must be a JSON array of slugs")
    return [str(item) for item in data]


def validate_all() -> tuple[int, int]:
    files = sorted(SKILLS_DIR.glob("*.md"))
    errors_total = 0
    warnings_total = 0
    slugs: set[str] = set()

    if not files:
        print("::error::skills/ is empty")
        return 1, 0

    for path in files:
        if path.stem in slugs:
            print(f"::error file={path}::duplicate slug '{path.stem}'")
            errors_total += 1
        slugs.add(path.stem)
        errors, warnings, _meta, _body = validate_skill(path)
        for message in errors:
            print(f"::error file={path}::{message}")
        for message in warnings:
            print(f"::warning file={path}::{message}")
        if errors:
            print(f"{path.name}: {len(errors)} error(s), {len(warnings)} warning(s)")
        errors_total += len(errors)
        warnings_total += len(warnings)

    try:
        tombstones = load_tombstones()
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"::error file=tombstones.json::{exc}")
        return errors_total + 1, warnings_total
    for slug in tombstones:
        if not SLUG_RE.match(slug):
            print(f"::error file=tombstones.json::'{slug}' is not a valid slug")
            errors_total += 1
        if slug in slugs:
            print(f"::error file=tombstones.json::'{slug}' is tombstoned but still present in skills/")
            errors_total += 1

    print(f"validated {len(files)} playbook(s): {errors_total} error(s), {warnings_total} warning(s)")
    return errors_total, warnings_total


if __name__ == "__main__":
    errors, _warnings = validate_all()
    sys.exit(1 if errors else 0)
