# Platform Playbook - Per-Source Extraction Hints

## Tier 1 - Primary Business Press

### Business Observer (businessobserverfl.com)
- **Strongest weekly artifact:** the "Top commercial real estate transactions in [counties]" recurring post (typically Monday or Tuesday). Lists named buyers, sellers, addresses, prices, property types - multiple SWFL transactions per week in one place. Always scan this if it ran in the window.
- Some articles are behind a soft paywall ("Already subscribed?"). Read the snippet/teaser content; do not attempt credentialed bypass. Capture what's visible (headline, lede, byline, date) and note paywall in `Notes`.
- Bylines: Louis Llovio writes most CRE pieces. Useful for filtering related items.

### Gulfshore Business (gulfshorebusiness.com)
- Best section: `/lee/` and `/collier/` paths. Development pieces often have `/development/` in URL.
- Reliable extraction - clean article markup, full content typically visible without paywall.
- Byline Tim Aten covers a lot of the Collier development beat.

### Naples Press (naplespress.com)
- Section: `/business-real-estate/`. Strong on Collier transactions and development.
- Includes a "Real estate briefs & transactions" recurring feature - similar to Business Observer's roundup but Collier-focused.

### News-Press (news-press.com)
- Gannett. Strong on Lee County but CRE is mixed into general news. Site search is the right entry point.
- Search terms: `development`, `rezoning`, `construction`, `acquires`, `buys`, `permit`, `groundbreaking`.
- Paywall: Gannett uses a metered paywall. Headlines/ledes are visible; full text behind the meter. Same handling as Business Observer - capture visible content, note in `Notes`.

### Naples Daily News (naplesnews.com)
- Sister site to News-Press, same Gannett platform and same paywall behavior. Same search strategy.

### SWFL Business Today (swfloridabusinesstoday.com)
- Lower publication cadence (monthly-feel); deeper feature pieces.
- Worth a single visit per run; check for any feature on developers, projects, or capital activity.

### Yoursun (yoursun.com)
- Sun Coast Media - covers Charlotte County (Punta Gorda, Port Charlotte, Englewood) primarily.
- This is the critical Charlotte County source. Site search for: `development`, `Punta Gorda`, `Port Charlotte`, `rezoning`, `commercial`, `construction`.
- Articles may also reach behind a metered paywall.

### Your Observer (yourobserver.com)
- Observer Media Group - five sister weeklies on one site. **Strongest pre-deal source for Sarasota/Manatee**, and the only deep Lakewood Ranch coverage.
- Scan BOTH business landings: `/news/east-county/business/` (Lakewood Ranch, East Manatee - SMR, Benderson, Neal, Kolter, Tavistock) and `/news/sarasota/business/` (downtown Sarasota).
- Free, no paywall - full article text is reliably extractable.
- Heavy planning-commission / county-commission pipeline coverage: named developers, acreage, entitlement transfers, parcel addresses. Reporters: Lesley Dwyer (East County development), Andrew Warfield (Sarasota County development).

### SRQ Daily (srqmagazine.com)
- The **Monday Business edition** is the target - a structured weekly digest with tagged `[Real Estate]` and `[Business]` briefs. High named-firm density, ideal for keyword scanning.
- Predictable dated URL pattern: `/srq-daily/YYYY-MM-DD`. Names broker-of-record on transactions.
- Catches Palmetto/Manatee items that the Sarasota-centric outlets miss.

## Tier 2 - Local TV

### WINK News (winknews.com), NBC2 (nbc-2.com), Fox 4 (fox4now.com)
- Best entry: site search for development-related terms.
- TV station sites pick up rezoning hearings, council meetings, and major project announcements often quickly - useful for catching items the print outlets are slower on.
- Coverage tends to be shorter and lead with the local-impact angle; extract sponsor and project facts and supplement with web search if names are not fully spelled out.

### ABC7 / WWSB - MySuncoast (mysuncoast.com)
- The only network affiliate physically based in the Sarasota-Bradenton MSA - fills the Manatee government / Bradenton EDC gap the Sarasota-centric print sources miss.
- Entry: `/news/local/` feed paired with keyword filters: `rezoning`, `commission approves`, `Lakewood Ranch`, `Parrish`, `groundbreaking`, `development`. The local feed mixes in crime/weather, so keyword-filter hard.
- Strong on Manatee/Sarasota County Commission coverage, EDC interviews, and groundbreakings. Daily publishing; same short-form extraction approach as the SWFL TV sites above.

## Tier 3 - Broker Press Releases

### LSI Cos. (lsicos.com)
- Press-release format. Each release covers one or a handful of transactions with buyer, seller, address, price, broker, sometimes intended use.
- LSI brokers a high share of SWFL land and commercial transactions. Treat each release as one candidate row per transaction (multi-transaction releases yield multiple article rows, all citing the same URL - in that case, write multiple rows with the same `Article URL` but distinct `Project Name` values, and use `Notes` to disambiguate).

### Lee & Associates Naples-Ft. Myers (lee-fl.com/news/)
- Publishes monthly transaction roundups under a recurring "FOR IMMEDIATE RELEASE Lee & Associates Announces Southwest Florida Transactions" header.
- Each release lists multiple Sales / Leases with sponsors and sizes named. Same multi-row handling as LSI.

### SVN Commercial Advisory Group - Suncoast (suncoastsvn.com)
- Top-10 SVN office nationally; covers Sarasota, Manatee, and Charlotte. The gold-standard Tier 3 feed for this part of the region.
- **Check RSS first:** `/feed/`. Browse categories `/category/news/`, plus "Just Sold" / "Closing" posts.
- Structured releases: named buyer LLC, named seller LLC, address, square footage, exact price, broker names. Asset mix across office, medical office, retail, land, industrial, multifamily. Same multi-transaction → multi-row handling as LSI when a post lists several deals.

### Ian Black Real Estate (ian-black.com)
- Sarasota's dominant local independent CRE firm; covers Sarasota + Manatee (downtown Sarasota, Lakewood Ranch, Bradenton, Venice).
- Scrape `/blog/categories/deals` directly - **no RSS** (Wix site). Mirror their LinkedIn, which often posts 1-2 days ahead of the blog.
- Mixes original deal announcements with prices, public-sector deals (county/city acquisitions), named-tenant lease signings, and priced exclusive listings. Strong retail / office / redevelopment-land signal. Partners: Jag Grewal, Cameron Wilson, Michelle Fuller, Ian Black.

## General Notes

**Paywalls.** Don't bypass with credentials that aren't the agent's. Capture the visible content (headline, lede, dateline, byline) and any structured metadata available. Mark `Notes` with `"Behind paywall - content captured from visible portion only"`. The visible portion is often enough to qualify and write a useful row.

**RSS feeds.** Some sources expose RSS at `/feed/` or `/rss/`. RSS gives clean titles + summaries + URLs without paywall friction; check for RSS first if browsing the site is awkward.

**Time stamps.** Many CRE pieces are "published" on the print date but updated on subsequent days. Use the article's stated publication date for `Article Date`, not the last-modified header.

**Cross-source dedupe.** A press release at LSI may show up two days later as an article at Business Observer. Both are valuable but they cite different URLs. If both reach the qualification filter, write both rows; in `Notes` on each, reference the other URL. This gives you the broker's view + the journalist's framing.

**Don't deep-research every article.** The article is the primary signal. Use web search only when the article is missing critical sponsor/project info needed to qualify or score. The permit scanner does the deep enrichment work - this skill is faster surface coverage.
