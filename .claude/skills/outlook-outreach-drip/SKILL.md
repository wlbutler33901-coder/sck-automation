---
name: outlook-outreach-drip
description: Draft 1:1 Outlook outreach emails to quarantined (unverified) SCK unit owner emails, process NDR kickbacks, and run the BMV owner marketing campaign. Three modes. DRAFT mode (default, nightly) pulls the next batch of quarantined emails from "04d - Email Verification", personalizes a short plain text outreach sent from Will Butler's Calusa Investments mailbox with Chance Friedman CCd, saves them to Outlook Drafts so Will can press send in the morning, and stamps "Drafted At". KICKBACK mode scans the mailbox for bounce and NDR messages, marks bounced addresses in 04d, suppresses them in "04a - Email Suppression", clears them from the CRM, and promotes drafts with no kickback after 4 days to clean. CAMPAIGN mode runs only after the verification queue is empty and drafts up to 50 UNIQUE Bonita Motor Vault owner recipients per morning from "04 - Unit Owner CRM" in region order, deduplicated by email so multi-unit owners are contacted once, logging each to "04e - Campaign Sends". Use whenever asked to run the outreach drip, draft the outreach batch, prep tomorrow's outreach emails, scan for kickbacks, process NDRs, check outreach bounces, or run the BMV owner campaign. Requires the "Supabase - Storage Condo King" and Microsoft 365 connectors.
---

# SCK Outlook Outreach Drip

## Purpose

"04d - Email Verification" is a WORKING QUEUE, not an archive. It holds only addresses that are not yet proven, meaning the pending drip population. A verified address does not live here: it lives in "04 - Unit Owner CRM" (proven good, with "Email Verified At" stamped) or in "04a - Email Suppression" (proven bad). When an address leaves the queue in either direction, its 04d row is DELETED.

The "04 - Unit Owner CRM" table holds only verified safe emails. Unverified addresses (MillionVerifier catch_all or unknown with no open on record) have been PULLED OUT of the CRM and sit only in "04d - Email Verification" with "Send Status" = 'quarantined', each carrying a "CRM Placements" jsonb array of {index, column} recording exactly which contact and which email column the address came from. They must never go through Constant Contact. Instead they are contacted 1:1 from will.butler@calusainvestments.com via Outlook, CCing chance.friedman@calusainvestments.com. Delivery itself is the verification: a send with no kickback proves the address and RESTORES it into the CRM, a kickback suppresses it permanently.

Drip rate: 45 drafts per run, one run per day, which clears the full quarantined set in about 7 days.

## Connectors required

- "Supabase - Storage Condo King" (project llwyvgkqhendgzsgngqh). All identifiers double quoted. apply_migration for DDL, execute_sql for DML. Multi statement execute_sql returns only the last result, so run every verification as a separate call.
- Microsoft 365 (Outlook tools), signed in as will.butler@calusainvestments.com.

**Mailbox precondition, verify before drafting.** Call the M365 get_me tool
first. If the signed-in address is not will.butler@calusainvestments.com, STOP
immediately, create no drafts, stamp nothing, and report the mismatch. The
outlook_create_draft tool has no sender parameter: it writes only to the
signed-in user's Drafts folder, and mail sent from it goes out under that
identity. Drafting under any other account would put the messages in the wrong
mailbox. This is a hard stop, never a warning to work around.

**Sending identity.** These go out from Will Butler personally at Calusa
Capital Partners, NOT from market@storagecondoking.com. That is deliberate:
1:1 correspondence from a named person reads as personal outreach rather than
marketing, and NDRs return to Will's own mailbox where KICKBACK mode can find
them. Do not attempt to set a different From address or use the shared mailbox.

**Always CC chance.friedman@calusainvestments.com** on every draft, so Chance
sees the outreach and can pick up replies.

## Mode selection

This skill runs UNATTENDED inside a scheduled Claude Code cloud routine at
5:15 AM. There is no user to ask questions. Every run is a FULL CYCLE in this
fixed order:

1. KICKBACK mode (process NDRs and promote proven deliveries).
2. DRAFT mode (prepare the next verification batch).
3. CAMPAIGN mode, ONLY if the verification queue had nothing to draft.

The verification queue always outranks the campaign. CAMPAIGN mode runs only
when Step 1 of DRAFT mode returned zero rows, meaning "04d - Email
Verification" holds no quarantined address still waiting on a draft. If DRAFT
mode drafted even one message this run, skip CAMPAIGN mode entirely and say so
in the report. The queue is empty as of 2026-08-11, so the campaign is
currently the working part of each run.

On ambiguity or any unexpected state, stop that item, leave the data untouched,
and explain it in the run report instead of guessing.

Idempotence guard: before DRAFT mode, check whether any 04d row already has
"Drafted At"::date = current_date. If yes, the day's batch exists (the routine
re-ran); skip DRAFT mode and say so in the report.

Campaign idempotence guard: before CAMPAIGN mode, count "04e - Campaign Sends"
rows for the campaign with "Drafted At"::date = current_date. If that count is
already at or above the 50 per morning cap, the campaign batch exists (the
routine re-ran); skip CAMPAIGN mode and say so in the report.

---

## DRAFT mode

### Step 1. Pull the batch

```sql
select d.id, lower(btrim(d."Email")) as email, d."MV Result", d."CRM Placements"
from "04d - Email Verification" d
where d."Send Status" = 'quarantined'
  and d."Drafted At" is null
order by d."MV Result" desc, d."Email"
limit 45;
```

If zero rows: report "Quarantined queue is empty, drip complete" and stop.

### Step 2. Join contact context

The address and often the entire contact are NOT in the CRM anymore. Contact context comes through "CRM Placements", checked in two places by the first placement's index:

1. The CRM, for contacts that still have other verified emails:

```sql
select c."Index", c."First Name", c."Last Name", c."Project", c."Region"
from "04 - Unit Owner CRM" c
where c."Index" in (<first placement index of each batch row>);
```

2. The parked standby ledger for the rest:

```sql
select ("CRM Indexes")[1] as idx,
       "Archived Contact"->>'First Name' as first_name,
       "Archived Contact"->>'Last Name' as last_name,
       "Archived Contact"->>'Project' as project,
       "Archived Contact"->>'Region' as region
from "04a - Email Suppression"
where "Suppression Type" like 'Parked%' and "Suppress" = false
  and ("CRM Indexes")[1] in (<remaining indexes>);
```

"Index" is bigint, cast any array comparisons ::int8[]. If an index appears in neither place, skip that address and delete its 04d row with no new 04a write. If the first name is null or blank, open with "Hello" instead of a name.

### Step 3. Create the Outlook drafts

For each contact create one draft with Microsoft 365 outlook_create_draft. Plain text only. No images, no HTML marketing layout, no unsubscribe footer. This is personal correspondence.

Every draft is addressed to the contact and CCs
chance.friedman@calusainvestments.com.

Subject: rotate between these three so the batch does not look templated:
1. `Your unit at {Project}`
2. `{Project} resale values`
3. `Quick question about your unit at {Project}`

**Body format: HTML, not plain text.** The earlier plain-text approach carried
hard line breaks mid-sentence and greyed out Outlook's formatting controls.
Build the body as simple HTML so it looks exactly like a normal email typed in
Outlook:

- One `<p>` per paragraph. NEVER insert manual line breaks inside a sentence;
  let the client wrap text naturally.
- The value link is a standard `<a href>` anchor with no style attributes,
  with the full URL as the href and the visible text. The M365 draft tool
  strips inline styles, so the link renders in Outlook's default blue, and
  that is accepted. Body text stays black via the plain HTML structure.
- The bullet list is a `<ul>` with plain `<li>` items, no styling.
- No other styling: no bold, no colors, no images, no font size changes.

Body template (adjust the opening naturally per contact; keep the bullets
verbatim):

```
Hi {First Name},

I run Storage Condo King, the market data platform tracking resale activity
across Florida garage and car condo projects, including {Project}.

You can see current values for {Project} here:
{value link}

For unit owners, the platform provides:

- Current market valuations, with a valuation engine covering both pre-sale
  and re-sale units.
- Verified sale comps across every Florida garage and car condo project.
- Live listings and a marketing distribution network when you are ready to
  sell.
- Investment cash flow models and market research.
- Project level detail: demographics, amenities, and the new supply pipeline.

Happy to send our Q2 2026 Florida Garage and Car Condo Market Report, or run
a no-cost value estimate on your specific unit. Just reply and I will put it
together.

Will Butler
Calusa Capital Partners
C: 239-898-5840
E: will.butler@calusainvestments.com
```

The signature is exactly those four lines, nothing more. No "Storage Condo
King" suffix on the firm line, no website line under the signature. It must
match Will's normal Calusa signature block verbatim.

If "Project" is null, drop the project sentence and link the general page
https://storagecondoking.com/unit-appraisals with the same utm params.

The project link must URL-encode the project name exactly as it appears in
"01 - Projects", normalizing en dashes and em dashes to hyphens first per the
repo join convention, with utm_source=outreach, utm_medium=email,
utm_campaign=drip-2026-08.

### Step 4. Stamp the batch

After all drafts are created, one set based update, then verify with a separate query:

```sql
update "04d - Email Verification"
set "Drafted At" = now(), "Send Status" = 'drafted'
where lower(btrim("Email")) in (<batch emails actually drafted>);
```

```sql
select count(*) from "04d - Email Verification" where "Send Status" = 'drafted' and "Drafted At"::date = current_date;
```

Only stamp emails whose draft was actually created. If any outlook_create_draft call fails, leave that row untouched so it re enters the next batch.

### Step 5. Report

End the run with a compact report: NDRs processed, addresses suppressed,
contacts reinstated, drafts promoted to clean, drafts created today, drafts
failed, remaining queue count, projected days to clear at 45 per day. The
drafts wait in Will's Outlook Drafts folder for him to review and send in the
morning, each CCing Chance. Write the report as the final message of
the run so it lands in the routine's run log.

---

## KICKBACK mode

### Step 1. Find NDRs

Search will.butler@calusainvestments.com with Microsoft 365 outlook_email_search for delivery failure messages received since the earliest "Drafted At" that is still in 'drafted' status (default lookback 10 days). Search terms to cover, run as separate searches and merge results:
- subject contains "Undeliverable"
- subject contains "Delivery has failed"
- subject contains "Delivery Status Notification"
- from contains "postmaster" or "mailer-daemon"

From each NDR extract the failed recipient address. Read the message body with the appropriate Outlook read tool when the failed address is not in the subject. Collect a deduplicated, lowercased list of bounced addresses. Only keep addresses that exist in 04d with "Send Status" = 'drafted'.

### Step 2. Suppress the bounces

For each bounced address, run these as separate statements with a separate verification query after each write:

1. Remove the queue row (the address is now proven bad and belongs in 04a only):
```sql
delete from "04d - Email Verification" where lower(btrim("Email")) in (<bounced>);
```

2. Insert into "04a - Email Suppression" (skip addresses already present, match on lower btrim). Populate "Email", "Suppress" = true, "Suppression Type" = 'Bounce', "Bounce Class" = 'hard', "Bounce Reason" = the NDR reason line if extractable else 'Outlook NDR', "Source" = 'Outlook NDR', "Notes" = 'Outlook 1:1 outreach kickback. Ingested {date}.', "Suppressed At" = now(). If the NDR reason indicates a soft failure (mailbox full, vacation autoreply), use "Suppression Type" = 'Soft bounce - not suppressed', "Bounce Class" = 'soft', "Suppress" = false, and leave the address in the queue rather than suppressing it.

3. Clear the address from CRM columns "Email 1" through "Email 4" (set the matching cell to null, exact set based update on lower btrim match).

4. If the bounced address belonged to a parked standby contact (ledger row with "Suppression Type" = 'Parked - unverified standby') and it was the contact's last quarantined address, update that ledger row: set "Suppression Type" = 'Parked - no email' and append to "Notes" that the final address hard bounced on {date} and the contact now waits on parcel based enrichment. If the contact is in the CRM and now has no non blank email in any column, follow the retire procedure from the sck-bounce-ingest skill: archive to the 04a jsonb ledger, delete any deal_leads rows, delete the CRM row, and flip "Removed From CRM".

### Step 3. Promote proven deliveries and RESTORE to CRM

Drafted emails with no kickback after 4 days are delivery proven. Three actions per address, in this order.

1. Reinstate the contact if it is parked. If the placement index is not in the CRM, find its row in the standby ledger ("04a - Email Suppression" where "Suppression Type" like 'Parked%', "Suppress" = false, ("CRM Indexes")[1] = index) and re insert the contact into "04 - Unit Owner CRM" from the "Archived Contact" jsonb, preserving the original "Index" and all fields. Then delete that ledger row. Verify the insert with a separate query before proceeding.

2. Restore the address using "CRM Placements". For each placement {index, column}: if that contact's target column is null or blank, write the address into that exact column. If occupied by a different address, use the first empty column of Email 1 to 4. If no empty column exists or the contact cannot be reinstated, leave everything untouched, keep the 04d row 'drafted', and flag it in the report.

3. Stamp the CRM and clear the queue row:

```sql
update "04 - Unit Owner CRM" set "Email Verified At" = current_date
where "Index" in (<restored placement indexes>);
```

```sql
delete from "04d - Email Verification" where lower(btrim("Email")) in (<restored addresses>);
```

Verify each with a separate query. Restored addresses are now in the CRM and safe for future Constant Contact daily lists. Never delete a 04d row without restoring both the contact and the address first. The CRM invariant is row count equals emailable count. The 04d invariant is zero overlap with CRM emails: every row is still pending.

### Step 4. Report

Report: NDRs found, addresses suppressed, contacts retired, drafts promoted to clean, drafts still in the 4 day waiting window, remaining quarantined count.

---

## CAMPAIGN mode

Campaign name: `BMV-Owner-1`. This is a VOLUME marketing campaign to existing
verified unit owners, not 1:1 verification correspondence. It runs at the end
of each 5:15 AM run, only when the verification queue had nothing to draft, and
only after the asset reachability gate passes. Up to 50 drafts per morning.

The ledger is "04e - Campaign Sends" (columns "Email", "Campaign", "Project",
"Unit", "Region", "Drafted At"), unique on lower("Email") plus "Campaign", so a
contact can receive this campaign exactly once. The table and the public
"Marketing Materials" bucket already exist. NEVER run a migration from this
skill.

### Step 1. Asset reachability gate (BEFORE the first draft of any run)

Fetch BOTH linked assets with a HEAD or ranged GET before building a single
draft:

- Report (PDF): https://llwyvgkqhendgzsgngqh.supabase.co/storage/v1/object/public/Quarterly%20Market%20Reports/florida-car-condo-market-report-q2-2026.pdf
- Listing (page): https://storagecondoking.com/projects/Bonita%20Motor%20Vault?utm_source=drip&utm_campaign=bmv-owner-1

The report URL passes only on a 2xx or 206 response whose content type is
application/pdf. Supabase storage returns a JSON body with
`{"error":"not_found","code":"NoSuchKey"}` for a missing object, so a JSON
content type is a FAILURE even when the status line looks survivable.

The listing URL passes on any 2xx. It is a web page, not a PDF, so do not
apply the content type test to it; a redirect that lands on a 2xx is fine, a
404 or 5xx is not.

If EITHER asset fails, draft NOTHING for this campaign. Insert no ledger rows,
log the failure as a learning, and state plainly in the run summary which URL
failed and with what status. Fifty emails carrying a dead link is worse than a
day's delay, and the campaign simply resumes the next morning once the asset is
in place. This gate is never bypassed or worked around.

The brochure is no longer linked in the campaign body and is NOT gated. The
"Marketing Materials" bucket state no longer blocks this campaign.

### Step 2. Pull the live BMV pricing data

**HARD RULE: NO HARDCODED FIGURES.** Every dollar and every percent in the
Bonita section comes from the RPC or the live table on the run that drafts it,
so the email can never contradict the listing page. The example numbers in the
target shape below are illustration only, never values to copy.

Run this once per run. It returns every figure the Bonita section needs:

```sql
with p as (
  select "Unit Size"::numeric as sf, "Asking $ PSF"::numeric as ask_psf,
         "Appraised $ / SF"::numeric as val_psf, "# of Units" as units,
         "Founding Cap" as cap, "Units Committed" as committed,
         "Ground Breaking" as gb, "Developer Listing Comments" as listing_comments
  from "06 - Pre-Sales" where "Project" = 'Bonita Motor Vault'
), r as (
  select (get_presale_appraisal_data('Bonita Motor Vault') -> 'project_context') as pc
)
select p.sf, p.ask_psf, p.val_psf,
       floor(p.ask_psf * p.sf / 1000) * 1000 as asking_price,
       floor(p.val_psf * p.sf / 1000) * 1000 as market_value,
       floor((p.val_psf - p.ask_psf) * p.sf / 1000) * 1000 as discount_dollars,
       round((p.val_psf - p.ask_psf) / p.val_psf * 100, 1) as discount_pct,
       p.units, p.cap, p.committed, (p.cap - p.committed) as positions_left,
       p.gb, p.listing_comments,
       (r.pc ->> 'annual_appreciation_pct') as annual_growth_pct,
       (r.pc -> 'region_kpis' ->> 'unit_sales_ttm') as sales_ttm,
       (r.pc -> 'region_kpis' ->> 'median_psf_ttm') as median_psf_ttm
from p, r;
```

Field sourcing, exactly:

- Asking PSF, valuation PSF and average unit size come from "06 - Pre-Sales"
  ("Asking $ PSF", "Appraised $ / SF", "Unit Size").
- Asking price, market value and dollar discount are DERIVED as PSF times unit
  size. Submarket annual growth, trailing twelve month sales count and median
  PSF come from the get_presale_appraisal_data RPC under "project_context",
  the last two nested in "region_kpis".
- Founding fields ("Founding Cap", "Units Committed", "# of Units",
  "Ground Breaking", "Developer Listing Comments") come from "06 - Pre-Sales".

**ROUNDING, follow exactly or the email will disagree with the listing page.**
FLOOR every dollar figure to the nearest $1,000. Compute the discount percent
from the UNROUNDED values and round to one decimal. "Appraised $ / SF" is
stored already rounded, so deriving dollars from it and then rounding up would
overstate the equity and drift off the published valuation; flooring reconciles
to the listing page and is the conservative direction for a discount claim.
Verified on 2026-08-15: $480 and $597 PSF on 1,125 SF floor to $540,000 asking
and $671,000 value, a $131,000 discount at 19.6 percent, which matches the
published appraisal.

- Scarcity. Positions remaining is "Founding Cap" minus "Units Committed".
- NULL RULE. If ANY figure comes back null, OMIT the sentence that carries it
  rather than inventing a value, and note the omission in the run report. The
  rest of the Bonita section still sends. This applies to every figure, not
  only the scarcity fields.
- Release detail. Which buildings are released, and how many units that covers,
  come from "Developer Listing Comments".
- Cross-check unit count, delivery year and flood zone against "01 - Projects".
  Report any mismatch rather than silently rewriting the copy.

### Step 3. Select the batch

Region order is fixed: South Florida, then Tampa MSA, then Southwest Florida,
then Central-East Florida, then Jacksonville MSA, then Orlando MSA. Within a
region, order by "Project" then "Index". Draft to "Email 1" ONLY; the other
email columns are never used by this campaign.

**FIFTY UNIQUE RECIPIENTS, NOT FIFTY ROWS.** Owners hold multiple units, so a
plain row limit under-delivers badly: on 2026-08-12 fifty rows collapsed to
twenty one people. DEDUPLICATE on lower(btrim("Email 1")) FIRST, then take 50
unique recipients, pulling as many rows as needed to reach 50 addresses. One
draft and one ledger row per recipient, never per unit.

Where an owner holds several units, reference that owner's LOWEST unit number
in the copy. Unit numbers are text, so rank on the digits ("Unit #" stripped to
digits, cast to bigint) and fall back to the raw text when a unit carries no
digits. The chosen row also supplies the "Project", "Region" and "Unit" written
to the ledger. An owner holding units in more than one region is worked once,
under the region of their lowest-numbered unit.

```sql
with eligible as (
  select lower(btrim(c."Email 1")) as email, c."Index", c."First Name",
         c."Region", c."Project", c."Unit #"
  from "04 - Unit Owner CRM" c
  where coalesce(btrim(c."Email 1"), '') <> ''
    and coalesce(btrim(c."Litigator"), '') = ''
    and not exists (
      select 1 from "04e - Campaign Sends" s
      where lower(btrim(s."Email")) = lower(btrim(c."Email 1"))
        and s."Campaign" = 'BMV-Owner-1'
    )
    and not exists (
      select 1 from "04a - Email Suppression" x
      where lower(btrim(x."Email")) = lower(btrim(c."Email 1"))
        and x."Suppress" = true
    )
), ranked as (
  select e.*, row_number() over (
      partition by e.email
      order by nullif(regexp_replace(e."Unit #", '\D', '', 'g'), '')::bigint nulls last,
               e."Unit #",
               array_position(array[
                 'South Florida','Tampa MSA','Southwest Florida',
                 'Central-East Florida','Jacksonville MSA','Orlando MSA'], e."Region"),
               e."Project", e."Index") as rn
  from eligible e
)
select email, "Index", "First Name", "Region", "Project", "Unit #"
from ranked
where rn = 1
order by array_position(array[
    'South Florida','Tampa MSA','Southwest Florida',
    'Central-East Florida','Jacksonville MSA','Orlando MSA'], "Region"),
  "Project", "Index"
limit 50;
```

"Litigator" is text and holds either null or the literal 'Litigator', so the
blank test above excludes the flagged rows. As of 2026-08-12 the eligible set
is 823 CRM rows collapsing to 658 unique recipients, so the campaign takes
roughly 14 mornings at 50 unique recipients per run. Report the unique
recipient count, never the row count, or the remaining runway reads long.

If zero rows come back, report "BMV owner campaign complete, no eligible
contacts remain" and stop.

### Step 4. Create the drafts

One Outlook draft per contact with outlook_create_draft, addressed to "Email 1".

**CC chance.friedman@calusainvestments.com on EVERY campaign draft.** The old
no-CC campaign exception is REMOVED. Chance is copied on the campaign exactly as
he is on the verification drip, so he sees the outreach and can pick up replies.

**SUBJECT, always exactly:**

`Your unit at {Project} and a first look at Bonita Motor Vault`

**SUBJECT GUARD.** CAMPAIGN mode uses this ONE fixed subject for every draft and
NEVER the DRAFT-mode three-subject rotation. Do not vary it, do not alternate it,
do not borrow "{Project} resale values" or "Quick question about your unit at
{Project}" from DRAFT mode. Those belong to the verification drip only. On
2026-08-13 a run applied the rotation to 43 of 50 campaign drafts and every one
had to be corrected by hand. The only value that changes between drafts is
{Project}.

Body is HTML in Will's voice, no em dashes and no en dashes.

**Markup rules, tested against the connector on 2026-08-12.**

- Build blocks with `<div>`, NOT `<p>`. Outlook gives `<p>` a default top
  margin, and that margin on the first block is what rendered as an empty gap
  above the greeting. `<div>` carries no margin, so the greeting sits flush at
  the top.
- Separate blocks with a `<div><br></div>` spacer. That reproduces paragraph
  spacing without the `<p>` margin.
- The body string MUST begin with the greeting `<div>`. No leading newline, no
  empty `<div>`, `<p>` or `<br>`, no wrapper padding ahead of it. Graph
  prepends its own `\r\n` to the stored content, which is inert HTML
  whitespace and renders nothing; do not try to strip it and do not add one.
- Each "button" is a standalone `<div>` holding a single `<a href>` anchor
  whose visible text is the button label. A styled button is not achievable,
  and the anchor lands in Outlook's default blue.
- The benefits heading is a `<div>` wrapping `<b>`, not an `<h1>` to `<h6>`,
  which would render oversized.

**FONT: CONFIRMED IMPOSSIBLE. NO RUN MAY EVER ATTEMPT FONT STYLING.** This is
settled, not open. Both approaches were tested and BOTH were rejected outright
by the connector, on create and on update:

- Inline style (`<div style="font-family:Aptos,'Segoe UI',sans-serif;font-size:12pt">`)
  fails; `style=` is outside the outbound allowlist.
- Legacy `<font face="Aptos" size="3">` fails; `font` is named in the reject
  list alongside `span` and `blockquote`.

The allowlist is p, br, a[href|name|target], b/strong, i/em, ul/ol/li, h1-h6,
table, code, pre, hr, div, strike, and nothing else. Bodies carrying anything
else are REJECTED, not silently cleaned, so a font attempt hard-fails the
outlook_create_draft call and takes the whole draft with it, which would abort
the morning's batch. Do not re-test either method and do not look for a third:
there is no styling hook in the allowlist at all. The drafts inherit Outlook's
default HTML font and cannot be forced to Aptos 12
through this connector. If Will needs Aptos, it has to come from a mailbox or
client setting, not from this skill.

**THIS IS THE COMPLETE COPY SPECIFICATION FOR CAMPAIGN MODE.** Everything from
here to the end of Step 4 is the whole spec: the fixed subject and its guard, the
CC, the no-ownership rule, the greeting fallback, the warm opening, the body
blocks in order, the two-block pricing-led Bonita section sourced live per Step 2
with no hardcoded figures, the bold-header bullets, the four line signature last,
no unsubscribe footer, and no font styling ever. Any future edit must PRESERVE
EVERY ITEM. When
changing one line, re-read the whole block and carry the rest forward; several
rounds of fixes have been lost by editing one item in isolation.

Structure, in this order. The benefits block sits ABOVE the signature, and the
signature is the LAST content block:

1. Greeting: `Hi {First Name},` when a first name exists, otherwise exactly
   `Hello,`.
2. WARM OPENING, then the unit line. Two separate blocks. The email opens like
   a note from a person, not a data feed, then gets to the numbers.

   Warm opening, exactly:

   `I hope your summer is going well. I run Storage Condo King, the market platform that tracks every garage and car condo project in Florida, and I wanted to make sure the numbers on {Project} were in front of you.`

   Then the unit line, exactly:

   `{Project} is tracked on the platform, and Unit {Unit} carries a current market value there along with the closed sales behind it.`

   **NEVER ASSERT OWNERSHIP.** Neither block, nor any other, may say "You own
   Unit X at Y" or any equivalent in any wording. Our data links the contact to
   the unit; it does not prove they own it today, and telling someone they own
   something they may have sold is the fastest way to lose them.

   Use the owner's LOWEST unit number per Step 3.
3. Unit link: `View Your Unit's Market Value` linking to
   `https://storagecondoking.com/projects/{URL-encoded Project}?tab=market-value&utm_source=drip&utm_campaign=bmv-owner-1`
   URL-encode the project name exactly as it appears in "01 - Projects",
   normalizing en dashes and em dashes to hyphens first per the repo join
   convention.
4. Comps paragraph: live comps from their project and submarket, unit value
   tracking, quarterly market reports, and a listing platform when they are
   ready to sell.
5. Report link: `Download the Q2 2026 Florida Market Report` linking to the
   report URL above.
6. Bonita section, PRICING LED, in TWO blocks. The math is the pitch: lead with
   the spread between what the developer is asking and what the unit is worth,
   then the product and scarcity detail. Will's voice, no hype words such as
   "incredible" or "unmatched", no em dashes or en dashes.

   First block, the pricing math:

   `We are also representing Bonita Motor Vault in Bonita Springs, and the pre-construction math is the part worth your attention. The developer is asking $540,000, or $480 per square foot, on a 1,125 square foot unit. Our valuation puts that same unit at $671,000, or $597 per square foot. That is $131,000 of day one equity and a 19.6 percent discount to market, earned at contract before a shovel moves. The submarket has compounded at 10 percent a year, with 35 sales in the trailing year at a $560 median.`

   Second block, the product and scarcity detail:

   `Buildings 1 and 2 released 21 of the 58 deeded units, 20 to 21 foot ceilings, mezzanines, Category 5 concrete in Flood Zone X. The Founding Owner Program is capped at 10 positions and 5 are left. Founding pricing ends when those fill. Groundbreaking is Q3 2026 with 2027 delivery.`

   EVERY dollar, PSF, percent and count above is a live value from Step 2. The
   shapes are models, not scripts, and the numbers shown are what the data
   happened to say on 2026-08-15. Never carry them forward. Per the Step 2 NULL
   RULE, drop any sentence whose figure comes back null and note it in the run
   report.
7. Call to action, exactly:
   `Take a look at the listing and reply if you want me to hold a unit for you.`
   followed by the listing link `See the Bonita Motor Vault listing` pointing to
   `https://storagecondoking.com/projects/Bonita%20Motor%20Vault?utm_source=drip&utm_campaign=bmv-owner-1`
   This link REPLACES the brochure link. The brochure is no longer linked in the
   campaign body.
8. Closing line, exactly:
   `Happy to answer anything about unit values or about Bonita. Just reply.`
9. Benefits block: a bold heading `Storage Condo King Unit Benefits` followed
   by a `<ul>` of exactly these five items. Each bullet carries a BOLD lead-in
   header, then a colon, then the description, worded exactly as below:
   - `<b>Live Market Values</b>: current valuations on your unit, covering both
     pre-sale and re-sale, refreshed as new sales record.`
   - `<b>Verified Sale Comps</b>: recorded closed sales across every Florida
     garage and car condo project, not asking prices.`
   - `<b>Listing Platform</b>: live listings and a marketing distribution
     network when you are ready to sell.`
   - `<b>Investment Tools</b>: cash flow models and market research built for
     owners and investors.`
   - `<b>Project Intelligence</b>: demographics, amenities, and the new supply
     pipeline for every project we track.`
10. Signature block, LAST, exactly these four lines:

```
Will Butler
Calusa Capital Partners
C: 239-898-5840
E: will.butler@calusainvestments.com
```

The campaign signature is the four line Calusa block, matching DRAFT mode, and
it is the LAST thing in the body. There is NO unsubscribe footer: Will has
instructed this directly and it is not an oversight, so never add one back.
These read as personal correspondence from a named person, not as a bulk
marketing send. Opt-outs are still honored in full through Step 6: a recipient
who replies asking out goes into "04a - Email Suppression" as 'Opt-Out' and the
Step 3 cross-check excludes them from this and every future campaign
permanently.

If "First Name" is null or blank, open with exactly `Hello,` instead of a name.
If "Unit #" is null or blank, drop the unit clause and say only that {Project}
is tracked on Storage Condo King with current market values and the closed sales
behind them. Never substitute an ownership claim for the missing unit.

Skeleton, with the greeting flush at the start and no leading whitespace:

```html
<div>Hi {First Name},</div><div><br></div><div>{warm opening}</div><div><br></div><div>{unit line}</div><div><br></div><div><a href="{unit url}">View Your Unit's Market Value</a></div><div><br></div><div>{comps paragraph}</div><div><br></div><div><a href="{report url}">Download the Q2 2026 Florida Market Report</a></div><div><br></div><div>{bonita pricing math}</div><div><br></div><div>{bonita product and scarcity}</div><div><br></div><div>Take a look at the listing and reply if you want me to hold a unit for you.</div><div><br></div><div><a href="{listing url}">See the Bonita Motor Vault listing</a></div><div><br></div><div>Happy to answer anything about unit values or about Bonita. Just reply.</div><div><br></div><div><b>Storage Condo King Unit Benefits</b></div><ul><li><b>Live Market Values</b>: ...</li></ul><div><br></div><div>Will Butler<br>Calusa Capital Partners<br>C: 239-898-5840<br>E: will.butler@calusainvestments.com</div>
```

### Step 5. Log each draft

After EACH successful draft, insert the ledger row:

```sql
insert into "04e - Campaign Sends" ("Email", "Campaign", "Project", "Unit", "Region", "Drafted At")
values (<email>, 'BMV-Owner-1', <project>, <unit>, <region>, now())
on conflict do nothing;
```

One ledger row per RECIPIENT, never one per unit. "Unit" and "Project" carry
the owner's lowest-numbered unit chosen in Step 3, which is the same unit named
in the copy. Insert only for drafts that were actually created. If a draft call
fails, write no ledger row so the contact re enters tomorrow's batch. Verify the
run with a separate query:

```sql
select count(*) from "04e - Campaign Sends"
where "Campaign" = 'BMV-Owner-1' and "Drafted At"::date = current_date;
```

### Step 6. Unsubscribe handling

The body carries NO unsubscribe footer, so opt-outs arrive as ordinary replies
and this step is the whole mechanism. Watch for them and act on every one. Any
reply asking to be removed, whether or not it uses the word unsubscribe, gets
that address added to "04a - Email Suppression" with "Suppression Type" =
'Opt-Out' and "Suppress" = true. The Step 3 suppression cross-check then
excludes the address from this and every future campaign permanently. Never
remove an Opt-Out row to re-reach someone.

### Step 7. Report

Report: gate result for both assets, any BMV fact that differed from the stock
copy, unique recipients drafted this morning, region worked, unique recipients
sent so far against that region's unique owner total, campaign total against
the eligible unique recipient population (658 as of 2026-08-12), drafts failed,
and unique recipients remaining. Count PEOPLE, not CRM rows, everywhere in this
report.

---

## Hard rules

- Never send email directly. Create drafts only. Will presses send.
- EVERY draft in EVERY mode CCs chance.friedman@calusainvestments.com. No exceptions. The old no-CC campaign exception is removed; CAMPAIGN drafts are CC'd exactly like DRAFT drafts.
- CAMPAIGN mode uses ONE fixed subject, `Your unit at {Project} and a first look at Bonita Motor Vault`. Never apply the DRAFT-mode three-subject rotation to a campaign draft.
- Campaign bodies NEVER assert ownership. No "You own Unit X at Y" or any equivalent phrasing. The unit is described as carrying a market value on the platform, never as the recipient's property.
- CAMPAIGN mode never runs while the verification queue still has something to draft, and never before the asset reachability gate passes on BOTH the brochure and the report URL. A failed gate means zero drafts and zero ledger rows that morning.
- 50 UNIQUE RECIPIENTS per morning maximum, deduplicated on lower(btrim("Email 1")) BEFORE the limit is applied, never 50 CRM rows. Owners hold multiple units, so a row limit silently under-delivers. One draft and one campaign row per address per campaign, enforced by the unique index on lower("Email") plus "Campaign" in "04e - Campaign Sends". Log the ledger row only after the draft actually exists.
- Never put a font declaration in a campaign body. Inline `style=` and the legacy `<font>` tag are both outside the connector allowlist and are REJECTED, not stripped, which hard-fails the draft call and aborts the batch. Bodies use `<div>` blocks with `<div><br></div>` spacers and start flush at the greeting.
- Run NO migrations from this skill. "04e - Campaign Sends" and the public "Marketing Materials" bucket already exist.
- Draft bodies are plain HTML with no inline style attributes. Body text stays black through the plain structure, and the value link is a standard `<a href>` anchor. The M365 draft tool strips inline styles, so the link renders in Outlook's default blue, and that is accepted. No colored fonts, images, or other styling.
- The CRM contains only verified emails. Never write an address into any CRM email column without stamping "Email Verified At" and deleting the matching 04d row in the same operation.
- 04d holds only unresolved addresses. An address must never exist in both 04d and the CRM. Resolved means deleted from 04d: good addresses go to the CRM, bad addresses go to 04a.
- Never draft to an address present in "04a - Email Suppression" with "Suppress" = true. That single table holds bounces AND unsubscribes, distinguished by "Suppression Type". There is no "04b" table; it was collapsed into 04a on 2026-08-02. Screen the batch against it before creating drafts and drop any hits, deleting their 04d row since the address is already resolved.
- Never touch Constant Contact. Suppression happens only in Supabase.
- Never reintroduce a bounced or unsubscribed address into any batch.
- 45 drafts per run maximum. Do not run DRAFT mode twice in one day unless Will explicitly asks.
- Re query after every write. Multi statement execute_sql returns only the last result.
- Bullet points in any output copy end with a period. No em dashes or en dashes anywhere, ranges use the word "to".
