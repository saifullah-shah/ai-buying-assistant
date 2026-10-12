# Product Data Source Research Register

Status: INVESTIGATION STARTER — none of the candidates below is approved or confirmed for production use.

## Questions every provider must answer
- Which countries/markets and product categories are covered?
- Is it a live API, a batch feed, a search results API, or a seller-management API?
- Who is eligible to access it? Is approval required?
- What fields are returned (model identifiers, specifications, price, currency, condition, stock, shipping, warranty, seller, URL, image, timestamps)?
- How often is it updated, and are stale values indicated?
- What are request quotas, rate limits, price plans, and failure behaviors?
- Can we display the data to end users? Can we store/cache it? For how long?
- Can we keep historical price observations?
- Are product images allowed to be stored/displayed?
- Are affiliate/tracking links supported and required? What are the qualification and payment rules?
- How are corrections, deletions, and discontinued products handled?
- Which exact documentation URL supports each answer, and when was it checked?

## Candidate providers / sources to investigate

| Source | Potential use | Do not assume |
|---|---|---|
| Curated CSV/JSON dataset | Prototype catalog and tests | That manually entered offers are live or scalable |
| Manufacturer pages/manuals | Verify specifications and model identifiers | That product pages are a reusable API or grant data/image reuse rights |
| Awin product feeds | Affiliate product catalogs where approved | That a desired retailer/market/feed is available to our account |
| CJ Product Feed API | Product data for participating advertisers | That every advertiser or region is available |
| eBay Browse/Buy APIs | eBay marketplace search and item details | That production access is automatically granted |
| Amazon Product Advertising API | Amazon affiliate/product information under its terms | That access is guaranteed or that all data can be stored indefinitely |
| SerpApi / shopping search API | Discover listings across sellers | That results are exhaustive, permanently fresh, or unrestricted for caching/republication |
| Keepa | Supported Amazon product/price-history information | That it covers every retailer or that every offer is current |
| Daraz Open Platform / affiliate route | Investigate Pakistan marketplace data | That seller APIs provide public cross-marketplace product search |
| Direct retailer feed/API agreement | Local or specialty retailer data | That a retailer can provide data or affiliate attribution without agreement |

## Source evaluation record template

### Source: [provider]
- Checked on (UTC): [YYYY-MM-DD]
- Official documentation URL:
- Supported market(s):
- Categories covered:
- Access/approval steps:
- Relevant endpoints/feed format:
- Fields provided:
- Price and availability freshness:
- Request quotas/cost:
- Storage/cache/history rules:
- Image and display/reuse permissions:
- Affiliate rules and attribution:
- Known gaps or errors:
- Minimal test performed and evidence (sample response with secrets removed):
- Status: `UNVERIFIED` / `TESTED` / `APPROVED FOR PILOT` / `REJECTED`
- Next action:

## Evidence rules
Use official provider documentation and terms as the primary evidence. A blog or search snippet may help discover a claim but does not finalize access, pricing, or licensing conclusions. Record date-checked because product and affiliate APIs change.
