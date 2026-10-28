---
title: Local SEO and Google Business Profile
category: Growth
summary: Build a location page and Google Business Profile that rank locally — NAP consistency, LocalBusiness schema, categories, service areas, reviews and tracking.
author: hidden0705
license: CC-BY-4.0
updated: 2026-10-28
version: 1
---

# Local SEO and Google Business Profile

Local ranking is decided by relevance, distance and prominence. The site can win
relevance and prominence; distance is fixed. Do not promise a map-pack position.

## One page per real location

- A service-area business without a storefront gets one page per city only when it
  has a genuine presence or serves that city distinctly. Ten thin pages with the
  city name swapped are a doorway-page risk.
- A physical location gets its own page with the full address, hours, phone and
  directions.
- Each page needs unique content: staff, services, parking, accessibility,
  neighbourhood landmarks, photos. The template can be shared; the body cannot.

URL: `/locations/<city-slug>/` is easier to read than `/local-seo-city-1/`.

## NAP consistency

Name, address and phone must match the Google Business Profile exactly, including
suite numbers and abbreviations. Pick one format and use it on:

- the location page (visible text, not only an image);
- the footer or contact page;
- schema JSON-LD;
- Google Business Profile;
- the main citations (Apple Business Connect, Bing Places, relevant directories).

A different phone number on one citation is a common reason for a suspended or
merged profile.

## LocalBusiness schema

Put one JSON-LD block on the location page, not on every page of the site. Choose
the most specific type (`Dentist`, `Plumber`, `Restaurant`, `Store`) and include
only facts that are visible on the page.

```json
{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "name": "Example Studio",
  "url": "https://example.com/locations/example-city/",
  "telephone": "+1-555-0100",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "100 Example Street",
    "addressLocality": "Example City",
    "addressRegion": "EX",
    "postalCode": "00000",
    "addressCountry": "US"
  },
  "openingHoursSpecification": [{
    "@type": "OpeningHoursSpecification",
    "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    "opens": "09:00",
    "closes": "17:00"
  }]
}
```

Rules:

- Do not add `aggregateRating` unless the reviews are on your own site and visible.
- Do not add `geo` coordinates unless they are the actual location.
- `areaServed` is for service-area businesses; a storefront should still list the
  address.
- Validate with a schema validator and re-check after a theme or builder update.

## Google Business Profile

1. Claim and verify the profile at the address or by video for a service area.
2. Choose the primary category carefully; it carries the most weight. Add a few
   accurate secondary categories, not every category available.
3. Set hours, special hours and holiday hours. Wrong hours hurt conversions more
   than they hurt rankings.
4. Add services and products with short descriptions and prices where relevant.
5. Upload real photos regularly: exterior, interior, team, work. Avoid stock
   photos on the profile.
6. Use Posts for offers and events; they expire, so put a review cadence in place.
7. Answer questions and reviews. Never post a template reply that ignores what the
   reviewer wrote.

A service-area business hides the address and lists service areas. Do not add a
fake storefront to appear in the map pack; suspension is common and hard to undo.

## Reviews

- Ask after a completed job, in person or by a link that goes straight to the
  review form.
- Never gate reviews by asking only happy customers, and never buy reviews.
- Reply to negative reviews with facts and an offline contact route. Do not argue.
- Do not offer an incentive that violates the platform's policy.

## Tracking

Use one consistent UTM pattern so calls and form fills can be attributed:

```
https://example.com/book/?utm_source=google&utm_medium=organic&utm_campaign=gbp
```

For calls, use a call-tracking number only on the profile and keep the real number
on the site, or use the same number everywhere if tracking is not set up. A
different number on the profile and the site is a NAP mismatch.

Measure: profile views, calls, direction requests, website clicks, and form fills
per location. Rankings alone do not pay the rent.

## WordPress implementation notes

- Build location pages as pages, not posts, so they do not drift into the blog.
- Use a reusable block or template part for the address and hours; update it once.
- Keep the address in text, not inside an image or a map iframe.
- If a page builder stores the schema in a widget, confirm the JSON-LD appears in
  the rendered HTML, not only in the editor preview.
- A multilingual site needs one location page per language with `hreflang`
  pointing at the equivalent page, not at the homepage.

## Verification

- Fetch the location page and confirm the address, phone and hours appear in the
  HTML and match the profile.
- Validate the JSON-LD and confirm there is exactly one LocalBusiness block.
- Check the profile's address and phone against the page character by character.
- Submit the updated sitemap and request indexing for the changed location pages.
- After 2-4 weeks, compare profile actions and form fills, not just impressions.
