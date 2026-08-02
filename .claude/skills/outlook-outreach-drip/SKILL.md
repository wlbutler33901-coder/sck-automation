---
name: outlook-outreach-drip
description: Draft 1:1 Outlook outreach emails to quarantined (unverified) SCK unit owner emails and process NDR kickbacks. Two modes. DRAFT mode (default, nightly) pulls the next batch of quarantined emails from "04d - Email Verification", personalizes a short plain text outreach sent from Will Butler's Calusa Investments mailbox with Chance Friedman CCd, saves them to Outlook Drafts so Will can press send in the morning, and stamps "Drafted At". KICKBACK mode scans the mailbox for bounce and NDR messages, marks bounced addresses in 04d, suppresses them in "04a - Email Suppression", clears them from the CRM, and promotes drafts with no kickback after 4 days to clean. Use whenever asked to run the outreach drip, draft the outreach batch, prep tomorrow's outreach emails, scan for kickbacks, process NDRs, or check outreach bounces. Requires the "Supabase - Storage Condo King" and Microsoft 365 connectors.
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

This skill runs UNATTENDED inside a scheduled Claude Code cloud routine. There
is no user to ask questions. Every run is a FULL CYCLE: KICKBACK mode first
(process NDRs and promote proven deliveries), then DRAFT mode (prepare the next
batch). On ambiguity or any unexpected state, stop that item, leave the data
untouched, and explain it in the run report instead of guessing.

Idempotence guard: before DRAFT mode, check whether any 04d row already has
"Drafted At"::date = current_date. If yes, the day's batch exists (the routine
re-ran); skip DRAFT mode and say so in the report.

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
3. `Quick question about your {Project} unit`

Body template (adjust naturally per contact, keep under 120 words):

```
Hi {First Name},

I am with Calusa Capital Partners in Fort Myers. We run Storage Condo
King, the market data platform tracking resale activity across Florida
garage and car condo projects, including {Project}.

We maintain verified sale comps for your building and I can send you a
current value estimate for your unit at no cost. Owners use these for
insurance, estate planning, or simply to know what the market is doing.

If that would be useful, just reply and I will put it together.

Best regards,

Will Butler
Calusa Capital Partners
will.butler@calusainvestments.com
storagecondoking.com
```

If "Project" is null, drop the project references and use the general Florida
market framing. Never sign as market@storagecondoking.com; the signature must
match the sending identity.

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

## Hard rules

- Never send email directly. Create drafts only. Will presses send.
- Every draft CCs chance.friedman@calusainvestments.com. No exceptions.
- The CRM contains only verified emails. Never write an address into any CRM email column without stamping "Email Verified At" and deleting the matching 04d row in the same operation.
- 04d holds only unresolved addresses. An address must never exist in both 04d and the CRM. Resolved means deleted from 04d: good addresses go to the CRM, bad addresses go to 04a.
- Never draft to an address present in "04a - Email Suppression" with "Suppress" = true. That single table holds bounces AND unsubscribes, distinguished by "Suppression Type". There is no "04b" table; it was collapsed into 04a on 2026-08-02. Screen the batch against it before creating drafts and drop any hits, deleting their 04d row since the address is already resolved.
- Never touch Constant Contact. Suppression happens only in Supabase.
- Never reintroduce a bounced or unsubscribed address into any batch.
- 45 drafts per run maximum. Do not run DRAFT mode twice in one day unless Will explicitly asks.
- Re query after every write. Multi statement execute_sql returns only the last result.
- Bullet points in any output copy end with a period. No em dashes or en dashes anywhere, ranges use the word "to".
