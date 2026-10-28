---
title: WordPress Multisite Operations
category: Core
summary: Work safely on a WordPress multisite network — per-site URLs, shared tables, network activation, domain mapping, backups and search-replace.
author: hidden0705
license: CC-BY-4.0
updated: 2026-10-28
version: 1
---

# WordPress Multisite Operations

A multisite is one WordPress install serving many sites from shared code and a
shared user table. Most commands that work on a single site need a `--url` flag
here, and a change made in the wrong place can affect every site on the network.

## First, confirm what you are on

```bash
wp core is-installed --network
wp site list --fields=blog_id,url,registered,last_updated --format=table
wp config get MULTISITE
wp config get SUBDOMAIN_INSTALL
```

`MULTISITE` true means the network is active. `SUBDOMAIN_INSTALL` true means sites
use subdomains; false means subdirectories. Never assume which one from the URL.

## The table map

| Table | Scope |
| --- | --- |
| `wp_users`, `wp_usermeta` | Network-wide |
| `wp_blogs`, `wp_site`, `wp_sitemeta` | Network control |
| `wp_<id>_options`, `wp_<id>_posts`, `wp_<id>_postmeta` | Per site |
| `wp_<id>_options` row `wp_<id>_user_roles` | Per-site roles |
| `wp_<id>_options` row `active_plugins` | Per-site plugin list |

A user is a member of a site only when they have a capability on it. Deleting a
user from the network removes them everywhere; removing them from one site uses
`wp user remove-cap` or the site's Users screen, not `wp user delete`.

## Run a command against one site

```bash
wp option get blogname --url=https://example.com/
wp plugin list --url=https://example.com/ --fields=name,status,version
wp theme list --url=https://example.com/
wp post list --url=https://example.com/ --post_type=page --fields=ID,post_title
```

Without `--url`, WP-CLI uses the main site. That is the most common way an agent
edits the wrong site and reports success.

## Plugins and themes

- Network activation (`wp plugin activate <slug> --network`) loads the plugin on
  every site. Use it for infrastructure (security, caching, MCP transport).
- Site activation loads it on one site only. Use it for business plugins whose
  data should not exist network-wide.
- `wp plugin list --status=network-active` shows the network set.
- A theme is network-enabled with `wp theme enable <slug> --network`, then
  activated per site. Enabling does not activate it anywhere.

Before network-activating a plugin, check for per-site options it writes and
whether its activation routine assumes a single site. Activate on a staging copy
of the network first when the plugin touches `wp_sitemeta` or creates tables.

## Domains and HTTPS

Domain mapping lives in `wp_blogs.domain` and `wp_blogs.path`, or in a mapping
plugin's own table. Change it with the mapping plugin's UI or WP-CLI command, not
with a direct `UPDATE`. After a domain change:

```bash
wp cache flush
wp rewrite flush --hard --url=https://example.com/
```

Check the canonical URL the site actually serves:

```bash
wp option get home --url=https://example.com/
wp option get siteurl --url=https://example.com/
```

Both should use the mapped domain and the scheme users see. A mismatch causes
redirect loops and mixed-content warnings.

## Search-replace on a network

Run it per site, with the site's own URL as both the scope and the replacement
target. A network-wide replace on shared tables can rewrite another site's
content.

```bash
wp search-replace 'https://old.example.com' 'https://new.example.com' \
  --url=https://new.example.com/ --all-tables-with-prefix --dry-run
```

Review the dry run, then repeat without `--dry-run`. Add `--skip-columns=guid`
unless the site intentionally stores full URLs in GUIDs (most do not). After the
replace, flush object cache and rewrite rules for that site, then fetch a page and
confirm the canonical, menu links and uploaded files all use the new domain.

## Backups

A network backup is not one database export. Capture:

1. The network database (`wp db export`), which includes every site's tables.
2. `wp-content/uploads` (shared by default, or per-site with a custom constant).
3. `wp-content/plugins`, `themes`, `mu-plugins`.
4. The mapping plugin's tables and any domain configuration outside WordPress.

Restore the whole set together. Restoring one site's tables into a network that
has moved on produces orphaned relationships and broken menus.

## Verification checklist

- `wp site list` still shows every site, with the expected URLs.
- Each edited site returns HTTP 200 over HTTPS.
- `wp option get home --url=...` matches the public URL.
- The network admin (`/wp-admin/network/`) loads and lists the same sites.
- No new rows in `wp_blogs` with an empty `last_updated` that you did not create.
- `wp plugin list --status=network-active` matches the intended network set.

## Traps

- `wp db export` on a huge network can time out. Use `--exclude_tables` for
  unrelated plugin logs, or dump per site with a table prefix filter.
- Deleting a site (`wp site delete`) is permanent after `--yes`; it drops that
  site's tables. Export first and confirm the blog ID twice.
- A super admin is not automatically a member of every site's roles, but has
  network-level capabilities. Test with a normal administrator account too.
- Cron is shared. One site's heavy job can delay every other site's scheduled
  tasks; check `wp cron event list` before blaming a plugin.
