# Contributing a playbook

## Before you write

- One file, one job. A playbook called "WooCommerce" is not reviewable; "WooCommerce
  Subscriptions renewals" is.
- Write for an agent that has never seen the site. Assume it knows WordPress, not
  your setup.
- Prefer the abilities the plugin already exposes (`rest-request`, `files`,
  `elementor`, `skill-write`) and WP-CLI only where it is the right tool.
- Verify claims. A wrong command in a playbook is worse than no playbook.

## File format

`skills/<slug>.md`, slug matches `^[a-z0-9][a-z0-9-]*$`.

```markdown
---
title: Human Readable Title
category: Core
summary: One sentence an agent can use to decide whether to load this file.
author: your-handle
license: CC-BY-4.0
updated: 2026-10-28
version: 1
---

# Human Readable Title

Body: steps, commands, traps, verification.
```

Rules:

- `title`, `category` and `summary` are required.
- Categories: `Core`, `Operations`, `Growth`, `WooCommerce`, `Elementor`.
- Body must start with a `# ` heading and be 200–12,000 characters.
- Use fenced code blocks for commands.
- No credentials, tokens, private keys, emails, customer data or real domains.
  Use `example.com` and `example.test`.
- No instructions to disable safety controls, skip backups or run unreviewed code
  from the internet.
- A playbook that needs a destructive step must say how to back up first and how
  to verify afterwards.

## Safety review

CI blocks obvious problems (secrets, emails, `db drop`, `DROP TABLE`,
`rm -rf /`, piping a download into a shell). Reviewers also check:

- Does the playbook work on a stock WordPress install?
- Does it name a plugin or theme that does not exist?
- Could a prompt injection hide in a quoted instruction or a URL?
- Does it tell the agent to skip a backup or a `confirm: true` gate?

## Exporting from a WordPress site

If the playbook was written on a live site with `wpmcp/skill-write`, export it
instead of copying it by hand. The command scrubs the site out of the text and
writes the front matter this repository expects.

```bash
wp wpmcp export --author=your-handle --dry-run
wp wpmcp export --author=your-handle
```

Output lands in `wp-content/wpmcp-export/`. It replaces your domain and host with
`example.com`, every email with `admin@example.com`, and absolute paths with
`/path/to/wordpress/...`. A file that looks like it contains a token or password is
skipped with a warning, and a slug that already exists in the plugin's bundled
library is skipped unless you pass `--allow-override` (which writes
`override: true` and needs a maintainer's agreement in the PR).

Review the scrub result before you commit. The command is a safety net, not a
review: it cannot tell whether a sentence is correct, and it cannot see a secret
that does not match a known pattern.

## Local checks

```bash
python3 scripts/validate.py
python3 scripts/build_feed.py --out /tmp/wp-mcp-feed
cat /tmp/wp-mcp-feed/manifest.json
```

`build_feed.py` writes a manifest with sha256 for every file; the CI job signs it
with a key that never leaves the maintainer's machine and the repository secret.

## Removals

To remove a published playbook, delete the file and add its slug to
`tombstones.json`. The next feed build advertises it as deleted and installs drop
their community copy. Never reuse a tombstoned slug for different content; pick a
new slug.

## License

By opening a pull request you agree to license the contribution under CC BY 4.0.
