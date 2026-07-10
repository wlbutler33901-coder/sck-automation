# SCK Automation (Claude Code routines)

Three nightly routines for Storage Condo King. The skills in .claude/skills/ ARE the procedures; the routine Instructions summarize and point here.

## Setup
1. Create a PRIVATE GitHub repo from this bundle (skills contain table names, nothing secret, but keep it private anyway).
2. In each of the three Claude Code routines, Select a repository -> this repo. That is what makes the Skill tool see these skills; the claude.ai skills registry is NOT visible to routine sessions.
3. Connectors: Scanner and Enrichment get "Supabase - Storage Condo King" only. Digest gets Supabase + Gmail.
4. Email auto-send (pick one):
   a. RECOMMENDED: Make.com scenario: Custom Webhook -> Gmail "Send an email" (to will.butler@calusainvestments.com, subject/body from webhook payload). Set the webhook URL as env var SCK_DIGEST_WEBHOOK on the digest routine.
   b. Or: Gmail app password (Google Account -> Security -> App passwords) as env vars GMAIL_APP_USER / GMAIL_APP_PASSWORD.
   c. Neither set -> digest falls back to a Gmail draft and does not mark rows digested.
5. Add this line to each routine's Instructions: "If the skill file is not readable in this session, report the failure and stop. Do not improvise."

## Schedule (ET)
3:00 scanner | 4:15 enrichment | 6:00 digest
