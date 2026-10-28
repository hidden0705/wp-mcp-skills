# WP MCP Community Skills

Shared playbooks for the [WP MCP Abilities](https://github.com/hidden0705/wp-mcp-abilities)
WordPress plugin.

A skill is a markdown file that tells an AI agent how to do one job on a
WordPress site: the commands, the order to run them in, the traps that break a
site, and how to verify the result. The plugin ships 46 playbooks; this
repository is the **extra** library that every install can pull and that grows
from what agents learn on real sites.

## What is here

```
skills/<slug>.md          one playbook per file
schemas/skill.schema.json front matter contract
tombstones.json           slugs removed from the feed
scripts/                  validation and manifest build
```

The plugin reads a signed manifest from
`https://github.com/hidden0705/wp-mcp-skills/releases/download/feed/manifest.json`.
Every installed site checks it twice a day and downloads only the playbooks that
changed.

## Precedence

```
site playbook (wp-content/wpmcp-skills)
  > team feed (private, configured by the site)
    > this community feed
      > bundled playbooks (shipped with the plugin)
```

A site can always shadow a community playbook with its own version of the same
slug. Community playbooks cannot override a bundled playbook unless the manifest
marks them `override`, which review has to approve.

## Contribute

1. Copy an existing file in `skills/` and change the front matter.
2. Keep it generic: `example.com`, no real domains, no credentials, no customer
   data, no site-specific paths.
3. Run `python3 scripts/validate.py` locally.
4. Open a pull request. CI validates again; a maintainer reviews for correctness
   and safety before merge.
5. On merge the feed is rebuilt, signed and published automatically.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full rules and the format.

## Safety

Playbooks are instructions that an administrator-level agent will follow. That
makes this repository a supply-chain surface, so:

- Every merge is reviewed by a human.
- The published manifest is signed with an offline RSA key; the plugin refuses a
  manifest whose signature does not verify.
- Every playbook is hashed; a modified file is rejected.
- Removed playbooks are tombstoned and deleted from installs.
- A playbook cannot override a bundled playbook without an explicit review flag.

Report a malicious or dangerous playbook through [SECURITY.md](SECURITY.md).

## License

Playbooks are licensed under [CC BY 4.0](LICENSE). By contributing you agree to
license your contribution under the same terms.
