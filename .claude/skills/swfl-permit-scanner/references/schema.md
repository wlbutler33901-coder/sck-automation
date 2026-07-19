# "Development Scanner - Municipality Portals" Schema

Target: SCK Supabase project llwyvgkqhendgzsgngqh, schema public, table "Development Scanner - Municipality Portals", via the "Supabase - Storage Condo King" MCP connector. Write only the columns below. Do not write `id` (auto) or `created_at` (auto). Always use named columns in every INSERT/PATCH - never positional inserts.

**Important rules:**
- Numeric columns (`Building Size (SF)`, `Land Size (Acres)`, `Project Cost ($)`) must receive raw numbers, or the key omitted entirely. Any non-numeric string will be rejected by the database.
- Never invent a value to fill a field. Omitting the field is acceptable and expected.
- Preserve line breaks in multi-line fields (`Key Dates`, `Relevant News Articles`, `Key Executives`, `References & Data Sources`).

## Schema Definition

| Column (use exact name, contains spaces) | Type | Format rule |
|---|---|---|
| Posting Date | date | ISO YYYY-MM-DD. Use permit posting/issue date; if only application date exists, use that and note it in Key Dates. |
| Municipality Posting Look-Up Value | text | The permit/case number plus how to find it, e.g. Permit #COM2025-01234 - Building Permit (Lee County DCD Reports Portal: <url>). This is the natural key for dedupe - always populate. |
| Project Name | text | Best available project name; if none, construct <Use> at <Street> (e.g., Warehouse at 16800 Alico Commerce Ct). |
| Municipality | text | The permitting jurisdiction (e.g., Unincorporated Lee County, City of Naples). |
| Address | text | Street address / parcel location. |
| Parcel / Folio Number | text | Parcel / folio / STRAP number from the permit or county property appraiser. Stable across name/address changes; primary fallback dedupe key. Populate whenever obtainable. |
| City | text | City. |
| County | text | One of: Lee, Charlotte, Collier, Sarasota, Manatee. Always populate; it drives the report and the rotation QA. |
| State | text | Two-letter (FL). |
| Property Type | text | Controlled vocabulary - pick one: Industrial, Multifamily, Retail, Office, Hospitality, Mixed-Use, Self-Storage, Medical/Healthcare, Senior Living, Data Center, Land/Subdivision, Other. |
| Project Stage | text | Controlled vocabulary - one of: Planned / Permitting, Under Construction, Completed, On Hold / Stalled. Drives outreach priority. |
| Building Size (SF) | numeric | Digits only - no commas, units, or text. 100000 not 100,000 SF. Omit the key if unknown. Never put "(approx.)" here. |
| Land Size (Acres) | numeric | Decimal only, e.g. 8.5. Omit the key if unknown. |
| Project Cost ($) | numeric | Digits only, no $ or commas. 10000000. Use permit valuation; if using a researched estimate, put the caveat in Development Description / References, not here. Omit the key if unknown. |
| Developer / Sponsor / Key Principal | text | e.g., Seagate Development Group / Alico Commerce LLC. |
| Developer Description | text | 1-2 factual sentences about the firm. |
| Developer Website | text | Root URL. |
| Developer LinkedIn | text | Company page URL. |
| Development Description | text | What is being built - scope, size, clear height, units, tenancy, phase, corridor. Note any estimate caveats here. |
| Key Dates | text | Multi-line allowed (use real line breaks). Application submitted / under review / expected issuance / hearing dates. |
| Relevant News Articles | text | Numbered list, one item per line: 1) Headline/summary. URL. |
| Developer Contact - Office Address | text | Office address (+ general contact URL if useful). |
| Developer Contact - Phone | text | Main phone. |
| Key Executives | text | Multi-line: Title: Name per line. |
| References & Data Sources | text | Multi-line numbered list of every source URL used (permit portal + each web source). Include confidence/qualification notes here. |

## Reference Example (JSON Payload)

Use this as the canonical example of a complete, well-formed record. Match its depth and formatting: numeric fields clean, multi-line fields with line breaks, every external claim cited in References & Data Sources.

```json
{
  "Posting Date": "2025-11-02",
  "Municipality Posting Look-Up Value": "Permit #COM2025-01234 - Building Permit (Lee County DCD Reports Portal: https://www.leegov.com/dcd/reports)",
  "Project Name": "Alico Trade Center Warehouse (Building 3)",
  "Municipality": "Unincorporated Lee County",
  "Address": "16800 Alico Commerce Court",
  "Parcel / Folio Number": "26-46-25-00-00001.0000",
  "City": "Fort Myers",
  "County": "Lee",
  "State": "FL",
  "Property Type": "Industrial",
  "Project Stage": "Planned / Permitting",
  "Building Size (SF)": 100000,
  "Project Cost ($)": 10000000,
  "Developer / Sponsor / Key Principal": "Seagate Development Group / Alico Commerce LLC",
  "Developer Description": "Regional industrial park developer ...",
  "Developer Website": "https://seagatedevelopmentgroup.com",
  "Developer LinkedIn": "https://www.linkedin.com/company/seagate-development-group",
  "Development Description": "Construction of a new flex industrial warehouse ...",
  "Key Dates": "Permit application submitted: 11/02/2025\nBuilding plans under review as of mid-November 2025\nExpected building permit issuance: by December 2025",
  "Relevant News Articles": "1) Seagate completes California Closets facility at Alico Trade Center (2024). https://...",
  "Developer Contact - Office Address": "9921 Interstate Commerce Dr., Fort Myers, FL",
  "Developer Contact - Phone": "239-738-7900",
  "Key Executives": "CEO: Matt Price\nVP - Commercial Division: Mark Coon",
  "References & Data Sources": "1) Lee County DCD: https://www.leegov.com/dcd/reports\n2) Seagate press release: https://..."
}
```

*Note: The parcel/folio value shown is illustrative only - use the actual parcel/folio/STRAP number from the permit or county property appraiser, never a placeholder.*
