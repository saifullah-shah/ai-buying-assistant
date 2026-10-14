# Pakistan-First Product Data Source Research — D-008

**Research checked:** 2026-10-13  
**Decision status:** D-008 remains OPEN; no provider approved.  
**Market decision:** D-007 remains OPEN / provisional. Pakistan is the research priority only, not an accepted launch-market decision.

## Executive summary

1. **Curated demo dataset:** A synthetic, explicitly demo-only Pakistan laptop fixture has been prepared separately. Its model names, specifications, sellers, prices, and availability are all illustrative. It is useful for testing data flow, hard filters, ranking, and explanation behavior, but it is not evidence of Pakistan market prices.
2. **Daraz Open Platform / consumer site:** The Open Platform documentation confirms a Pakistan API base (`api.daraz.pk`) and describes app registration, app keys/tokens, and seller authorization; visible API examples include seller-side product management. Separately, Daraz Pakistan's consumer Terms and Conditions explicitly prohibit collection/use of product listings, descriptions, or prices and data-mining/robots absent express written permission. This is a **material blocker** for any consumer-site collection. Do not scrape or reuse listings/prices unless Daraz gives explicit written permission or an applicable approved program agreement clearly grants those rights.
3. **Daraz affiliate route:** Daraz Pakistan publicly links an affiliate program, and an affiliate landing page is discoverable. Public visibility alone does not verify that an account can join, that a laptop product feed/API is available, or the rights for caching, historical prices, images, and display. Request official program documentation and written/account-specific confirmation.
4. **PriceOye:** Its official Fair Use page identifies bots/scripts among patterns that can trigger restrictions. Do not scrape or automate PriceOye for this project without explicit written permission and clear terms.
5. **Direct retailer/manufacturer route:** No retailer feed/API or reuse grant has been verified in this research pass. Direct permission and manufacturer specifications/manuals remain candidate routes; a manufacturer spec page is evidence for specs, not for Pakistan seller price, availability, or reuse of images.

## Source evaluation records

### Source: Daraz Open Platform (Pakistan API)

- Checked on (UTC date): 2026-10-13
- Official documentation URLs:
  - https://open.daraz.com/
  - https://open.daraz.com/doc/doc.htm?docId=118729&nodeId=27493
  - https://open.daraz.com/doc/api.htm
  - https://pages.daraz.pk/wow/gcp/route/daraz/pk/upr/router?at_iframe=1&data_prefetch=true&hybrid=1&prefetch_replace=1&wh_pid=/lazada/channel/pk/terms-and-condition/user-terms-and-conditions (Daraz Pakistan consumer Terms and Conditions; see “License to Access the Site”, especially clauses on collection/use of product listings, descriptions, or prices and data-mining/robots)
- Supported market(s): Documentation lists Pakistan API base `https://api.daraz.pk/rest`.
- Categories covered: Platform presents multiple e-commerce API areas; category coverage for buyer-side laptop discovery was not established.
- Access/approval steps: Official getting-started guide describes registering an app, obtaining an app key, and access tokens; seller-sensitive data access involves seller authorization. Account eligibility and permissions for the intended use remain unverified.
- Relevant endpoints/feed format: The API reference surfaced seller-management endpoints such as product creation and price/quantity updates. No confirmed public endpoint for general buyer-side product discovery was established in this pass.
- Fields provided: Seller product APIs include product attributes, images, SKU, price, and quantity in examples; that does not prove these fields are available for arbitrary third-party seller offers.
- Price and availability freshness: Not established for a consumer product-search use case.
- Request quotas/cost: Not verified.
- Storage/cache/history rules: Not verified for any API/affiliate program. Consumer-site terms state that the license does not include collection/use of listings/descriptions/prices and restrict downloading/copying; do not infer caching/history rights.
- Image and display/reuse permissions: Not verified.
- Affiliate rules and attribution: Separate affiliate route exists publicly, but exact terms, feed access, attribution, and eligibility are not verified.
- Known gaps or errors: The API reference reviewed appears seller-management-oriented; do not infer public marketplace-wide search access. The separate consumer-site terms prohibit collection/use of product listings, descriptions, or prices and data-mining/robots without express written consent. An API/affiliate route must be confirmed to be covered by applicable terms and permission.
- Minimal test performed and evidence: Documentation reviewed only; no account/app registration, authenticated call, or sample response test performed.
- Status: `UNVERIFIED`
- Next action: Obtain written confirmation from Daraz or an applicable approved program agreement that explicitly authorizes third-party consumer comparison/recommendation use. Confirm laptop offer access, permitted fields, refresh cadence, storage/history, image display, outbound links, and affiliate conditions before any integration.

### Source: Daraz Pakistan affiliate program

- Checked on (UTC date): 2026-10-13
- Official documentation URL:
  - https://www.daraz.pk/home (footer links to “Join Daraz Affiliate Program”)
  - https://pages.daraz.pk/wow/gcp/route/daraz/pk/upr/router?at_iframe=1&data_prefetch=true&hybrid=1&laz_event_id=150_1778691774686_28787&laz_prefetch_id=laz_pre_163722423046755&prefetch_replace=1&scm=20140773.channel.affiliate.d&web_view_type=pre_hot&wh_pid=%2Flazada%2Fchannel%2Fpk%2Fdaraz-affiliates%2Fdaraz-affiliates
- Supported market(s): Pakistan affiliate landing page is visible.
- Categories covered: General merchandise appears on the landing page; laptop feed coverage not confirmed.
- Access/approval steps: Application and acceptance details not verified.
- Relevant endpoints/feed format: No official machine-readable product feed/API documentation verified.
- Fields provided: Not verified.
- Price and availability freshness: Not verified.
- Request quotas/cost: Not verified.
- Storage/cache/history rules: Not verified.
- Image and display/reuse permissions: Not verified.
- Affiliate rules and attribution: Exact terms, eligible publishers, commission rules, attribution links, and feed permissions remain unverified.
- Known gaps or errors: A public affiliate page is not proof of account eligibility or product-feed access.
- Minimal test performed and evidence: Public page discovery only; no affiliate account or feed tested.
- Status: `UNVERIFIED`
- Next action: Obtain the current official affiliate terms and account-specific confirmation of laptop feed access, allowed display, caching/history, image use, link requirements, and commission/attribution rules.

### Source: PriceOye

- Checked on (UTC date): 2026-10-13
- Official documentation URL: https://priceoye.pk/fair-usage
- Supported market(s): Pakistan-facing retailer.
- Categories covered: Not assessed for this research task.
- Access/approval steps: No data API/feed access was verified.
- Relevant endpoints/feed format: None verified.
- Fields provided: Its public consumer pages show product and price information, but no permitted programmatic feed was verified.
- Price and availability freshness: The page says price/stock information is informational and may change without notice.
- Request quotas/cost: No API terms or quota information verified.
- Storage/cache/history rules: Not verified.
- Image and display/reuse permissions: Not verified.
- Affiliate rules and attribution: Not verified.
- Known gaps or errors: The official Fair Use page lists bots/scripts among suspicious behavior that may result in account restrictions. This is a reason not to scrape or automate without explicit permission; it is not a complete analysis of all site terms.
- Minimal test performed and evidence: Policy page reviewed; no crawling or automated requests performed.
- Status: `UNVERIFIED` (for a data-provider integration); do not scrape absent permission.
- Next action: Ask for an official partner/feed/API route or written permission and complete terms.

## Pakistan-first comparison

| Route | What public evidence supports | Main blocker | Current disposition |
|---|---|---|---|
| Synthetic curated JSON/CSV | Can support prototype/testing with explicit provenance and `is_demo=true` | Not live market data; manual maintenance does not scale | Use for demo/testing only |
| Daraz Open Platform / site | Official app/API docs and Pakistan base URL exist; seller product-management operations are documented. Consumer terms expressly restrict collection/use of listing data and data-mining without written consent. | Need an approved endpoint/program and explicit permission for consumer comparison use, plus storage/display terms | Do not scrape; seek written permission; not approved |
| Daraz affiliate program | Public Pakistan affiliate landing page exists | Eligibility, laptop feed/API, field rights, cache/history and image terms unverified | Investigate official terms; not approved |
| PriceOye | Public product pages and Fair Use policy exist | No permitted feed/API confirmed; policy flags bots/scripts as risk | No scraping; request permission |
| Direct retailer partnership | Could provide local price/stock and seller metadata if agreed | No partner agreement/feed verified | Candidate only |
| Manufacturer specifications | Potential authoritative product-specification evidence | Does not provide local seller offer/price; reuse rights still need checking | Use for factual specs only after per-page review |

## Dataset notes

See `laptop_demo_dataset_pk.json` and `laptop_demo_dataset_pk.csv`.

- All records set `is_demo=true`.
- All brand/model names are fictional placeholders.
- All specifications and PKR prices are illustrative, not real-world facts.
- No product image URLs or external seller URLs are included.
- Do not use the fixture to infer current market prices, stock, or seller quality.
- Before adapting it to the M1 loader, map these fields to the exact `Product`, `SellerOffer`, `PriceObservation`, `ProductSpecification`, `SourceRef`, and `Evidence` constructors and run the loader's demo gate/tests.

## Outstanding evidence needed before a provider can be approved

- Current official terms/developer agreement and data protection policy.
- Written/account-specific eligibility and approval.
- A documented endpoint/feed that actually returns Pakistan laptop offers from the intended sellers.
- Sample response with secrets removed, proving required fields and timestamps.
- Confirmed display, storage/cache duration, historical price, image, and outbound-link permissions.
- Rate limits, quotas, costs, failure behavior, and correction/deletion handling.
- A repeatable freshness check and a successful minimal test.

## Decision state

- **D-008:** `OPEN` — research underway; no provider approved.
- **D-007:** `OPEN` — Pakistan is the research priority, not yet the accepted launch market.
