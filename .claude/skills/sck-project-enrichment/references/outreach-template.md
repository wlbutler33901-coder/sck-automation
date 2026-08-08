# FL Developer Outreach - Fallback Queue Template

Used by the enrichment routine on mornings when the overnight scan surfaced no new developers.
One email per morning, one developer at a time, queued as an Outlook draft for Will to review,
attach the current Florida Market Report PDF, and send. The system never sends; it only drafts.

## Copy rules

No em-dashes or en-dashes anywhere; ranges use the word "to". Bullets end with periods. Will's
voice: warm, direct, zero sales pressure. Reference the recipient's OWN project by name (their
project, so the competitor anonymity rule does not apply); never name any other car condo or
garage condo project. One factual compliment maximum, and only if the record supports it; if
the staged data is thin, keep the opener generic rather than fabricating detail.

## Subject

{Project Name} - Storage Condo King intro

If no project name is on file: Florida garage condo market - Storage Condo King intro

## Body

{First name} - Nice to e-meet you! {Project name} looks like a great project and I would love
to figure out a way to be a resource on it or your next one. I run Storage Condo King, the
Florida garage and car condo market intelligence and listing platform, alongside Calusa Capital
Partners, our CRE financing advisory in Fort Myers. Do you have a few minutes over the next
week or two for a quick Teams intro? {If their project is in FL within roughly 2 hours of Fort
Myers, add: I am in {their metro} frequently and would love to grab a quick coffee or lunch
sometime as well!}

Here are some of the ways we can help:

Developer Service Package:

- Site Selection Valuation Report (available for any address in FL). Helpful for quickly
  underwriting proforma unit values.
- Site Selection Demographic Reports (FL).
- Development Financing and Underwriting Model.
- Website, Brand and Operations Consulting.
- Capital Markets Advisory. Debt, equity and Founding Member funding capitalization structures.
- Full-Service Unit Sales, Marketing and Distribution.
- Storage Condo King Web Platform. Developer project portals, pre-sale marketing and
  distribution network, market data and research (Florida, with GA, NC and SC coming soon),
  comp data, pre-sale and re-sale unit valuation engine, listing platform, contact directory,
  and deal email and CRM system.

Our latest Florida Garage and Car Condo Market Report is worth a skim for where pricing and
inventory are trending in {their region}:
[Q2 2026 Florida Garage and Car Condo Market Report](https://llwyvgkqhendgzsgngqh.supabase.co/storage/v1/object/public/Quarterly%20Market%20Reports/florida-car-condo-market-report-q2-2026.pdf)
Render this as an HTML hyperlink in the Outlook draft body: the linked text is "Q2 2026 Florida
Garage and Car Condo Market Report" and the href is that URL.

Best,
Will Butler
Calusa Capital Partners | Storage Condo King
will.butler@calusainvestments.com

## Personalization slots

{First name} from Contact (first token). {Project name} from source_project or the linked
project row. {their metro} and {their region} from the project's City and Region. Fill every
slot from the database; never invent.

"Recipient Email" must be a bare address with no annotations, parentheses, or secondary
addresses. Developer Email fields often store notes like "scott@example.com (direct);
info@example.com"; extract the FIRST valid address only and prefer a named-person address over
a generic info@ or legal@ inbox when both appear.

## Selection and rotation

1. RUN EVERY MORNING. One draft per morning is the target, not the exception. Selection
   priority: first, developers staged in "05 - Developers - New" within the last 26 hours that
   have a usable email and ideally a named contact, newest first; then the standing backlog
   priority (Pre-Development and Under Construction FL first, then Developer Sale, then
   Completed). A new developer with only a generic inbox and no named contact falls to the
   backlog rather than blocking the morning; log the reason. The sent-check in rules 2 and 2b
   still runs first every morning and an occupied queue still skips with outreach_skipped.
2. SENT CHECK FIRST: before drafting anyone new, take the most recent row in "Developer
   Outreach - Drafts" with Status in ('queued','draft'), ordered by "Queued At" then
   created_at. Search Outlook Sent Items for a message from
   will.butler@calusainvestments.com to that row's "Recipient Email" sent after its "Queued
   At". If found: set that row Status = 'sent' and "Sent At" to the send time, and note the
   contact in the developer's Comments. If not found: the queue is occupied; do NOT draft
   another. Log outreach_skipped, reason prior draft still pending, and stop this step.
2b. LEGACY DRAFTS: eight rows created 2026-08-04 by the per-discovery drafter have Status
   'draft' and no "Queued At". Their "Recipient Email" values have been backfilled. Treat
   them exactly like queued rows for the sent-check: if a matching message appears in Sent
   Items, mark Status 'sent' and set "Sent At". If a legacy draft is older than 14 days with
   no send and no reply, set Status 'expired' and free that developer back into the rotation,
   logging change_type 'outreach_expired'. Never delete a Drafts row.
3. SELECT the next outstanding developer only when the queue is clear: a Florida developer
   (from "05 - Developers" or approved rows in "05 - Developers - New") with a usable Email,
   no row in "Developer Outreach - Drafts" with Status in ('queued','sent','draft'), and no
   contact already noted in Comments. Priority order: developers with a Pre-Development or
   Under Construction FL project first, then Developer Sale, then Completed; ties broken by
   most recent project activity. Deterministic; no judgment calls at 4 AM. Developer rows are
   known to contain unmerged duplicates (Harrod Properties, The Vault, ReVest, Storage Caves,
   Stables Motor Condos). Match on normalized developer name and deduplicate before selecting,
   so one developer can never be drafted twice under variant records.
4. DRAFT: compose from this template, create the Outlook draft in Will's Drafts folder via the
   Microsoft 365 connector, CC chance.friedman@calusainvestments.com. Then INSERT the row into
   "Developer Outreach - Drafts" with Developer, Project, Region, Subject, Body, "Recipient
   Email", Status = 'queued', "Queued At" = now(). Log change_type = 'outreach_queued' with the
   developer name.
5. The report is linked, never attached; the draft arrives ready to send with no manual
   attachment step. When a new quarterly report PDF is uploaded to the "Quarterly Market
   Reports" bucket, this URL is updated to the newest file; check the bucket's newest object
   each run and use it.
6. If the Microsoft 365 connector is unavailable, still INSERT the Supabase row with Status =
   'draft' so nothing is lost, and log the connector failure. Never silently skip.
