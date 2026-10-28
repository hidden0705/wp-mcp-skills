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
