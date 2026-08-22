---
name: outlook-developer-drip
description: Draft developer outreach emails into Will Butler's Outlook Drafts, two per weekday morning, one per lane. Lane A is the new-development intro to a developer behind a newly discovered project. Lane B rotates through live "05 - Developers" contacts not yet touched by that lane and pitches the expanded capabilities of Storage Condo King, including an offer to blast their projects to the SCK unit owner and buyer database. Both lanes run an outbound correspondence gate across ALL Outlook folders before queuing anything, honor the deleted-draft branch, and log to "Developer Outreach - Drafts". Use whenever asked to run the developer drip, draft developer outreach, prep the morning developer emails, run Lane A or Lane B, or check the developer outreach queue. Requires the "Supabase - Storage Condo King" and Microsoft 365 connectors.
---

# SCK Outlook Developer Drip

**SCOPE.** This skill owns DEVELOPER correspondence only. Unit owner
correspondence, the verification drip and the BMV owner campaign belong to
`outlook-unit-owner-drip`. The two skills never share a queue, a ledger or a
rotation, and neither may draft into the other's audience. Split out of
`outlook-outreach-drip` on 2026-08-22.

Target: **2 developers per weekday morning, one per lane.** Never more. A lane
that cannot produce a candidate produces nothing and says why; it does not
borrow the other lane's slot.

- **Lane A, new developments.** The existing rotation: an intro draft to the
  developer behind a newly discovered project. Lane value `car-condo`.
- **Lane B, existing developers.** A rotation through live "05 - Developers"
  contacts not yet touched by this lane, themed on the expanded capabilities of
  Storage Condo King. Lane value `developer-capabilities`.

Weekdays only. On Saturday and Sunday the skill runs no lane and logs
`outreach_skipped` with reason `weekend`.

## Connectors required

- "Supabase - Storage Condo King" (project llwyvgkqhendgzsgngqh). All
  identifiers double quoted. Multi statement execute_sql returns only the last
  result, so run every verification as a separate call.
- Microsoft 365 (Outlook tools), signed in as will.butler@calusainvestments.com.

**Mailbox precondition, verify before drafting.** Call the M365 get_me tool
first. If the signed-in address is not will.butler@calusainvestments.com, STOP,
create no drafts, write no rows, and report the mismatch. This is a hard stop,
never a warning to work around.

## Ledger

Both lanes log to "Developer Outreach - Drafts" (columns id, created_at,
Developer, Project, Region, Subject, Body, Status, "Sent At", "Recipient Email",
"Queued At", Lane).

**LANE FILTER, absolute.** Every read and every write this skill makes against
that table filters on the lane it is currently running, and every row it inserts
carries that lane's value. Lane A sees only `car-condo`. Lane B sees only
`developer-capabilities`. Neither lane may count, mark sent, expire or select
against a row belonging to the other lane, or to the Monday `calusa-cre` lane
owned by `cre-report-writer`. Lane leakage has broken this queue before; the
filter is not optional and is never widened for convenience.

---

## Step 1 - OUTBOUND CORRESPONDENCE GATE (both lanes, before queuing anything)

**This gate runs on every candidate in both lanes, before a draft is composed.**

Search Outlook across **ALL FOLDERS, Sent Items included**, for any
correspondence with the candidate in the **last 90 days**, matching on EITHER:

1. the candidate's exact recipient email address, or
2. the **domain** of that address.

Search both directions: mail we sent them and mail they sent us. Do not scope
the search to a single folder, and do not scope it to Sent Items alone; a reply
Will wrote from his phone, a thread sitting in the Inbox, and an archived
exchange all count.

**SEARCH ADDRESS FIELDS ONLY. NEVER FULL-TEXT BODY.** The gate asks who Will has
corresponded WITH, which lives in the From, To and CC fields. Run it with the
`sender` and `recipient` parameters, once each, so the match is on an address.
Do NOT use the free-text `query` parameter, which searches subject, body and
attachments and answers a completely different question.

CONFIRMED FAILURE, 2026-08-22: a full-text search for `octaneparks.com` returned
three of Will's own SCK Daily Intelligence Briefs, because the scanner had
listed the domain in the body of the digest. On a body search, every developer
the pipeline discovers gates itself the morning after discovery, since the
digest that surfaced them mentions their domain. Re-running the same candidate
with `recipient` returned zero rows, which was the truth: no correspondence had
ever taken place. A body mention is not correspondence.

**ANY HIT MEANS SKIP.** Do not draft. Mark the queue row
`held - existing correspondence <date>` using the date of the most recent hit,
log `outreach_skipped` with the matched address or domain and that date, and
**rotate to the next candidate** in the same lane. Repeat the gate on the next
candidate; a lane may walk several candidates in one morning before it finds a
clean one.

**Why the domain, not just the address.** A developer who wrote in through the
site and got a manual reply from Will must never receive an automation intro the
next morning. The inbound address is frequently a different mailbox at the same
firm than the one on the developer card, so an address-only check misses it. The
domain test is what closes that hole. Free-mail domains (gmail.com, yahoo.com,
outlook.com, hotmail.com, aol.com, icloud.com, me.com, msn.com, comcast.net,
att.net, bellsouth.net, verizon.net) are matched on the **full address only**,
never on the domain, or every gmail contact would gate every other gmail contact.

A held row is not a dead row. It is released back into its lane's rotation once
the 90 day window has passed with no further correspondence.

## Step 2 - DELETED-DRAFT BRANCH (both lanes)

Before selecting a new candidate, check the lane's outstanding queue rows
(Status in `queued`, `draft`) against Outlook.

If a queued draft is found in **Deleted Items**, set that row's Status to
`declined - draft deleted in Outlook`, stamp "Sent At" null, log
`outreach_declined`, and **free the rotation** so the lane may select a new
candidate this morning.

**A deletion is a decision, not an error state.** Will deleting a draft is him
saying no to that outreach. Never re-draft that developer for the same lane,
never treat the deletion as a failed send to retry, and never raise it as a
warning that needs investigation. Record it and move on.

If a queued draft is still sitting in Drafts, the queue is occupied: log
`outreach_skipped` with reason `prior draft still pending` and run no new draft
in that lane this morning. If a matching message appears in Sent Items after the
row's "Queued At", mark the row `sent` with "Sent At" set, note the contact in
the developer's Comments, and the lane is free.

## Step 3 - KNOWN-CONTACT CROSS-REFERENCE (both lanes, before drafting)

Run the cross-reference exactly as specified in `sck-project-enrichment`
Step 4e against "08 - Brokers", "05 - Developers",
"05 - Developers - All Property Types", "09 - Lenders" and
"04 - Unit Owner CRM", matching on exact email (split multi-address cells on
';', lower, trim) and normalized name.

- A recipient who matches "08 - Brokers" gets **no developer pitch**. Log
  `broker_lead_flag` and rotate to the next candidate. A broker marketing a
  project is a listing signal, not a developer.

**SELF-LISTING DEVELOPER EXCEPTION.** A developer who sells in house legitimately
appears in BOTH tables, and the guard must not treat that as a broker match.
PROCEED with the draft when BOTH of these hold:

1. the "08 - Brokers" row carries the SAME FIRM NAME as the developer
   (normalized: lower, trim, dashes normalized), AND
2. the broker row's email DOMAIN is the developer's OWN domain.

That combination is an in-house sales desk, not a third party marketing someone
else's project, and the reason the guard exists does not apply. Log the benign
match to scan_notes so the run report shows the guard fired and was cleared, and
address the draft to the developer's NAMED principal, never to the sales desk
inbox.

CONFIRMED CASE, 2026-08-22: "08 - Brokers" carries a row `The Motor Enclave /
Sales Team / info@themotorenclave.com`. That is Brad Oleshansky's own sales desk
at his own domain, and Brad is the Founder on the developer card. Blocking him
as a broker would have been wrong. Note the shape of the test: it is the firm
name AND the domain together. Either one alone is not enough, because a
third-party brokerage that happens to share a name, or a developer-domain
address sitting on a genuinely different firm's broker row, are both real and
both must still block. The 2026-08-21 Florida Garage Condos case is exactly the
second shape: a developer-domain address appearing on a live broker row for a
DIFFERENT firm, which must keep blocking.
- A recipient who matches an existing "05 - Developers" row is addressed using
  that row's named contact, never a scraped generic address.

These are READ-ONLY lookups: match and annotate, never modify a live row.

## Step 4 - DO NOT DRIP FLAG (Lane B)

"05 - Developers" has no Do Not Drip column today. **When one exists, Lane B
must respect it**: any developer whose flag is set is excluded from Lane B
selection permanently, with no draft and no queue row, logged once as
`outreach_skipped` reason `do not drip`. Check for the column each run and honor
it the moment it appears; do not wait for a skill edit. Until it exists, Lane B
selection proceeds on the other criteria and this step is a no-op that the run
report states plainly.

## Step 5 - OUTREACH HOLD CHECK (both lanes, before composing)

Two independent holds. Either one skips the candidate. Both run on EVERY
candidate in BOTH lanes, before a draft is composed.

### 5a. Conversations hold

Query "05 - Developers - Conversations & Learnings", matching the candidate by
`"Developer Index"` OR normalized developer name:

```sql
select id, "Developer", "Note Type", "Note", "Hold Until"
from "05 - Developers - Conversations & Learnings"
where "Outreach Hold" is true
  and ("Hold Until" is null or "Hold Until" >= current_date)
  and ( "Developer Index" = $DEV_ROW
        or regexp_replace(lower(btrim("Developer")), '[\u2013\u2014]', '-', 'g')
           = regexp_replace(lower(btrim($DEV_NAME)), '[\u2013\u2014]', '-', 'g') );
```

A NULL "Hold Until" is an INDEFINITE hold, not an expired one. On any hit: do
not draft, write the ledger row as `held - see conversations note id <n>`,
rotate to the next candidate, and list the hold in the morning digest so Will
sees it that day.

### 5b. Competitive hold

Do not draft a developer who competes with a listing SCK is actively selling.
Hold when EITHER is true of ANY project belonging to the candidate:

1. it lies **within 60 miles** of a project with an active SCK-engaged pre-sale
   listing (great-circle distance on the latitude and longitude in
   "01 - Projects"), OR
2. it sits in the **same Region** as one.

Write the ledger row as
`held - competitive with active engagement <project>`, naming the conflicting
project, and surface it in the digest for Will's call.

**DEFINITION, and it decides how much of the rotation survives.** "Active
SCK-engaged pre-sale listing" means a row in "06 - Pre-Sales" with an ACTIVE
FOUNDING PROGRAM, evidenced by a non-null "Founding Cap". As of 2026-08-22 that
is exactly TWO projects, Bonita Motor Vault and Luxe Dream Garage Waterside,
both in Southwest Florida. The other ten rows in that table are listed but carry
no founding program and do NOT trigger this hold.

This definition is deliberate and was measured. Reading "any row in
06 - Pre-Sales" instead puts a listing in SIX of the seven Florida regions, and
of 100 unique live developers with an email it leaves exactly ONE evaluable
candidate, which then failed the correspondence gate. That reading shuts Lane B
down completely rather than steering it. If Will wants the wider reading, widen
it here deliberately and expect the lane to go quiet in Florida.

**AN UNEVALUABLE TEST IS A HOLD, NOT A PASS.** A candidate with no project row
in "01 - Projects", or whose project rows carry null coordinates, cannot be
tested. Do not draft on the assumption of no conflict. Skip with
`held - competitive test unevaluable, no project coordinates` and report it.
44 of 100 live developers are in this state today, usually because the project
is filed under a name variant of the developer, which is a data problem to fix
in enrichment rather than a licence to draft blind.

Match the candidate to their projects on NORMALIZED developer name. Collection
Suites was briefly scored clean on 2026-08-22 only because its developer card
reads "Collection Suites / JMF Consulting" while its two South Florida project
rows read "Collection Suites"; the exact-string join missed both.

**OVERRIDE.** Will clears a hold by setting "Outreach Hold" false or a past
"Hold Until" on the conversations row, or by adding a new note row. Never clear
a hold from inside this skill.

---

## DEVELOPER SERVICE PACKAGE (canonical shared block, BOTH lanes)

**This is the one and only service list, and it is IDENTICAL in Lane A and
Lane B.** Neither lane keeps a shortened, reordered or re-worded variant. When
this block changes, it changes here once and both lanes inherit it.

Heading, bold: `Developer Service Package`

Bullets, verbatim and in this order, each ending with a period:

- `Site Selection Valuation Report, available for any address in Florida today. Helpful for quickly underwriting proforma unit values.`
- `Site Selection Demographic Reports.`
- `Development Financing and Underwriting Model.`
- `Website, Brand and Operations Consulting.`
- `Capital Markets Advisory. Debt, equity and Founding Member funding capitalization structures.`
- `Full-Service Unit Sales, Marketing and Distribution.`
- `Storage Condo King Web Platform. Developer project portals, pre-sale marketing and distribution network, market data and research, comp data, pre-sale and re-sale unit valuation engine, listing platform, contact directory, and deal email and CRM system.`

Rendered as `<div><b>Developer Service Package</b></div>` followed by a `<ul>`
of seven `<li>` items. No `style=`, no `<span>`, no `<font>`, per the allowlist.

Set 2026-08-22 by Will, replacing the shortened five-bullet capabilities list
Lane B had been using. A developer who gets both lanes over time must see the
same menu twice, not two different accounts of what Storage Condo King does.
The `references/outreach-template.md` copy of this list is superseded by this
block; if the two ever disagree, THIS ONE WINS.

---

## LANE A - New developments

Selection, composition and rotation are unchanged from the queue this skill
inherited. Follow `references/outreach-template.md` exactly: the selection
priority (newest staged developers with a usable email first, then the standing
backlog), the subject, the body, the personalization slots, the linked quarterly
report, and the connector-failure fallback.

Lane A additions from the split, applied on top of that template:

1. The Step 1 correspondence gate runs before the Step 2 sent-check of the
   template, not after. A candidate held by the gate never reaches composition.
2. The Step 2 deleted-draft branch replaces silent requeueing.
3. The Step 5 holds, conversations and competitive, run before composition.
4. The service list is the CANONICAL DEVELOPER SERVICE PACKAGE block above, not
   the copy inside the template file, which is superseded.
5. Lane value on every read and write is `car-condo`.

## LANE B - Existing developers, expanded capabilities

### Selection

Rotate through **live "05 - Developers"** contacts not yet touched by this lane.

```sql
select d."#", d."Developer", d."Contact", d."Email", d."Website", d."Comments"
from "05 - Developers" d
where coalesce(btrim(d."Email"), '') <> ''
  and not exists (
    select 1 from "Developer Outreach - Drafts" o
    where o."Lane" = 'developer-capabilities'
      and lower(btrim(o."Developer")) = lower(btrim(d."Developer"))
  )
order by d."#"
limit 20;
```

Pull a short candidate list, not one row, because the Step 1 gate and Step 3
cross-reference will disqualify some of them. Walk the list in order and take
the first candidate that survives every gate. Deduplicate on normalized
developer name before selecting: the live table still carries same-name rows
with differing payloads, and one firm must never be drafted twice under variant
records.

"Email" cells often pack several addresses and annotations. Extract the FIRST
valid bare address, preferring a named-person address over a generic info@ or
legal@ inbox. "Recipient Email" stores that bare address only, with no
parentheses, notes or secondary addresses.

### Market data, woven as LIQUIDITY EVIDENCE for the distribution ask

**The data has a job, and the job is not to inform.** It exists to make the
distribution offer credible: this product trades, and we hold the list of the
people trading it, so let us put your units in front of them. A figure that does
not serve that argument does not belong in the email.

**NEVER a standalone stat paragraph.** Retired 2026-08-22 by Will as awkward and
disconnected: a lone sentence reading "For context on the market, 143 car condo
units traded across 25 Florida projects over the trailing twelve months," parked
between the opener and the service list, doing nothing and leading nowhere. The
data now lives INSIDE the distribution paragraph, or in the sentence immediately
setting it up, and it always resolves into the ask.

Two components, in this order, because the argument only works in this order:

1. **MARKET LIQUIDITY.** Transaction velocity, aggregate: units traded and
   projects transacting over the trailing twelve months. This proves the product
   moves. Prefer the widest cut that is still true and relevant, statewide when
   the recipient's own region is thin.
2. **PLATFORM REACH.** The size of the owner and buyer list that captures that
   activity, plus the recipient's own region slice when it is non-trivial. This
   proves WE can reach the people doing the trading, which is the whole basis of
   the offer.

Pull both live:

```sql
-- 1. liquidity: units traded and projects transacting, trailing 12 months
select n as units_traded, project_count
from get_market_segmentation_v2(null, null, null, null, null, null, 12)
where dimension = 'all';

-- 2. reach: the distribution list, overall and in the recipient's region
select count(distinct lower(btrim("Email 1")))
         filter (where coalesce(btrim("Email 1"),'') <> '') as unique_owners,
       count(distinct "Project") as projects_covered
from "04 - Unit Owner CRM";

select count(distinct lower(btrim("Email 1")))
         filter (where coalesce(btrim("Email 1"),'') <> '') as region_owners,
       count(distinct "Project") as region_projects
from "04 - Unit Owner CRM" where "Region" = $REGION;
```

`get_market_appreciation` and "Region Definition" remain available for a growth
or median cut when one genuinely strengthens the argument.

**HARD RULES:**

- **AGGREGATE FIGURES ONLY. NEVER a named competing project.** Rollups, counts
  and percentages are fine. Anything specific enough to identify another
  developer's project is barred outright, and this has no exceptions. The
  recipient's OWN project may be named.
- **NEVER a competitor's pricing.** A PSF figure drawn from a region or
  submarket with only two or three tracked projects effectively quotes the
  neighbour, so prefer COUNTS, which expose no pricing at all. Check
  `project_count` before using any average or median: below about five projects,
  drop the price figure and use volume.
- **Never state a decline.** `psf_growth_1yr_pct` is volatile and frequently
  negative. Never present a falling figure, and never frame thin volume as
  weakness.
- **Cite the list honestly.** The number comes from "04 - Unit Owner CRM" and
  those people are unit OWNERS. Say owners. Do not inflate the count with
  prospects, and do not describe it as a buyer list larger than it is.
- If the liquidity figures are null, **drop that clause and keep the reach
  clause**, and vice versa. If both are null, make the distribution ask WITHOUT
  numbers rather than inventing any. The ask never drops; the evidence can.
- At most THREE figures total. This is an argument, not a market report.

### Body spec (complete; every element required unless marked optional)

In order:

1. **Personalized opener** referencing their project or their market by name.
   One factual reference, drawn from the developer card, their live project row
   or their website. If the record is thin, keep the opener generic rather than
   fabricating detail.
2. *(No standalone market paragraph here.)* The market data is NOT a separate
   block. It belongs to item 4 below, where it functions as evidence.
3. **The DEVELOPER SERVICE PACKAGE**, exactly as specified in the canonical
   shared block above. All seven bullets, verbatim, in order, each ending with a
   period. Do NOT shorten it, reword it, or substitute a Lane B specific
   capabilities list; the old four to six bullet variant was retired 2026-08-22.
   Introduce it with a short line such as `Here are some of the ways we can help:`.
4. **The DISTRIBUTION ASK, carrying the market data as its evidence.** This is
   the point of the lane and is never dropped, softened into a hint, or left to
   be inferred. Build it in one move: the market is liquid, we hold the list of
   the owners behind that liquidity, so let us put your current or upcoming
   project in front of them. Say it plainly and make the next step a reply.
   The liquidity and reach figures per the section above live HERE and nowhere
   else in the email.
5. **Signature**, Will's standard block.

Body construction rules, all mandatory:

- **CC chance.friedman@calusainvestments.com on every draft.** No exceptions.
- **No unsubscribe footer.** This is 1:1 correspondence from a named person,
  not a bulk send. Opt-outs are honored by hand when someone asks.
- **No font or style markup of any kind.** No `style=` attributes, no `<font>`,
  no `<span>`, no colors, no sizes. The M365 outbound allowlist REJECTS the
  whole message rather than stripping the offending tag, so a single style
  attribute fails the draft call and loses the morning's work. Build blocks with
  `<div>` and separate them with `<div><br></div>`. The allowlist is p, br,
  a[href|name|target], b/strong, i/em, ul/ol/li, h1-h6, table, code, pre, hr,
  div, strike, and nothing else.
- **No em-dashes anywhere**, and no en-dashes; ranges use the word "to".
- Will's voice: warm, direct, no sales pressure, no hype words.

### Draft and log

Create the Outlook draft in Will's Drafts folder, CC Chance, then insert the
ledger row:

```sql
insert into "Developer Outreach - Drafts"
("Developer","Project","Region","Subject","Body","Recipient Email","Status","Queued At","Lane")
values (<developer>, <project or null>, <region>, <subject>, <body>, <email>, 'queued', now(), 'developer-capabilities');
```

Log `outreach_queued` with the developer name and the lane. If the Microsoft 365
connector is unavailable, still INSERT the row with Status `draft` so nothing is
lost, and log the connector failure. Never silently skip.

---

## Run report

Report per lane: candidates walked, candidates held by the correspondence gate
with the matched address or domain and date, broker matches flagged (and any
cleared by the self-listing exception), candidates held by the conversations
hold with the note id, candidates held by the competitive hold with the
conflicting project, candidates skipped as competitively unevaluable, deleted
drafts recorded as declined, the draft queued (developer, project, region,
recipient), the market nugget used and its source figure, any nugget omitted for
null data, and the Do Not Drip column's presence or absence. Count developers,
never rows.

## Hard rules

- Never send email. Create drafts only. Will presses send.
- 2 developers per weekday morning maximum, one per lane. A lane never borrows
  the other lane's slot.
- The outbound correspondence gate runs on EVERY candidate in BOTH lanes before
  composition, across ALL folders including Sent Items, on the address AND its
  domain, over 90 days. Any hit is a skip and a rotate, never a draft.
- The correspondence gate searches ADDRESS FIELDS ONLY (`sender`, `recipient`),
  never the free-text body. A body mention is not correspondence, and a body
  search makes every discovered developer gate itself via the morning digest.
- The Step 5 holds run on EVERY candidate in BOTH lanes before composition: the
  conversations hold and the competitive hold. An unevaluable competitive test
  is a HOLD, never a pass.
- The broker guard has ONE exception, the self-listing developer: same firm name
  AND the developer's own email domain. Either condition alone still blocks.
- A queued draft found in Deleted Items is `declined - draft deleted in Outlook`
  and frees the rotation. A deletion is a decision, not an error.
- EVERY draft in EVERY lane CCs chance.friedman@calusainvestments.com.
- No unsubscribe footer, no font or style markup, no em-dashes or en-dashes.
- Lane B market data is AGGREGATE ONLY and NEVER names a competing project.
- Lane B market data is never a standalone stat paragraph. It sits inside the
  distribution ask as evidence that the product trades and that we hold the list
  of the people trading it. Data that does not serve that argument is cut.
- Lane B never states a decline and never invents a figure. Null figures drop
  their clause; the distribution ask itself never drops.
- Never quote an average or median PSF from a region with fewer than about five
  tracked projects; that quotes the neighbour. Use counts.
- Lane B honors a Do Not Drip flag the moment the column exists.
- Never modify a live table. "05 - Developers" is READ ONLY to this skill;
  the only write is the developer's Comments note recording a confirmed send,
  which is the pre-existing behavior of the Lane A queue.
- Never fabricate a contact. A slot stays empty with a logged reason before it
  ever holds a guess.
- Bullets in any output copy end with a period.

## Learnings file (read first, append on lessons)

At RUN START: read the repo-root file LEARNINGS.md (the last ~30 entries) and
honor every lesson in it. Entries tagged `outlook-outreach-drip` predate the
2026-08-22 split and cover the unit owner side; entries tagged
`sck-project-enrichment` cover the Lane A queue before it moved here. Both still
bind where they touch developer outreach.
At RUN END: append an entry ONLY when something failed, was corrected,
surprised you, or required a workaround (never for routine success), one line:
- {YYYY-MM-DD} | {routine} | {what happened} | {lesson or fix}
In an unattended cloud run, record learnings as change_type learning rows in
"Scan Activity Log" instead, and never commit, branch, or push.

## Version self-check (prevents skill/instruction drift)

This skill version's marker section is "LANE B - Existing developers, expanded
capabilities". If the routine instructions reference features this file does not
contain, or this file lacks its marker, the deployed skill is stale: log
change_type='skill_out_of_date' with run_type='outreach' detail beginning
"SKILL-OUT-OF-DATE", do what the loaded skill supports, and never improvise
missing templates or rules.

## Scheduling (document for the operator, do not self-schedule)

Weekdays 4:45 AM: claude -p "Run the developer drip per the outlook-developer-drip skill: Lane A then Lane B" --permission-mode acceptEdits
