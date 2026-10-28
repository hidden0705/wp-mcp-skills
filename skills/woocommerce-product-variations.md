---
title: WooCommerce Product Variations
category: WooCommerce
summary: Build, import and repair variable products — attributes, variation generation, per-variation price and stock, bulk updates, cache sync and front-end verification.
author: hidden0705
license: CC-BY-4.0
updated: 2026-10-28
version: 1
---

# WooCommerce Product Variations

A variable product is one parent product plus a variation for every combination
of its attributes. Most variation bugs come from editing the parent when the
value lives on the variation, or from changing variation data without letting
WooCommerce resync its price and stock caches.

## How the data is stored

- The parent is a `product` post with `product_type = variable`.
- Each variation is a `product_variation` post whose `post_parent` is the parent.
- Global attributes (`pa_color`, `pa_size`) are taxonomies; their terms are the
  values. Custom attributes are stored in the parent's `_product_attributes`
  meta and their values are plain strings on the variation.
- A variation stores its chosen values in meta such as
  `attribute_pa_color` or `attribute_color` (the `attribute_` prefix plus the
  attribute name). A missing or misspelled key means the variation never
  matches a dropdown selection.
- HPOS changes how **orders** are stored, not products or variations. Variation
  data stays in `wp_posts` and `wp_postmeta` even with HPOS enabled.

Check the type before anything else:

```bash
wp post get <id> --field=post_type
wp post meta get <id> _product_attributes --format=json
wp wc --user=1 product get <id> --fields=id,name,type,attributes --format=json
```

## Prices live on the variation

For a variable product the parent's `regular_price` and `sale_price` are not the
price a customer pays; WooCommerce derives a range from the variations. Setting a
price on the parent changes nothing on the front end.

```bash
wp wc --user=1 product_variation list <parent_id> \
  --fields=id,sku,regular_price,sale_price,stock_status,stock_quantity --format=table
```

Every purchasable variation needs a price. A variation with an empty price is
skipped in the range and cannot be added to the cart, even though it appears in
the dropdown.

## Stock: pick one level

- **Manage stock at variation level** (the usual choice): set
  `manage_stock = true` and `stock_quantity` on each variation. The parent shows
  the sum.
- **Manage stock at parent level**: the parent tracks one pool and variations
  inherit it. Do not set quantities on both levels; the numbers disagree.

```bash
wp wc --user=1 product_variation update <parent_id> <variation_id> \
  --manage_stock=true --stock_quantity=12
```

`stock_status` is derived from the quantity when stock management is on. Setting
`stock_status=instock` while the quantity is 0 produces a product that can be
ordered and then fails at checkout.

## Creating variations

In the admin, define the attributes on the **Product data → Attributes** tab,
tick "Used for variations", save, then use **Variations → Generate variations**.
Generating again does not duplicate existing combinations; it adds the missing
ones.

Programmatically, create each variation explicitly so you control the SKU and
price:

```bash
wp wc --user=1 product_variation create <parent_id> \
  --attributes='[{"id":1,"option":"Blue"},{"id":2,"option":"Large"}]' \
  --regular_price=29.00 --sku=SHIRT-BLUE-L --manage_stock=true --stock_quantity=5
```

For bulk work use the REST batch endpoint instead of one request per variation:

```
POST /wp-json/wc/v3/products/<parent_id>/variations/batch
{
  "update": [
    { "id": 123, "regular_price": "31.00", "stock_quantity": 8 },
    { "id": 124, "sale_price": "25.00" }
  ]
}
```

The batch endpoint runs each item through the CRUD layer, so caches and hooks
stay correct. Direct `update_post_meta` calls do not.

## CSV import

Variation rows in the WooCommerce CSV importer are separate rows with:

- `Type` = `variation`
- `Parent` = the parent product ID or SKU
- one column per attribute, named exactly like the attribute (`Attribute 1 name`
  / `Attribute 1 value(s)` for custom attributes, or `pa_color` for global ones)
- `SKU`, `Regular price`, `Sale price`, `Stock`, `Manage stock`

Import the parent first, then the variations. A variation row whose attribute
value is not a term of the global attribute is rejected or imported without the
link; create the terms first.

## After any direct data change, resync

If a repair script must write variation meta directly, finish with the product
save so WooCommerce rebuilds its caches:

```bash
wp eval '
$parent = wc_get_product( 123 );
if ( $parent && $parent->is_type( "variable" ) ) {
    WC_Product_Variable::sync( 123 );
    wc_delete_product_transients( 123 );
    $parent->save();
}
echo "synced\n";
'
```

Without this, the price range, "out of stock" badge and variation dropdown can
show stale values until the next scheduled sync.

## Verification

1. Open the product page and confirm every attribute dropdown lists the expected
   terms.
2. Select each combination and confirm the price and stock message change.
3. Add the cheapest and the most expensive variation to the cart; the cart line
   must show the chosen attributes and the right price.
4. Place a test order for one variation and confirm the order line names the
   variation, not only the parent.
5. Check that no two variations share a SKU:

   ```bash
   wp wc --user=1 product_variation list <parent_id> --fields=id,sku --format=csv
   ```

6. Confirm the parent shows the expected price range, not "Read more" (which
   usually means every variation is out of stock or unpriced).

## Traps

- Deleting a variation does not delete its image attachment; clean orphans
  separately.
- Changing an attribute from custom to global (or the reverse) orphans the old
  `attribute_*` meta. Recreate the variations instead of patching meta by hand.
- A sale price higher than the regular price silently disables the sale.
- Bulk-editing variations in the admin list can overwrite per-variation prices
  with a blank value; check the list after a bulk save.
- Caches: a page cache or CDN can keep serving the old price range after a
  correct database change. Purge the product page cache and test logged out.
