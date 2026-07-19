# Target News Sources - SWFL CRE Financing Opportunities

Tiered by financing-signal density and pre-deal coverage. Exhaust higher tiers before spending budget on lower.

## Tier 1 - Primary Business Press

These produce the highest density of named-developer, pre-deal coverage.

| Source | URL | Coverage | Notes |
|---|---|---|---|
| Business Observer | https://www.businessobserverfl.com/ | Tampa Bay → Naples (all five SWFL counties), weekly CRE transactions roundup | Strongest single source. Look for weekly "top commercial real estate transactions" posts - named buyers/sellers/prices; the roundup already spans Charlotte, Collier, Lee, Manatee, and Sarasota. For targeted Sarasota/Manatee CRE, use the county landing page: https://www.businessobserverfl.com/news/commercial-real-estate/manatee-sarasota/ |
| Gulfshore Business | https://www.gulfshorebusiness.com/ | Naples-centric, Collier + Lee coverage | "Development" section is the priority. Often the first to cover Collier zoning approvals. |
| Naples Press | https://www.naplespress.com/business-real-estate/ | Naples / Collier | Dedicated business & real estate vertical with regular development coverage. |
| News-Press | https://www.news-press.com/ | Fort Myers / Lee | Gannett. Wide local coverage; CRE pieces are mixed in with general news. Filter to business section. |
| Naples Daily News | https://www.naplesnews.com/ | Naples / Collier | Gannett, sister to News-Press. Strong Collier development reporting. |
| SWFL Business Today | https://swfloridabusinesstoday.com/ | Regional SWFL | Monthly business journal cadence; deeper analysis pieces. |
| Sun Coast Media (Yoursun) | https://www.yoursun.com/ | Charlotte County (Punta Gorda, Port Charlotte, Englewood) | The Daily Sun's online home. Critical for Charlotte County, which is otherwise underrepresented. |
| Your Observer (Observer Media Group) | https://www.yourobserver.com/news/east-county/business/ | Sarasota County + East Manatee / Lakewood Ranch, Longboat / Siesta | Strongest pre-deal source for Sarasota/Manatee and the only deep Lakewood Ranch coverage (SMR, Benderson, Neal, Kolter, Tavistock). Named developers, acreage, parcel addresses from the planning/commission pipeline. Free, no paywall. Use BOTH URLs - Lakewood Ranch lives on /news/east-county/business/, downtown Sarasota on https://www.yourobserver.com/news/sarasota/business/. Reporters: Lesley Dwyer, Andrew Warfield. |
| SRQ Daily - Monday Business Edition | https://www.srqmagazine.com/srq-daily | Sarasota, Bradenton, Palmetto, barrier islands | Structured weekly business digest with tagged [Real Estate] / [Business] briefs - high density, names broker-of-record, and one of the few Tier 1 sources that regularly catches Palmetto/Manatee items. Predictable dated URL pattern (/srq-daily/YYYY-MM-DD) = easy scrape. |

## Tier 2 - Local TV (Business / Development sections)

Often picks up rezoning hearings, council meetings, and major project announcements that print outlets miss or are slower on.

| Source | URL | Coverage |
|---|---|---|
| WINK News | https://www.winknews.com/ | CBS, Lee/Charlotte/Collier |
| NBC2 | https://nbc-2.com/ | Same footprint |
| Fox 4 / WFTX | https://www.fox4now.com/ | Same footprint; Charlotte County coverage is notable |
| ABC7 / WWSB (MySuncoast) | https://www.mysuncoast.com/news/local/ | Sarasota, Manatee, Charlotte, DeSoto - only network affiliate based in the Sarasota-Bradenton MSA |

## Tier 3 - Broker Press Releases

Brokers announce deals here often before journalists pick them up. Lower polish, higher information density. Press-release format, not editorial - adjust extraction accordingly.

| Source | URL | Notes |
|---|---|---|
| LSI Cos. | https://www.lsicos.com/ | Fort Myers commercial brokerage; frequently named in SWFL land and commercial transactions with sponsor identity. |
| Lee & Associates Naples-Ft. Myers | https://lee-fl.com/news/ | Publishes monthly transaction roundups with sponsor names and deal sizes. |
| SVN Commercial Advisory Group (Suncoast) | https://suncoastsvn.com/category/news/ | Sarasota, Manatee, Charlotte. Gold-standard broker feed for this market (top-10 SVN office nationally). Structured releases: named buyer/seller LLC, address, SF, exact price, broker - often days ahead of the Business Observer roundup. Has RSS at https://suncoastsvn.com/feed/. |
| Ian Black Real Estate | https://ian-black.com/blog/categories/deals | Sarasota + Manatee (downtown Sarasota, Lakewood Ranch, Bradenton, Venice). Sarasota's dominant local independent CRE firm. Original deal announcements with prices, public-sector deals, exclusive listings. No RSS (Wix) - scrape the Deals page; mirror their LinkedIn, which often posts 1-2 days ahead. |

## Search Strategy Per Source

**Tier 1 sites with explicit business/CRE sections:** start at the business or real-estate landing page; sort by most recent; scan headlines for the qualification filter; open articles flagged as potentially qualifying.

**Tier 1 sites without a clean CRE section (News-Press, Yoursun):** use the site's search for terms like: "development", "approves", "rezoning", "construction", "groundbreaking", "acquires", "buys land", "permit", "plans".

**Your Observer:** free, no paywall. Scan BOTH business landing pages - /news/east-county/business/ (Lakewood Ranch, East Manatee) and /news/sarasota/business/ (downtown Sarasota). Heavy planning-commission and county-commission pipeline coverage with named developers and parcel addresses.

**SRQ Daily:** the Monday Business edition is the target. Use the dated URL pattern /srq-daily/YYYY-MM-DD; scan the tagged [Real Estate] and [Business] briefs.

**Tier 2 TV sites:** site search for the same terms; look in business/development sub-pages. For MySuncoast (WWSB), pair the /news/local/ feed with keyword filters ("rezoning", "commission approves", "Lakewood Ranch", "Parrish", "groundbreaking") to surface Manatee government / Bradenton EDC items the Sarasota-centric print outlets miss.

**Tier 3 broker pages:** the press releases ARE the article; extract directly. No need for additional enrichment beyond what's in the release. SVN Suncoast exposes RSS at /feed/ (use it first). Ian Black has no RSS - scrape the /blog/categories/deals page directly and check their LinkedIn for advance posts.

## Geographic Filter

The analyst covers **Lee, Charlotte, Collier, Sarasota, and Manatee counties**, treated as one SWFL region. Orlando MSA and the rest of the Tampa Bay metro (Hillsborough, Pinellas, Pasco, Polk) are part of the broader Calusa mandate but not in this scanner's current scope - capture incidentally if a SWFL sponsor appears in that context, but don't actively scan those outlets here. Note that some sources (Business Observer's weekly roundup, FOX 13) span the full Tampa Bay-to-Naples corridor - filter their content down to the five SWFL counties.

For each article, set the `County` field to the relevant SWFL county (Lee, Charlotte, Collier, Sarasota, or Manatee) or, if it's a sponsor-profile piece on a SWFL firm covering activity elsewhere, the firm's home county.
