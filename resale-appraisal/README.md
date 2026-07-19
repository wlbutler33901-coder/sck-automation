# SCK Resale Appraisal Runner

Deterministic batch re-appraisal for every unit in "02 - Units": engine ->
renderer -> validated write-back -> re-query verification. Replaces the Make
DeepSeek pipeline with zero-variance output and near-zero cost per run.

## One-time setup (two GitHub secrets)

Repo Settings -> Secrets and variables -> Actions -> New repository secret:

- SUPABASE_URL = https://llwyvgkqhendgzsgngqh.supabase.co
- SUPABASE_SERVICE_ROLE_KEY = the service_role key from the Supabase dashboard
  (Project Settings -> API -> service_role). Keep it out of the repo itself.

Optional: DIGEST_WEBHOOK_URL to POST each run summary to the Make digest hook.
Monthly schedule: off by default; enable later with repository variable
ENABLE_MONTHLY = true (Settings -> Secrets and variables -> Actions -> Variables).

## Running from a phone

GitHub app or mobile web: Actions -> Resale Appraisals -> Run workflow ->
pick scope and dry run -> Run. Reports and summary.csv download as the run
artifact. Or ask Claude Code: "run the Orlando dry run and show me the deltas".

## What a run does

Per project: one RPC pull (get_comprehensive_market_data), live blended
appreciation rate from Market Coverage (capped at 10), subject Wealth Index
from Demographic Data - Project. Per unit: engine, render, structural
validation (exact table headers, disclosure, no dashes, subject excluded from
Table 5), then PATCH of "Appraisal" + "Appraised Value $" with "Manual Update"
cleared to NULL, verified by an independent re-query. Never touches Make.
