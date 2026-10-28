---
title: WooCommerce Subscriptions and Memberships
category: WooCommerce
summary: Diagnose renewals, statuses, failed payments and member access in WooCommerce Subscriptions and Memberships without corrupting HPOS data.
author: hidden0705
license: CC-BY-4.0
updated: 2026-10-28
version: 1
---

# WooCommerce Subscriptions and Memberships

Subscriptions and Memberships add their own order types, statuses and access
rules on top of WooCommerce. The dangerous mistake is treating a subscription like
a normal order: editing status or dates directly in the database skips the hooks
that create renewal orders, revoke access, and notify the customer.

## Identify the stack before touching it

```bash
wp plugin list --fields=name,status,version | grep -Ei 'woocommerce|subscription|membership'
wp option get woocommerce_custom_orders_table_enabled
wp wc --user=1 subscription list --fields=id,status,next_payment_date --format=table
```

Notes:

- Subscriptions stores data in its own tables (`wp_woocommerce_subscriptions` is
  not the whole picture; HPOS uses `wp_wc_orders`, `wp_wc_orders_meta`).
- `woocommerce_custom_orders_table_enabled` = `yes` means HPOS is authoritative.
  Direct SQL against `wp_posts`/`wp_postmeta` will miss these orders.
- Memberships may be a separate plugin with its own plan and member tables, not
  only a Subscriptions add-on.

## Statuses that matter

| Status | Meaning | Access |
| --- | --- | --- |
| `active` | Paid and current | Yes |
| `on-hold` | Awaiting payment or manual review | Usually no |
| `pending-cancel` | Cancelled, paid until the end of the term | Until end date |
| `cancelled` | Ended | No |
| `expired` | End date passed | No |
| `switched` | Moved to another subscription | Follow the new one |

Do not invent a status. A typo writes an order status that no hook recognises and
the customer loses access with no email.

## A failed renewal, in order

1. Read the subscription and its related orders.
2. Check the gateway's own log for the transaction, not only WooCommerce's.
3. Confirm the renewal order exists and what status it has.
4. If the payment succeeded at the gateway but the order is unpaid, use the
   gateway's "capture" or the subscription's "retry renewal" action so the proper
   hooks run.
5. If the payment genuinely failed, let the retry schedule run or trigger a
   manual retry; do not mark it paid.

```bash
wp wc --user=1 subscription get <id> --fields=id,status,next_payment_date,end_date,billing_period
wp wc --user=1 shop_order list --parent=<subscription_id> --fields=id,status,date_created
```

WooCommerce's own CLI is preferable to SQL because it fires the CRUD hooks. If a
hook must be bypassed for a repair, take a database export first and record the
exact rows changed.

## Changing a renewal date

Use the subscription object's date setter (admin UI or a small, reviewed script
that calls `WC_Subscription::update_dates()`), not an `UPDATE` on meta. Changing
`_schedule_next_payment` alone leaves the action scheduler event pointing at the
old time, so the renewal fires twice or not at all.

After a date change:

```bash
wp action-scheduler run --hooks=woocommerce_scheduled_subscription_payment --due-now
```

Run only the specific hook, and only after verifying the pending action's
subscription ID.

## Memberships and access

- A membership plan grants roles or capabilities. Removing the plan should remove
  the role; a manual role removal can leave an active membership with no access.
- Check the user's roles and the membership record together:
  `wp user get <id> --fields=ID,user_login,roles`
- Rules can be content-based (page/category restrictions) or role-based. A page
  can be protected even when the member's role looks correct; inspect the plan's
  rules before changing the role.
- Cancelling a subscription does not always end a membership immediately. The
  membership may run to the paid-through date by design.

## Refunds and switches

- Refunding a renewal does not automatically cancel the subscription. Decide and
  document which one the customer asked for.
- An upgrade/downgrade creates a switched subscription and prorated charges. Do
  not edit the old subscription to look like the new one; the switch record is the
  audit trail.
- Test a switch on a test product with a test gateway before doing it for a
  customer.

## Verification

- The customer's My Account > Subscriptions page shows the expected status and
  next payment date.
- The related renewal order exists with a matching total and currency.
- The membership grants the expected content; open the protected page as that
  user, not as an administrator.
- The next scheduled action points at the same date the subscription shows.
- No duplicate renewal orders were created by a retry.

## Traps

- HPOS and the legacy posts table can disagree after a failed migration. Pick the
  authoritative store (`wp wc order list` uses HPOS when enabled) and do not write
  to the other one.
- A gateway that does not support automatic renewals will never create renewal
  orders; the subscription still shows `active`. Check the gateway's support flag
  before debugging WooCommerce.
- Deleting a user does not cancel their subscription. Cancel first, then decide
  what to do with the account and its orders.
- Bulk status changes in the admin list can skip per-subscription hooks. Use the
  edit screen or the CLI for one record at a time.
