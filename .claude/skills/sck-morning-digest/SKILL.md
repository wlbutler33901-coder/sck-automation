---
name: sck-morning-digest
description: 6am daily email digest of the Storage Condo King overnight scan and enrichment activity. Summarizes new project candidates and critical updates from the Scan Activity Log and emails will.butler@calusainvestments.com. Use whenever asked to run the SCK morning digest, send the scan summary email, summarize last night's scans, or report overnight pipeline activity.
---

# SCK Morning Digest (6am email)

Reads everything the scanner and enrichment agent logged since the last digest, buckets it, emails Will, marks it digested.

## Step 1 - Pull undigested activity
```sql
SELECT * FROM "Scan Activity Log" WHERE digested_at IS NULL AND run_type IN ('scan','enrichment') ORDER BY ts;
```
Scanner heartbeat check (MUST filter run_type - an enrichment summary is NOT a scan):
```sql
SELECT COUNT(*) FROM "Scan Activity Log" WHERE run_type='scan' AND change_type='run_summary' AND ts > now() - interval '26 hours';
```
Join new candidates to their staged rows for full detail:
```sql
SELECT p.* FROM "01 - Project - New" p WHERE p.discovered_at > now() - interval '26 hours';
```

## Step 2 - Bucket
**Bucket 1 - New Projects**: ONLY rows logged change_type='new_candidate' in this digest window. Never present pre-existing staged inventory as new; if the scanner logged no new_candidate rows, this section reads "No new candidates." One line each -
{Project Name} | {Region} / {Submarket} | {Status} | {Units} units | confidence {level} | {one-line note} | {source_url}
Order: financing_relevance High first (mark these as CALL-WORTHY with developer + contact if enriched), then confidence, then region.

**Bucket 2 - Critical Updates**, in this order:
1. live_status_suggestion (live-database changes awaiting Will's approval - most important)
2. dead_project flags
3. status_change on staged rows (Planned -> UC -> Completed)
4. near_match_flag (possible duplicates needing a human eye)
5. Notable field_enriched items ONLY if high-value (developer contact found, units/pricing confirmed); routine fills go in the counts line, not the body.

## Step 3 - Compose and send
To: will.butler@calusainvestments.com
Subject: SCK Morning Scan Digest - {YYYY-MM-DD}
Body (plain, terse, no em-dashes):
1. Counts line: X new candidates, Y critical updates, Z fields enriched. Regions covered: {list}.
2. NEW PROJECTS section (Bucket 1). If none: "No new candidates."
3. CRITICAL UPDATES section (Bucket 2). If none: "No critical updates."
4. Footer: "Review queue: 01 - Project - New, review_status = pending ({count} rows). Blocked sources or scan errors: {from run_summary rows, if any}."
Send mechanism, in priority order:
1. If env var SCK_DIGEST_WEBHOOK is set: POST the digest as JSON {"to","subject","body"} to that URL (Make.com scenario sends the email). Treat HTTP 200 as a successful send.
2. Else if env vars GMAIL_APP_USER and GMAIL_APP_PASSWORD are set: send via Gmail SMTP (smtp.gmail.com:587, STARTTLS) using python smtplib.
3. Else fall back to the Gmail connector create_draft, and leave digested_at NULL (a draft is not a send).
Never silently skip; if all mechanisms fail, write the digest to ~/sck-digests/{date}.md and log the failure.
Always send, even on a zero-activity night (two-line email). If the run_type='scan' heartbeat query above returns zero, lead the email with: "WARNING: 3am scan did not run or did not complete."

## Step 4 - Mark digested
```sql
UPDATE "Scan Activity Log" SET digested_at = now() WHERE digested_at IS NULL AND run_type IN ('scan','enrichment') AND ts < now();
```
Only after a successful send (or successful fallback write).

## Scheduling
Daily 6:00 AM:
claude -p "Run the SCK morning digest routine per the sck-morning-digest skill" --permission-mode acceptEdits
