# Outlook Outreach Drip - Setup

## What this is

A Claude Code skill for the sck-automation repo. Each morning it processes
Outlook kickbacks from prior drip sends, promotes proven addresses back into
the CRM, then drafts the next 45 personalized 1:1 outreach emails to
quarantined addresses from "04d - Email Verification". Drafts land in Will's own Outlook
Drafts folder (will.butler@calusainvestments.com), each CCing
chance.friedman@calusainvestments.com, ready to review and send.
The 311 address queue clears in about 7 days of sends.

## Install (one time)

1. Unzip at the ROOT of the sck-automation repo. It adds one file:
   .claude/skills/outlook-outreach-drip/SKILL.md
2. Commit and push to main.

## Create the routine (one time)

In Claude Code cloud, Routines, New routine:

- Name: Storage Condo King - Outlook Outreach Drip.
- Repo: wlbutler33901-coder/sck-automation.
- Model: Opus.
- Trigger: Schedule, every day at 5:15 AM (after the other SCK routines
  finish, before Will starts).
- Connectors: Supabase - Storage Condo King, Microsoft 365 (signed in as
  will.butler@calusainvestments.com). Remove the rest.
- Model: Opus, not Sonnet. The personalization step is judgment work.
- Instructions: paste the block below.

## Routine instructions (paste as written)

Run the outlook-outreach-drip skill at .claude/skills/outlook-outreach-drip/SKILL.md as a full cycle.

First run KICKBACK mode. Search the market@storagecondoking.com mailbox for NDR and delivery failure messages, suppress bounced addresses in "04a - Email Suppression", clear them from the CRM, and promote drafts older than 4 days with no kickback: reinstate their parked contact if needed, restore the address to the CRM, stamp "Email Verified At", delete the 04d row.

Then run DRAFT mode. Pull the next 45 quarantined addresses from "04d - Email Verification" (skip if today's batch already exists), screen them against "04a - Email Suppression", personalize the plain text outreach per the skill, save each as an Outlook draft, CCing chance.friedman@calusainvestments.com, and stamp "Drafted At".

Never send email. Drafts only. Follow every hard rule in the skill. Finish with the skill's run report as your final message.

## Daily loop for Will

1. Morning: open Outlook Drafts, skim, press send on the batch. They go out
   from your own address with Chance CCd, so replies and NDRs both come back
   to you.
2. That is all. The next routine run handles kickbacks, promotions, and the
   next batch automatically.

## Notes

- The routine warns that connector tools run without permission prompts.
  That is required here: the skill writes to Supabase and creates Outlook
  drafts unattended. It never sends mail; sending stays manual.
- If a run reports zero remaining, the queue is clear and the routine can be
  paused or deleted.
- Bounce exports from Constant Contact still go through the sck-bounce-ingest
  Cowork skill as before. This routine only handles the 1:1 Outlook channel.
