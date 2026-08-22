# Outlook Drips - Setup

## What this is

Two Claude Code skills in the sck-automation repo, each drafting Outlook mail
for Will to review and send. Neither ever sends. They were one skill,
`outlook-outreach-drip`, until 2026-08-22; that skill was split by audience
because the two jobs have nothing in common but the mailbox.

| Skill | Audience | Cadence |
|---|---|---|
| `.claude/skills/outlook-unit-owner-drip/SKILL.md` | Unit owners | Daily 5:15 AM |
| `.claude/skills/outlook-developer-drip/SKILL.md` | Developers | Weekdays 4:45 AM |

The two never share a queue, a ledger or a rotation, and neither may draft into
the other's audience.

---

## Skill 1 - outlook-unit-owner-drip

Renamed from `outlook-outreach-drip`. Behavior unchanged.

Each morning it processes Outlook kickbacks from prior drip sends, promotes
proven addresses back into the CRM, then drafts the next batch of personalized
1:1 outreach emails to quarantined addresses from "04d - Email Verification".
When that queue is empty it runs the BMV owner campaign against
"04 - Unit Owner CRM" instead. Drafts land in Will's own Outlook Drafts folder
(will.butler@calusainvestments.com), each CCing
chance.friedman@calusainvestments.com, ready to review and send.

### Routine

- Name: Storage Condo King - Outlook Unit Owner Drip.
- Repo: wlbutler33901-coder/sck-automation.
- Model: Opus, not Sonnet. The personalization step is judgment work.
- Trigger: Schedule, every day at 5:15 AM (after the other SCK routines finish,
  before Will starts).
- Connectors: Supabase - Storage Condo King, Microsoft 365 (signed in as
  will.butler@calusainvestments.com). Remove the rest.
- Instructions:

Run the outlook-unit-owner-drip skill at .claude/skills/outlook-unit-owner-drip/SKILL.md as a full cycle.

First run KICKBACK mode. Search the mailbox for NDR and delivery failure messages, suppress bounced addresses in "04a - Email Suppression", clear them from the CRM, and promote drafts older than 4 days with no kickback: reinstate their parked contact if needed, restore the address to the CRM, stamp "Email Verified At", delete the 04d row.

Then run DRAFT mode. Pull the next batch of quarantined addresses from "04d - Email Verification" (skip if today's batch already exists), screen them against "04a - Email Suppression", personalize per the skill, save each as an Outlook draft CCing chance.friedman@calusainvestments.com, and stamp "Drafted At".

Then, ONLY if DRAFT mode had nothing to draft, run CAMPAIGN mode per the skill.

Never send email. Drafts only. Follow every hard rule in the skill. Finish with the skill's run report as your final message.

---

## Skill 2 - outlook-developer-drip

New on 2026-08-22. Two developers per weekday morning, one per lane.

- **Lane A, new developments** (Lane value `car-condo`): the intro draft that
  used to live in `sck-project-enrichment` Step 5b. Its template moved to
  `.claude/skills/outlook-developer-drip/references/outreach-template.md`.
- **Lane B, existing developers** (Lane value `developer-capabilities`): a
  rotation through live "05 - Developers" contacts not yet touched by the lane,
  themed on the expanded capabilities of Storage Condo King, including an
  explicit offer to blast their projects to the SCK unit owner and buyer
  database.

Both lanes run an **outbound correspondence gate** before queuing anything:
Outlook is searched across ALL folders, Sent Items included, for any
correspondence with the recipient address OR its domain in the last 90 days. Any
hit is a skip and a rotate to the next candidate, so a developer who wrote in
through the site and got a manual reply never receives an automation intro the
next morning.

A queued draft found in Deleted Items is recorded as
`declined - draft deleted in Outlook` and frees the rotation. A deletion is a
decision, not an error state.

### Routine

- Name: Storage Condo King - Developer Drip.
- Repo: wlbutler33901-coder/sck-automation.
- Model: Opus.
- Trigger: Schedule, weekdays at 4:45 AM.
- Connectors: Supabase - Storage Condo King, Microsoft 365 (signed in as
  will.butler@calusainvestments.com). Remove the rest.
- Instructions:

Run the outlook-developer-drip skill at .claude/skills/outlook-developer-drip/SKILL.md. Run Lane A, then Lane B, at most one draft each. Run the outbound correspondence gate on every candidate in both lanes before composing, across all folders including Sent Items, on the address and its domain, over 90 days; any hit is a skip and a rotate. Apply the deleted-draft branch. CC chance.friedman@calusainvestments.com on every draft. Never send email. Finish with the skill's run report as your final message.

---

## Daily loop for Will

1. Morning: open Outlook Drafts, skim, press send. Mail goes out from your own
   address with Chance CCd, so replies and NDRs both come back to you.
2. Deleting a developer draft is how you say no to it. The next run records the
   deletion and frees that lane; it will not re-draft that developer.
3. That is all. The next runs handle kickbacks, promotions, rotation and the
   next batch automatically.

## Notes

- The routines warn that connector tools run without permission prompts. That is
  required here: the skills write to Supabase and create Outlook drafts
  unattended. They never send mail; sending stays manual.
- If the unit owner routine reports zero remaining and the campaign is complete,
  the queue is clear and that routine can be paused.
- Bounce exports from Constant Contact still go through the sck-bounce-ingest
  Cowork skill as before. These routines only handle the 1:1 Outlook channel.
- LEARNINGS.md entries tagged `outlook-outreach-drip` predate the split. They
  are the unit owner skill's history and still bind; the developer skill also
  reads them where they touch developer outreach.
