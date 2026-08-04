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

I have also attached our latest Florida Garage and Car Condo Market Report, worth a skim for
where pricing and inventory are trending in {their region}.

Best,
Will Butler
Calusa Capital Partners | Storage Condo King
will.butler@calusainvestments.com

## Personalization slots

{First name} from Contact (first token). {Project name} from source_project or the linked
project row. {their metro} and {their region} from the project's City and Region. Fill every
slot from the database; never invent.

## Selection and rotation

1. TRIGGER: run this step only when the last 26 hours produced zero new developer rows in
   "05 - Developers - New". On nights with new developers, the existing per-discovery drafter
   handles outreach and this step is skipped (log outreach_skipped, reason new developers
   found).
2. SENT CHECK FIRST: before drafting anyone new, take the most recent row in "Developer
   Outreach - Drafts" with Status = 'queued'. Search Outlook Sent Items for a message from
   will.butler@calusainvestments.com to that row's "Recipient Email" sent after its "Queued
   At". If found: set that row Status = 'sent' and "Sent At" to the send time, and note the
   contact in the developer's Comments. If not found: the queue is occupied; do NOT draft
   another. Log outreach_skipped, reason prior draft still pending, and stop this step.
3. SELECT the next outstanding developer only when the queue is clear: a Florida developer
   (from "05 - Developers" or approved rows in "05 - Developers - New") with a usable Email,
   no row in "Developer Outreach - Drafts" with Status in ('queued','sent','draft'), and no
   contact already noted in Comments. Priority order: developers with a Pre-Development or
   Under Construction FL project first, then Developer Sale, then Completed; ties broken by
   most recent project activity. Deterministic; no judgment calls at 4 AM.
4. DRAFT: compose from this template, create the Outlook draft in Will's Drafts folder via the
   Microsoft 365 connector, CC chance.friedman@calusainvestments.com. Then INSERT the row into
   "Developer Outreach - Drafts" with Developer, Project, Region, Subject, Body, "Recipient
   Email", Status = 'queued', "Queued At" = now(). Log change_type = 'outreach_queued' with the
   developer name.
5. The PDF attachment is Will's step. The morning digest reminds him: attach the current
   Florida Market Report PDF before sending. Never claim in the email body that anything was
   attached by anyone but Will; the body's attachment sentence is written for the email HE
   sends.
6. If the Microsoft 365 connector is unavailable, still INSERT the Supabase row with Status =
   'draft' so nothing is lost, and log the connector failure. Never silently skip.
