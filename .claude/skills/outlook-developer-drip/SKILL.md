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
3. Lane value on every read and write is `car-condo`.

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

### Market data nugget (live, aggregate only)

Every Lane B draft carries exactly ONE market data figure relevant to the
recipient's region: a PSF trend, a sales velocity stat, or an inventory figure.
Pull it live:

```sql
select region, submarket, psf_growth_5yr_ann_pct, psf_growth_1yr_pct,
       unit_sales_ttm, median_psf_ttm
from "Region Definition"
where region = $REGION;
```

`get_market_segmentation_v2` and `get_market_appreciation` are also available for
a region or submarket cut when the "Region Definition" row is thin.

**HARD RULES on the nugget:**

- **AGGREGATE FIGURES ONLY. NEVER a named competing project.** Region and
  submarket rollups, medians, counts and percentages are fine. A sentence that
  names another developer's project, or that is specific enough to identify one,
  is barred outright. This is the competitor anonymity rule and it has no
  exceptions in this lane. The recipient's OWN project may be named.
- **Never state a decline.** `psf_growth_1yr_pct` is volatile and frequently
  negative; do not use it as the nugget when it is negative, and never present a
  falling figure as news. Prefer `psf_growth_5yr_ann_pct`, `unit_sales_ttm` or
  `median_psf_ttm`.
- If every figure for the recipient's region is null, **omit the nugget
  sentence entirely** and note the omission in the run report. An email with no
  nugget ships; an invented nugget never does.
- One figure, one sentence. Do not stack three stats into a paragraph.

### Body spec (complete; every element required unless marked optional)

In order:

1. **Personalized opener** referencing their project or their market by name.
   One factual reference, drawn from the developer card, their live project row
   or their website. If the record is thin, keep the opener generic rather than
   fabricating detail.
2. **The market data nugget**, one sentence, per the rules above. Optional only
   in the all-null case.
3. **A short bullet list of SCK benefits.** Each bullet ends with a period.
   Keep it to four to six bullets; this is a capabilities note, not the full
   Lane A service menu.
4. **An explicit offer to blast their current or upcoming projects to the SCK
   database of unit owners and buyers.** This is the point of the lane and is
   never dropped, softened into a hint, or left to be inferred. Say it plainly
   and make the next step a reply.
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
with the matched address or domain and date, broker matches flagged, deleted
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
- A queued draft found in Deleted Items is `declined - draft deleted in Outlook`
  and frees the rotation. A deletion is a decision, not an error.
- EVERY draft in EVERY lane CCs chance.friedman@calusainvestments.com.
- No unsubscribe footer, no font or style markup, no em-dashes or en-dashes.
- Lane B nuggets are AGGREGATE ONLY and NEVER name a competing project.
- Lane B never states a decline and never invents a figure; a null region omits
  the sentence.
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
