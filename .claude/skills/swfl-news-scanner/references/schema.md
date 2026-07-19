# "Development Scanner - News Scanner" Schema Spec

**Connection:** "Supabase - Storage Condo King" MCP, project llwyvgkqhendgzsgngqh, schema `public`, table `"Development Scanner - News Scanner"`.
**Auth:** the MCP connector handles auth; never embed keys in skill files or logs.

## Important Rules

- Numeric columns (`"Building Size (SF)"`, `"Project Cost ($)"`) must receive raw numbers, or the key omitted entirely. Never send `null`, empty strings, `$`, or commas. Never include "(approx.)".
- Never invent a value to fill a field. Omitting the field is acceptable and expected.
- For multi-line text fields, use real line breaks. Do not escape as literal `\n`.
- Use named columns in every INSERT. Quote identifiers (they contain spaces, parentheses, and forward slashes).

## Column-by-Column

| Column | Type | Format Rule |
|---|---|---|
| `Article URL` | text | **Mandatory.** Canonicalized via `scripts/url_normalize.py` before insert. This is the dedupe key. |
| `Publication` | text | Source name (e.g., "Business Observer", "Gulfshore Business", "Naples Press"). Use consistent naming for easy filtering. |
| `Article Title` | text | Exact headline as published. |
| `Article Date` | date | ISO `YYYY-MM-DD`. Publication date from the article (not scrape date - `created_at` auto-captures that). |
| `Author` | text | Byline if available. Omit if unattributed. |
| `Article Type` | text | Controlled vocab - one of: `Development Announcement`, `Sponsor Profile`, `Market Report`, `Permit Coverage`, `Acquisition Announcement`, `Capital Raise Coverage`, `Other`. |
| `Article Summary` | text | 2-3 sentence synthesis written by the agent. Capture: who, what, where, financing angle. Direct prose, no bullets. |
| `Key Quotes` | text | 1-3 attributed direct quotes from sponsors/principals, one per line, format: `"<quote>" - <Name>, <Title>`. These are outreach gold. Omit if no notable quotes. |
| `Project Name` | text | If named in the article. |
| `Property Type` | text | Controlled vocab (match Development Pipeline): `Industrial`, `Multifamily`, `Retail`, `Office`, `Hospitality`, `Mixed-Use`, `Self-Storage`, `Medical/Healthcare`, `Senior Living`, `Data Center`, `Land/Subdivision`, `Other`. Single value. |
| `City` | text | City named in the article. |
| `County` | text | One of `Lee`, `Charlotte`, `Collier`, `Sarasota`, `Manatee`, or - for incidental coverage of SWFL sponsors active elsewhere - leave null and note in `Notes`. |
| `Address or Location Detail` | text | Street address if given, or intersection/landmark detail. |
| `Building Size (SF)` | numeric | Digits only - no commas, no units. Omit if not stated. |
| `Project Cost ($)` | numeric | Digits only - no `$`, no commas. Omit if not stated. |
| `Project Stage` | text | Controlled vocab (match Pipeline): `Planned / Permitting`, `Under Construction`, `Completed`, `On Hold / Stalled`. Best inference from article language. |
| `Key Dates Mentioned` | text | Timeline mentioned in the article (groundbreaking, expected completion, hearing dates). Multi-line, one item per line. |
| `Developer / Sponsor` | text | Firm name + ultimate parent if mentioned (e.g., `KL WP Village LLC (The Kolter Group LLC)`). |
| `Key Principals Mentioned` | text | Multi-line: `<Title>: <Name>` per line. |
| `Developer Contact Info` | text | Only if explicitly in the article (firm address, phone, email). Don't web-scrape it here - that's the permit scanner's job. |
| `Financing Opportunity Type` | text | Controlled vocab - one of: `Construction Financing`, `Bridge/Mezz`, `Refi/Takeout`, `Equity Raise`, `Recap`, `Acquisition Financing`, `Multiple`, `None Apparent`. |
| `Financing Relevance Score` | text | One of `High`, `Medium`, `Low`. See scoring rules in SKILL.md §10. |
| `Outreach Recommendation` | text | If `Financing Relevance Score = High`, write 1-2 sentences of specific outreach framing (who to call, what to lead with, what hook to use from the article). For Medium/Low, can be omitted or brief. |
| `Linked Portal Record` | bigint | The `id` from `"Development Scanner - Municipality Portals"` if this article maps to an existing permit record. Populate via cross-reference query before insert. Leave null if no confident match. |
| `Notes` | text | Free-form: candidate pipeline matches that didn't quite reach confidence threshold, cross-reference observations, anything that doesn't fit elsewhere. |

## Example Insert Payload (JSON)

```json
{
  "Article URL": "https://www.businessobserverfl.com/news/2026/may/17/fort-myers-land-single-family-houses-sold/",
  "Publication": "Business Observer",
  "Article Title": "Fort Myers land zoned for single-family houses sold",
  "Article Date": "2026-05-17",
  "Author": "Louis Llovio",
  "Article Type": "Acquisition Announcement",
  "Article Summary": "A 223-acre parcel of residential property in North Fort Myers sold for $10.5M to a New York LLC tied to DW Partners. The site is zoned for single-family estate lots ranging 0.5-1 acre and is positioned just off Lynn Road near I-75. LSI Cos. brokered.",
  "Key Quotes": "\"...\" - Christi Pritchett, LSI Cos.",
  "Project Name": "18300 Leetana Road land assemblage",
  "Property Type": "Land/Subdivision",
  "City": "North Fort Myers",
  "County": "Lee",
  "Address or Location Detail": "18300 Leetana Road, near Lynn Road and I-75",
  "Project Cost ($)": 10500000,
  "Project Stage": "Planned / Permitting",
  "Developer / Sponsor": "DW Partners (NY LLC affiliate)",
  "Financing Opportunity Type": "Acquisition Financing",
  "Financing Relevance Score": "Medium",
  "Outreach Recommendation": "Research DW Partners' SWFL investment thesis; the buyer may need land carry + horizontal development financing if they intend to develop rather than hold. Reach via LSI broker contact (Christi Pritchett) for warm intro.",
  "Notes": "Buyer is institutional alt-asset manager; may have existing capital relationships."
}
```

Note: keys for numeric fields that aren't known (e.g., `Building Size (SF)` in the example above) are **omitted entirely** rather than sent as `null`.
