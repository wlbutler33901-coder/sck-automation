---
name: outlook-unit-owner-drip
description: Draft 1:1 Outlook outreach emails to quarantined (unverified) SCK UNIT OWNER emails, process NDR kickbacks, and run the BMV owner marketing campaign. This skill owns the UNIT OWNER side only; developer outreach lives in the separate outlook-developer-drip skill and the two never share a queue. Three modes. DRAFT mode (default, nightly) pulls the next batch of quarantined emails from "04d - Email Verification", personalizes a short plain text outreach sent from Will Butler's Calusa Investments mailbox with Chance Friedman CCd, saves them to Outlook Drafts so Will can press send in the morning, and stamps "Drafted At". KICKBACK mode scans the mailbox for bounce and NDR messages, marks bounced addresses in 04d, suppresses them in "04a - Email Suppression", clears them from the CRM, and promotes drafts with no kickback after 4 days to clean. CAMPAIGN mode runs only after the verification queue is empty and drafts up to 50 UNIQUE Bonita Motor Vault owner recipients per morning from "04 - Unit Owner CRM" in region order, deduplicated by email so multi-unit owners are contacted once, logging each to "04e - Campaign Sends". Use whenever asked to run the outreach drip, draft the outreach batch, prep tomorrow's outreach emails, scan for kickbacks, process NDRs, check outreach bounces, or run the BMV owner campaign. Requires the "Supabase - Storage Condo King" and Microsoft 365 connectors.
---

# SCK Outlook Unit Owner Drip

**SCOPE.** This skill owns UNIT OWNER correspondence only: the verification drip
against "04d - Email Verification" and the BMV owner campaign against
"04 - Unit Owner CRM". DEVELOPER outreach is a separate skill,
`outlook-developer-drip`, with its own queue, its own rotation and its own
correspondence gate. The two never share a queue, a ledger or a rotation, and
neither one may draft into the other's audience. Renamed from
`outlook-outreach-drip` on 2026-08-22 when the split happened; behavior is
unchanged, and LEARNINGS.md entries tagged `outlook-outreach-drip` are this
skill's history and still bind.

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

The body links exactly TWO destinations: the recipient's project page and the
Bonita listing page. Both are pages on the same site. Gate the Bonita listing
URL with a HEAD or ranged GET before building a single draft:

- Listing (page): https://storagecondoking.com/projects/Bonita%20Motor%20Vault?utm_source=drip&utm_campaign=bmv-owner-1

The listing URL passes on any 2xx. It is a web page, not a PDF, so do not
apply a content type test to it; a redirect that lands on a 2xx is fine, a
404 or 5xx is not.

If the listing fails, draft NOTHING for this campaign. Insert no ledger rows,
log the failure as a learning, and state plainly in the run summary which URL
failed and with what status. Fifty emails carrying a dead link is worse than a
day's delay, and the campaign simply resumes the next morning once the asset is
in place. This gate is never bypassed or worked around.

The quarterly market report PDF is NO LONGER LINKED in the campaign body and is
NO LONGER GATED. The report now appears only as a phrase inside the Verified
Sale Comps bullet. Do not fetch it, do not gate on it, and do not let a bad
report URL block the campaign. The brochure is likewise not linked and not
gated; the "Marketing Materials" bucket state does not block this campaign.

### Step 2. Pull the live BMV pricing data

**HARD RULE: NO HARDCODED FIGURES.** Every dollar and every percent in the
Bonita section comes from the RPC or the live table on the run that drafts it,
so the email can never contradict the listing page. The example numbers in the
target shape below are illustration only, never values to copy.

Run this once per run. It returns every figure the Bonita paragraph and the
P.S. need:

```sql
with p as (
  select "Unit Size"::numeric as sf, "Asking $ PSF"::numeric as ask_psf,
         "Appraised $ / SF"::numeric as val_psf, "# of Units" as units,
         "Founding Cap" as cap, "Units Committed" as committed,
         "Ground Breaking" as gb, "Deposit Refundable" as deposit_refundable,
         "Developer Listing Comments" as listing_comments
  from "06 - Pre-Sales" where "Project" = 'Bonita Motor Vault'
), j as (
  select "Key Amenities" as amenities, "Construction Materials" as materials,
         "Flood Zone" as flood_zone, "Units" as project_units
  from "01 - Projects" where "Project Name" = 'Bonita Motor Vault'
), r as (
  select (get_presale_appraisal_data('Bonita Motor Vault') -> 'project_context') as pc
)
select p.sf, p.ask_psf, p.val_psf,
       floor(p.ask_psf * p.sf / 1000) * 1000 as asking_price,
       floor(p.val_psf * p.sf / 1000) * 1000 as market_value,
       floor((p.val_psf - p.ask_psf) * p.sf / 1000) * 1000 as discount_dollars,
       round((p.val_psf - p.ask_psf) / p.val_psf * 100, 1) as discount_pct,
       p.gb, p.deposit_refundable,
       p.units, p.cap, p.committed, (p.cap - p.committed) as positions_left,
       p.listing_comments,
       j.amenities, j.materials, j.flood_zone, j.project_units,
       (r.pc ->> 'annual_appreciation_pct') as annual_growth_pct
from p, j, r;
```

Field sourcing, exactly:

- Asking PSF, valuation PSF and average unit size come from "06 - Pre-Sales"
  ("Asking $ PSF", "Appraised $ / SF", "Unit Size").
- Asking price, market value and dollar discount are DERIVED as PSF times unit
  size.
- "Ground Breaking" and "Deposit Refundable" come from "06 - Pre-Sales" and
  drive the two conditional clauses in the P.S. per Step 4 Block 4.

- `amenities`, `materials`, `flood_zone` and `project_units` come from
  "01 - Projects" and feed the Block 2 specs sentence. `listing_comments`
  supplies the release counts in that same sentence.

**REPORT ONLY, NEVER COPY.** `cap`, `committed`, `positions_left` and
`annual_growth_pct` are pulled for the run report and for cross-checking. NONE
of them may appear in a campaign body. The founding position counts are barred
outright by the no-characterizing-sales rule in Block 4, and the Bonita
submarket growth belongs to the listing page, not to this email.

**ROUNDING, follow exactly or the email will disagree with the listing page.**
FLOOR every dollar figure to the nearest $1,000. Compute the discount percent
from the UNROUNDED values and round to one decimal. "Appraised $ / SF" is
stored already rounded, so deriving dollars from it and then rounding up would
overstate the equity and drift off the published valuation; flooring reconciles
to the listing page and is the conservative direction for a discount claim.
Verified on 2026-08-15: $480 and $597 PSF on 1,125 SF floor to $540,000 asking
and $671,000 value, a $131,000 discount at 19.6 percent, which matches the
published appraisal.

- NULL RULE. If ANY figure comes back null, OMIT the sentence that carries it
  rather than inventing a value, and note the omission in the run report. The
  rest of the Bonita paragraph still sends. This applies to every figure.
- Cross-check unit count, delivery year and flood zone against "01 - Projects".
  Report any mismatch rather than silently rewriting the copy.

### Step 2b. Pull the per-recipient unit value data

Block 1 of the body carries ONE personalized sentence about the recipient's own
unit. Run this ONCE for the whole batch after Step 3 has chosen the recipients,
feeding the chosen (project, unit) pairs into `picks`:

```sql
with picks as (
  select * from (values
    ('The Motor Enclave','117'), ('The Motor Enclave','1117')  -- one row per recipient
  ) as t(project, unit)
), u as (
  select p.project, p.unit,
         un."Suite Size (SF)"::numeric as sf,
         un."Appraised $ / SF"::numeric as psf,
         un."Suite Size (SF)"::numeric * un."Appraised $ / SF"::numeric as value_raw
  from picks p
  join "02 - Units" un
    on un."Project" = p.project and btrim(un."Unit #") = btrim(p.unit)
), s as (
  select distinct on (project_name, unit) project_name, unit, sale_date, sale_price
  from (
    select distinct "Project Name" as project_name, btrim("Unit") as unit,
      case
        when "Sale Date" ~ '^\d{1,2}/\d{1,2}/\d{4}$' then to_date("Sale Date",'MM/DD/YYYY')
        when "Sale Date" ~ '^\d{1,2}/\d{1,2}/\d{2}$'  then to_date("Sale Date",'MM/DD/YY')
        when "Sale Date" ~ '^\d{4}-\d{2}-\d{2}$'      then to_date("Sale Date",'YYYY-MM-DD')
      end as sale_date,
      "Sale Price"::numeric as sale_price
    from "03 - Sales" where "Project Name" in (select project from picks)
  ) d
  where sale_date is not null
  order by project_name, unit, sale_date desc, sale_price desc
)
select u.project, u.unit,
       round(u.value_raw / 1000) * 1000 as unit_value,
       round(u.psf)                     as unit_psf,
       to_char(s.sale_date, 'FMMonth YYYY') as sale_label,
       s.sale_price,
       round((u.value_raw - s.sale_price) / 1000) * 1000 as increase,
       split_part(pr."Submarket", ';', 1)   as submarket_label,
       rd.psf_growth_5yr_ann_pct            as submarket_growth_pct,
       rd.unit_sales_ttm                    as submarket_sales_ttm,
       rd.median_psf_ttm                    as submarket_median_psf_ttm
from u
left join s  on s.project_name = u.project and s.unit = btrim(u.unit)
left join "01 - Projects" pr on pr."Project Name" = u.project
left join "Region Definition" rd on rd.submarket = pr."Submarket"
order by u.project, u.unit;
```

Sourcing and mechanics, exactly:

- Unit value is "Suite Size (SF)" times "Appraised $ / SF" from "02 - Units",
  matched on "Project" plus "Unit #". PSF is that same "Appraised $ / SF".
- The prior sale comes from "03 - Sales", matched on "Project Name" plus
  "Unit", taking the MOST RECENT sale by parsed date.
- "Sale Date" is TEXT in mixed formats, so parse with the three branch CASE
  above. As of 2026-08-16 the table holds 1,525 rows as M/D/YY and 186 as
  M/D/YYYY; the ISO branch is carried because the ingest skills can write it.
  Anything the CASE cannot parse yields null and is dropped, never guessed.
- Some units carry DUPLICATE sale rows. The inner `distinct` dedupes on date
  and price before `distinct on` picks the latest, so a doubled row cannot
  win by tiebreak.
- ROUNDING here is round-to-nearest thousand for the value and the increase,
  and round-to-nearest dollar for the PSF. This differs from the Bonita floor
  rule in Step 2 on purpose: the Bonita figures must reconcile to a published
  listing page, these do not.
- Submarket label is the text BEFORE the first semicolon in
  "01 - Projects"."Submarket". The stored value is a pair such as
  `Tampa; Brandon`, which reads wrong in a sentence, so the label is `Tampa`.
- Submarket growth is "Region Definition".psf_growth_5yr_ann_pct, the
  annualized five year PSF growth, matched on the FULL stored submarket value.
  **Never substitute psf_growth_1yr_pct for it.** The one year figure is
  volatile and frequently NEGATIVE (Naples; Bonita Springs is -3.8 as of
  2026-08-16), and Block 1 may never carry a decline. When
  psf_growth_5yr_ann_pct is null, the submarket sentence is simply omitted;
  most submarkets are null today, so omission is the normal case, not a fault.
- Trailing-year color (`unit_sales_ttm`, `median_psf_ttm`) comes from the SAME
  "Region Definition" row, which is the segmentation KPI table the Market
  Research pages read. Taking all three figures from one row keeps growth,
  count and median internally consistent. `get_market_segmentation_v2` was
  evaluated on 2026-08-17 and rejected as the source for this clause: it
  exposes `avg_psf` only, with no median at all, and its rolling window returns
  a slightly different count (42 versus 44 for Tampa; Brandon), so mixing the
  two would print a count and a median that disagree. Use it only to
  cross-check, never to compose.

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

`Your {Project} unit value, plus founding pricing at Bonita Motor Vault`

**SUBJECT ONLY: strip a leading `The `.** In the subject line, and NOWHERE else,
drop a leading `The ` from the project name so the possessive reads naturally.
`The Motor Enclave` becomes `Your Motor Enclave unit value, plus founding pricing
at Bonita Motor Vault`. Strip only a leading `The ` followed by a space; leave
the name otherwise untouched, and leave every in-body reference to the project at
its full stored name.

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
here to the end of Step 4 is the whole spec: the fixed subject with its leading
`The ` strip and its guard, the CC, the no-ownership rule, the greeting fallback,
the FOUR BLOCK body, the merged single-paragraph opening, the conditional unit
value sentence with its trailing-year market color, the arrow on both link
anchors, the one paragraph three sentence Bonita section sourced live per Step 2
with no hardcoded figures, the bold-header bullets, the four line signature, the
conditional two sentence P.S., no unsubscribe footer, and no font styling ever.
Any future edit must PRESERVE EVERY ITEM. When changing one line, re-read the
whole block and carry the rest forward; several rounds of fixes have been lost by
editing one item in isolation.

The body is FOUR BLOCKS, in this order, and is deliberately SHORTER than the
version it replaced on 2026-08-16. What was cut is cut on purpose: the standalone
comps paragraph (redundant with the benefits list), the market report paragraph
and its download link (now a phrase inside one bullet), the Bonita specs
paragraph (the listing page carries it), the standalone "Take a look at the
listing" line and the standalone closing line (both folded into the Bonita
paragraph). Do not restore any of them.

#### BLOCK 1. Intro and unit value

**ONE PARAGRAPH, NOT FOUR.** The greeting is its own block, and EVERYTHING else
in Block 1 before the link is a SINGLE paragraph: the warm opener, the platform
sentence and the personalized closing sentence run together in one `<div>`. The
four short stacked paragraphs this replaced on 2026-08-17 read as a form letter;
one paragraph reads as a note. Never split them apart again.

1. Greeting, its own block: `Hi {First Name},` when a first name exists,
   otherwise exactly `Hello,`.
2. ONE paragraph, opening exactly:

   `I hope your summer is going well. I run Storage Condo King, the market platform that tracks every garage and car condo project in Florida, and I wanted to put the numbers on {Project} in front of you.`
3. Then the personalized closing sentence, APPENDED TO THAT SAME PARAGRAPH after
   a single space, never as a new block. Chosen by this priority; take the FIRST
   variant that resolves and append nothing at all if none do:

   a. Unit has an appraised value AND a most recent recorded sale AND the change
      is POSITIVE and at least $25,000:

      `Unit {Unit} currently values at {$value}, or {$psf} per square foot, up about {$increase} from its {Month Year} sale.`

   b. Else, unit has an appraised value:

      `Unit {Unit} currently values at {$value}, or {$psf} per square foot.`

      Follow it, in the same paragraph, with the submarket sentence when
      `submarket_growth_pct` is not null.

   c. Else the submarket sentence alone, and only when growth is available.

   **THE SUBMARKET SENTENCE**, with trailing-year color when available:

   `Values in the {Submarket} submarket have compounded at {x} percent a year, with {n} units trading in the trailing year at a {$median} per square foot median.`

   The stored median is a PSF median, not a price, so the copy says `per square
   foot median` and never implies a median sale price.

   The trailing-year clause is OPTIONAL and additive. Ship it only when BOTH
   `submarket_sales_ttm` and `submarket_median_psf_ttm` come back non-null; if
   either is null, end the sentence after `a year.` and note the omission in the
   run report. The clause never ships on its own: it hangs off the compounding
   sentence, so a null growth figure drops the whole sentence including the
   color.

   **HARD RULE, NEVER STATE A DECLINE.** Never state a decrease, never state a
   change of zero, and never compare to a prior sale unless the change is
   POSITIVE and at least $25,000. Roughly half of these owners are currently
   below their last recorded sale price; every one of them receives variant b,
   with no comparison of any kind. A near-flat change is also barred, which is
   what the $25,000 floor is for: "up about $3,000 from its 2024 sale" reads as
   a bad investment even though the sign is positive. When in doubt, drop to b.

   Value and increase round to the nearest thousand, PSF to the nearest dollar,
   per Step 2b. `{Month Year}` is the `sale_label`, e.g. `December 2023`.
   `{Submarket}` is the `submarket_label`, the text before the first semicolon.

   **NEVER ASSERT OWNERSHIP.** No block may say "You own Unit X at Y" or any
   equivalent in any wording. Our data links the contact to the unit; it does
   not prove they own it today, and telling someone they own something they may
   have sold is the fastest way to lose them. "Unit {Unit} currently values at"
   is a statement about the unit, not about the reader, and that is the line.

   Use the owner's LOWEST unit number per Step 3. If "Unit #" is null or blank,
   variants a and b cannot resolve; fall to c, and omit the block if growth is
   null too. Never substitute an ownership claim for a missing unit.
4. Unit link, anchor text exactly `View Your Unit's Market Value →`, linking to
   `https://storagecondoking.com/projects/{URL-encoded Project}?tab=market-value&utm_source=drip&utm_campaign=bmv-owner-1`
   URL-encode the project name exactly as it appears in "01 - Projects",
   normalizing en dashes and em dashes to hyphens first per the repo join
   convention. The link ships even when the personalized sentence was omitted.

**LINK ARROWS.** Both anchors in the body end with a space and the UNICODE RIGHT
ARROW `→` (U+2192). Not `->`, not `&gt;`, not `&rarr;` as an entity, not an
image, and not a styled pseudo-element. It is ordinary text inside the anchor,
so it survives the connector allowlist exactly as the label does. Verified
against the connector on 2026-08-17 by reading a draft back.

#### BLOCK 2. Bonita, ONE paragraph

One paragraph of THREE sentences, then the listing link. Every dollar, percent
and count is a live value from Step 2, never hardcoded. The numbers below are
what the data happened to say on 2026-08-17 and are illustration only:

`We are also representing Bonita Motor Vault in Bonita Springs, where the developer is asking $540,000 or $480 per square foot against our $671,000 valuation, which is $131,000 of day one equity at a 19.6 percent discount to market, earned at contract before a shovel moves. Buildings 1 and 2 released 21 of the 58 deeded units, with clear heights over 18 feet, mezzanines, and block construction in Flood Zone X. Happy to answer anything about unit values or about Bonita. Just reply.`

The MIDDLE sentence is the property and market intel, added 2026-08-17. It sits
between the pricing sentence and the reply ask, and it is ONE sentence: this is
NOT the deleted specs paragraph coming back, and it never grows into a second
block. Source it live:

- Release counts (`{n} of the {total} deeded units`) come from
  "06 - Pre-Sales"."Developer Listing Comments", which states the initial
  release, cross-checked against "# of Units" and "01 - Projects"."Units" for
  the total. As of 2026-08-17 that reads "Initial release is Buildings 1 and 2,
  21 of the 58 units."
- Clear height, mezzanine and any other spec come from
  "01 - Projects"."Key Amenities", construction from
  "01 - Projects"."Construction Materials", and the zone from
  "01 - Projects"."Flood Zone".
- **Render the amenities as PLAIN PROSE, never the canonical strings.** The
  stored values are catalog labels for the platform UI, not sentence fragments.
  `18'+ Clear Heights` becomes `clear heights over 18 feet`,
  `Mezzanine Capabilities` becomes `mezzanines`, and `Block` becomes
  `block construction`. Never paste a canonical label straight into the copy.
- OMIT any clause whose source is null, keeping the sentence grammatical, and
  note the omission in the run report. If the release counts are unavailable,
  drop the whole sentence rather than leading with the specs.

Then the listing link, anchor text exactly `See the Bonita Motor Vault listing →`,
pointing to
`https://storagecondoking.com/projects/Bonita%20Motor%20Vault?utm_source=drip&utm_campaign=bmv-owner-1`

Will's voice, no hype words such as "incredible" or "unmatched", no em dashes or
en dashes. Per the Step 2 NULL RULE, drop any clause whose figure comes back
null and note it in the run report; the reply ask in the second sentence always
ships.

#### BLOCK 3. Benefits

A bold heading `Storage Condo King Unit Benefits` followed by a `<ul>` of
exactly these five items. Each bullet carries a BOLD lead-in header, then a
colon, then the description, worded exactly as below:

- `<b>Live Market Values</b>: current valuations on your unit, covering both
  pre-sale and re-sale, refreshed as new sales record.`
- `<b>Verified Sale Comps</b>: recorded closed sales across every Florida
  garage and car condo project, not asking prices, plus quarterly Florida
  market reports.`
- `<b>Listing Platform</b>: live listings and a marketing distribution
  network when you are ready to sell.`
- `<b>Investment Tools</b>: cash flow models and market research built for
  owners and investors.`
- `<b>Project Intelligence</b>: demographics, amenities, and the new supply
  pipeline for every project we track.`

The `plus quarterly Florida market reports` tail on the second bullet is the
ONLY place the market report appears now. Its paragraph and download link are
gone from the body and the report URL is out of the Step 1 gate.

#### BLOCK 4. Signature, then P.S.

Signature block, exactly these four lines:

```
Will Butler
Calusa Capital Partners
C: 239-898-5840
E: will.butler@calusainvestments.com
```

Then the P.S., which is the LAST content block, after the signature. It was cut
to roughly half its length on 2026-08-17; TWO sentences, not four:

`P.S. Founding pricing closes when Bonita breaks ground, which is weeks away. The listing link above is the fastest way to lock the current ask and pick your unit.`

THREE CONDITIONS, checked from live data on EVERY run, never assumed:

1. **Groundbreaking timing.** `which is weeks away` ships ONLY when
   "Ground Breaking" resolves to a date within 90 days of the run date. The
   value is TEXT: resolve a quarter string such as `Q3 2026` to the END of that
   quarter (Q1 Mar 31, Q2 Jun 30, Q3 Sep 30, Q4 Dec 31), and use a parseable
   date as given. If it resolves further out than 90 days, state the date
   instead:

   `P.S. Founding pricing closes when Bonita breaks ground, which is {Ground Breaking value}. The listing link above is the fastest way to lock the current ask and pick your unit.`

   If it is null, `Delivered`, or does not resolve to a date at all, drop the
   `, which is ...` clause and end the first sentence at `breaks ground.`
   As of 2026-08-17 the value is `Q3 2026`, resolving to 2026-09-30, which is
   inside 90 days, so `weeks away` ships.
2. **Refundable deposit clause.** A refundable-deposit claim ships ONLY when
   "06 - Pre-Sales"."Deposit Refundable" CONFIRMS it (a 'Yes' or equivalent
   affirmative), appended to the second sentence as
   `, and the deposit is fully refundable`. If that field is null or does not
   confirm, it does not appear at all. As of 2026-08-17 Bonita Motor Vault's
   "Deposit Refundable" is NULL, so the clause is ABSENT. Do not ship it back on
   a guess; it is a contractual claim.
3. **Never characterize how much has sold.** No "majority sold", "nearly gone",
   "most positions taken", "filling fast", or any equivalent, and no founding
   position counts at all. The live record shows half the founding positions
   still open (cap 10, committed 5 as of 2026-08-17), so any stronger claim
   would be FALSE. Urgency comes ONLY from the groundbreaking date and the
   founding pricing close, both of which are dated facts. The deeded unit counts
   in the Block 2 specs sentence are a description of the release, not a
   sell-through claim, and are the only counts permitted anywhere in the body.

There is NO unsubscribe footer: Will has instructed this directly and it is not
an oversight, so never add one back. These read as personal correspondence from
a named person, not as a bulk marketing send. Opt-outs are still honored in full
through Step 6: a recipient who replies asking out goes into "04a - Email
Suppression" as 'Opt-Out' and the Step 3 cross-check excludes them from this and
every future campaign permanently.

Skeleton, with the greeting flush at the start and no leading whitespace:

```html
<div>Hi {First Name},</div><div><br></div><div>I hope your summer is going well. I run Storage Condo King, the market platform that tracks every garage and car condo project in Florida, and I wanted to put the numbers on {Project} in front of you. {unit value sentence}</div><div><br></div><div><a href="{unit url}">View Your Unit's Market Value →</a></div><div><br></div><div>{bonita paragraph}</div><div><br></div><div><a href="{listing url}">See the Bonita Motor Vault listing →</a></div><div><br></div><div><b>Storage Condo King Unit Benefits</b></div><ul><li><b>Live Market Values</b>: ...</li></ul><div><br></div><div>Will Butler<br>Calusa Capital Partners<br>C: 239-898-5840<br>E: will.butler@calusainvestments.com</div><div><br></div><div>{p.s.}</div>
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

Report: gate result for the listing URL, the live Bonita figures used, which
unit value variant each recipient received (a, b, c, or omitted) as counts, any
sentence dropped by the NULL RULE, which P.S. conditions resolved on and off,
any BMV fact that differed from "01 - Projects", unique recipients drafted this morning, region worked, unique recipients
sent so far against that region's unique owner total, campaign total against
the eligible unique recipient population (658 as of 2026-08-12), drafts failed,
and unique recipients remaining. Count PEOPLE, not CRM rows, everywhere in this
report.

---

## Hard rules

- Never send email directly. Create drafts only. Will presses send.
- EVERY draft in EVERY mode CCs chance.friedman@calusainvestments.com. No exceptions. The old no-CC campaign exception is removed; CAMPAIGN drafts are CC'd exactly like DRAFT drafts.
- CAMPAIGN mode uses ONE fixed subject, `Your {Project} unit value, plus founding pricing at Bonita Motor Vault`, with a leading `The ` stripped from the project name in the SUBJECT ONLY. Never apply the DRAFT-mode three-subject rotation to a campaign draft.
- Both body link anchors end with a space and the unicode right arrow `→`. Never `->`, never an entity, never styling.
- Campaign bodies NEVER assert ownership. No "You own Unit X at Y" or any equivalent phrasing. The unit is described as carrying a market value on the platform, never as the recipient's property.
- CAMPAIGN mode never runs while the verification queue still has something to draft, and never before the asset reachability gate passes on the Bonita listing URL. That URL is the only gated asset: the report PDF and the brochure are no longer linked in the body, so neither is fetched or gated. A failed gate means zero drafts and zero ledger rows that morning.
- Campaign bodies NEVER state a decline, a flat change, or a below-purchase value. The unit value sentence compares to a prior sale ONLY when the change is positive and at least $25,000; otherwise it states the current value alone. About half of these owners sit below their last recorded sale, and a mass email that tells them so is unrecoverable.
- The campaign P.S. never characterizes how much of Bonita has sold. No "majority sold", "nearly gone", "filling fast", and no position counts. Half the founding positions are open, so any such claim would be false. Urgency comes only from the groundbreaking date and the founding pricing close.
- The refundable deposit clause in the P.S. ships only when "06 - Pre-Sales"."Deposit Refundable" confirms it. It is a contractual claim and is currently DROPPED, because that field is null for Bonita Motor Vault.
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
