# Security policy

## What this repository distributes

Markdown playbooks that an administrator-level AI agent reads and follows. A
malicious playbook is not "just text": it can tell the agent to install a plugin,
change a payment setting, export the database or hand credentials to an external
host.

## Report a bad playbook

Open a private security advisory on this repository
(**Security → Advisories → New draft security advisory**) or email the maintainer
listed on the GitHub profile. Include:

- the slug and the exact lines that are dangerous;
- what an agent would do if it followed them;
- whether the playbook is already published in the feed.

Do not open a public issue for an exploitable playbook. We will tombstone it, ship
a new signed manifest, and note the removal in the advisory.

## Controls

| Control | What it does |
| --- | --- |
| Human review | Every pull request is reviewed before merge |
| CI validation | Blocks secrets, emails, destructive shell patterns and malformed front matter |
| Signed feed | The manifest is signed with an offline RSA-3072 key; the plugin refuses an invalid signature |
| Per-file hashes | A changed playbook fails the hash check and is not installed |
| Tombstones | Removed playbooks are deleted from installs |
| No bundled overrides | A community playbook cannot replace a bundled one without an explicit `override` review |
| Kill switch | A site can disable the feed with `WPMCP_SKILLS_FEED` |

## Out of scope

- Vulnerabilities in WordPress, WooCommerce, Elementor or another plugin.
- A site that deliberately opts into an unreviewed private feed.
- An administrator who follows a playbook that was correctly reviewed but makes a
  bad operational decision.
