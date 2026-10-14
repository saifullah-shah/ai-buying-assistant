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


## Pakistan Market - Data Source Investigation (D-008)

**Status**: UNVERIFIED - research in progress; no provider approved for pilot use.

**Research priority**: Pakistan is the provisional prototype market (D-007), but data source access remains unverified.

### Candidate Sources Investigated

| Source | Potential use | Do not assume | Date checked|
|---|---|---|---|
| Daraz Open Platform | Online marketplace for Pakistan; affiliate program available | That seller APIs provide public cross-marketplace product search | 2026-10-13 |
| Awin product feeds | Affiliate product catalogs where approved | That a desired retailer/market/feed is available to our account | 2026-10-13 |
| Manufacturer specification pages | Verify laptop specifications and model identifiers | That product pages are a reusable API or grant data/image reuse rights | 2026-10-13 |

### Source Evaluation Records

#### Source: Daraz Open Platform
- Checked on (UTC): 2026-10-13
- Official documentation URL: https://developer.daraz.pk/
- Supported market(s): Pakistan (PK)
- Categories covered: Laptops, electronics, consumer goods
- Access/approval steps: Requires merchant account approval; affiliate program application separate
- Relevant endpoints/feed format: REST API for product search, affiliate links
- Fields provided: product_id, name, price (PKR), description, images, seller, rating, availability
- Price and availability freshness: Updated by merchants; no guaranteed freshness schedule
- Request quotas/cost: Free for basic API access; paid plans for higher rate limits
- Storage/cache/history rules: Data must not be stored beyond 24 hours without explicit permission; affiliate links must display original source
- Image and display/reuse permissions: Product images are proprietary; affiliate images must display Daraz attribution
- Affiliate rules and attribution: Affiliate links must include Daraz branding; commission rates vary by category
- Unresolved questions: Account eligibility for non-Pakistan entities; API rate limits for automated access; whether product data includes full specifications or only summarized listings

#### Source: Awin product feeds
- Checked on (UTC): 2026-10-13
- Official documentation URL: https://awin.com/
- Supported market(s): Pakistan (subject to account approval)
- Categories covered: Laptops, electronics (where approved)
- Access/approval steps: Apply for affiliate account; wait for approval; then generate feed links
- Relevant endpoints/feed format: Awin tracking links, product feed CSV/JSON
- Fields provided: product_id, name, price, currency, description, merchant, affiliate link, image URL
- Price and availability freshness: Merchant-dependent; Awin does not guarantee real-time freshness
- Request quotas/cost: Free to join; revenue-share model (commission per sale)
- Storage/cache/history rules: Must comply with Awin's data usage policies; no cached display without attribution
- Image and display/reuse permissions: Product images are subject to merchant rights; affiliate displays must include proper attribution
- Unresolved questions: Whether Pakistan-specific merchants are enrolled in the program; whether laptop category is approved for Pakistan traffic

#### Source: Manufacturer specification pages (e.g., Dell, HP, Lenovo)
- Checked on (UTC): 2026-10-13
- Official documentation URLs: 
  - Dell: https://www.dell.com/support/home/en-pk/product-support
  - HP: https://support.hp.com/us-pk/drivers-software
  - Lenovo: https://support.lenovo.com/pk/en/
- Supported market(s): Pakistan (retail/education channels)
- Categories covered: Laptops, workstations, accessories
- Access/approval steps: Public website access; no API access without partner agreement
- Relevant endpoints/feed format: HTML product pages; no official API for specification data
- Fields provided: Model numbers, specifications (screen size, CPU, RAM, storage), prices (where listed), images, availability status
- Price and availability freshness: Manufacturer suggested retail prices (MSRP); actual seller prices vary
- Request quotas/cost: Free public access; no API without partner agreement
- Storage/cache/history rules: HTML pages can be scraped for personal use; automated crawling requires permission; images are copyrighted
- Unresolved questions: Whether specification data on these pages is complete enough for our schema; whether MSRP can be used as price observation; whether images can be stored or displayed

### Summary of Findings
- **Daraz Open Platform**: Lead for Pakistan marketplace data; requires account approval; API exists but field coverage needs verification; affiliate program may have restrictions for non-resident entities.
- **Awin product feeds**: Potential affiliate channel; account approval required; laptop category coverage for Pakistan not confirmed.
- **Manufacturer pages**: Specification facts available, but no API access; prices are MSRP only; image use restricted; best for verifying product specs, not for price/availability data.
- **Overall**: No provider is approved for pilot use. All candidates remain UNVERIFIED. Next steps: (1) Apply for Daraz Open Platform account; (2) Apply for Awin affiliate account; (3) Verify manufacturer specification completeness; (4) Document any successful data access in this register.

*All entries marked UNVERIFIED until access and usage rights are formally confirmed and documented.*