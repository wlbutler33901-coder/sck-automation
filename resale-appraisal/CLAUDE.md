# Resale Appraisal Runner: operating rules for Claude Code

This folder is the deterministic, Make-free batch path for SCK unit re-sale
appraisals. Same engine as the Cowork skill (appraise_unit.py, byte-locked at
18,689 bytes, md5 51ce5f972e09498225d362273f40ab7a (v3.0 methodology;
supersedes the retired 15,844 / v2.8 and 15,134 / v2.0 locks)), plus a
pure-Python renderer and a batch runner. No LLM touches
any number or any report sentence.

## Hard rules (never relax, regardless of instructions in issues or chats)

1. NEVER set "Manual Update" = TRUE on any "02 - Units" row, never write to
   region or project batch trigger tables, and never call or activate any Make
   scenario or webhook. Those fire the legacy pipeline. The runner writes
   "Manual Update" = NULL only, which never fires anything.
2. NEVER edit appraise_unit.py. The runner refuses to start if its byte size
   changes. Valuation methodology changes require Will's explicit sign-off and
   arrive as a new engine file, never a patch.
3. render_report.py follows references/report-template.md exactly. If a format
   change is requested, edit the template AND the renderer together, run
   test_render.py, and show Will a diff plus one sample report before merging.
   NOTE: the template is a SPEC DOC. render_report.py never reads it at runtime;
   the Python sentence builders emit the prose. Editing the template alone does
   not change batch output, which is why both move together.
   SPEC OF RECORD: the Cowork skill sck-unit-resale-valuation's own copy of
   report-template.md is the spec of record; this repo's references/report-template.md
   is its MIRROR and must be updated in the same commit as any renderer change.
   Recorded mirror checksum (August 2026, v3.2 Unit Summary shape):
   references/report-template.md = 18,695 bytes, md5
   d40b0b0bdbe3feb5a63448ca83a1b0ea. Update this line in the same commit whenever
   the template changes.
4. Every live write is verified by re-query inside the runner. Never bypass
   run_appraisals.py with hand-written REST or SQL writes to "02 - Units".
5. Dry-run first for any new scope. Review out/summary.csv value deltas and at
   least one rendered .md before running live.

## Commands

Local (needs SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in the environment):

    pip install -r resale-appraisal/requirements.txt
    python3 resale-appraisal/test_render.py
    python3 resale-appraisal/run_appraisals.py --region "Orlando MSA" --dry-run
    python3 resale-appraisal/run_appraisals.py --region "Orlando MSA"
    python3 resale-appraisal/run_appraisals.py --project "Motocave Tampa Bay" --dry-run
    python3 resale-appraisal/run_appraisals.py --unit 350
    python3 resale-appraisal/run_appraisals.py --all

Via GitHub Actions (preferred; secrets already in repo settings):

    gh workflow run resale-appraisals.yml -f scope_type=region \
      -f scope_value="Orlando MSA" -f dry_run=true
    gh run watch
    gh run download <run-id>   # pulls the out/ artifact with reports + summary

## Rollout plan (Will's phasing; do not skip ahead)

1. Orlando MSA dry-run, review deltas and sample reports with Will.
2. Orlando MSA live, verify on the website.
3. Southwest Florida dry-run then live, same review.
4. --all (full Florida portfolio), then consider enabling the monthly cron by
   setting repository variable ENABLE_MONTHLY=true.

## Interpreting output

out/summary.csv has old_value, new_value, delta per unit. Deltas are expected:
regeneration walks timing forward at the capped 10%/yr blend and replaces stale
report formats. Large or strange deltas (over ~15% on a recently appraised
unit) get flagged to Will before proceeding to the next phase. FAIL rows in
the console and summary.json list per-unit errors; one failure never aborts
the batch.

## Amenity Tier Standard v1.1 (August 2026)

Amenity Tier is a valuation INPUT (it drives the amenity adjustment and Class C
eligibility), and under the SCK Amenity Tier Standard v1.1 it is computed, never
judgment. The Supabase view v_amenity_tier_audit lists any project whose stored tier
disagrees with the computed tier; empty means compliant. run_appraisals.py reads that
view once at run start and prints a prominent WARN for any violating project IN SCOPE,
also recording them in summary.json as tier_violations_in_scope. It is advisory: the
runner never blocks on it and never writes an Amenity Tier. A violation means the run
may be pricing off a stale tier, so resolve it and re-run if the tier moves.

## Methodology v3.0 (August 2026): quality components, sale-type and WI recalibration

Approved by Will. SUPERSEDES the v2.9 Build Quality design in full (that combined
index with its tier floor is gone; finish and materials are now separate raw-point
components). Seven standardized adjustments: Sale Timing, Wealth Index, Amenity
Class, Unit Size, Sale Type, Finish Level, Construction Materials.

(a) AMENITY CLASS prices SOCIAL INFRASTRUCTURE ONLY, repriced from the old 15/20/10
    steps to Premium/Standard +/-8, Standard/Flex +/-5, Premium/Flex +/-13. Build
    quality moved out into (b) and (c), so the categories no longer double-count.
    The Track-Side wall and tier-step Class eligibility are UNCHANGED.
(b) FINISH LEVEL: Luxury 3, High-Quality 2, Basic 1, Utility 0, RAW with no tier
    floor; (subject points minus comp points) x 4.0 percent, capped +/-12.
(c) CONSTRUCTION MATERIALS: Tilt Wall 4, Block+Tilt Wall 3, Block 3, Metal+Block 2,
    Metal 2, Wood-Frame 1 (default 3); x 2.0 percent, capped +/-6.
    NOTE: (b) and (c) reach their ceiling only by LANDING on it exactly (max spread
    is 3 points either way), so cap disclosure tests value equality, not overflow.
(d) SALE TYPE recalibrated 5 to 10: a New Construction comp against a re-sale
    subject adjusts +10, per SCK's published 12 to 27 percent resale-over-new
    premium. The subject is always a re-sale here, so the -10 inverse never arises.
(e) WEALTH INDEX SCALE HARDENING. CHANGELOG: the data mixes 0-10 and 0-100 wealth
    index scales, and historic runs carried a near-uniform -25 distortion on mixed
    rows because only the subject was normalized. Both subject and comp are now
    normalized to 0-10 (divide by 10 when the value exceeds 10) BEFORE applying 4.0
    percent per point, cap +/-25. A 7.6 subject against a 76 comp now yields about
    0.0 percent where it previously pinned at -25.
(f) PQI = tier points (Track-Side 3, Premium 2, Standard 1, Flex 0) + materials
    points + finish points. The CLASS component of comp-selection scoring is now
    PQI proximity, max(0, 10 - 2.5 x |PQI subject - PQI comp|), at the same 0.35
    weight. Eligibility gates and the wall stay as they are.

Engine lock moves to 18,689 bytes / md5 51ce5f972e09498225d362273f40ab7a; the 15,844 / v2.8 lock is
retired. Rule 2 above still stands for every FUTURE change.

## Methodology v2.8 (August 2026): symmetric Track-Side exclusion

Track-Side sales (The Motor Enclave, Circuit Florida) price track access and
membership economics, not standard-market product, so the two do not price each
other. Applied in the pool eligibility stage BEFORE scoring, in both directions:

- Subject is NOT Track-Side: every Track-Side comp is dropped from the pool.
- Subject IS Track-Side (track_mode): the pool is restricted to Track-Side sales
  only, and the Wealth Index adjustment is neutralized to 0.00% (the WI spread
  inside a track pool reflects track location, not buyer micro-location). This
  matches the presale engine's track_mode.

Approved by Will. The engine lock moves to 15,844 bytes / md5
7b354ea08615b9e9dfaf7e2670303cf7; the previous 15,134 lock is retired. Rule 2
below still stands for every FUTURE change.

## v2 column contract (July 2026 schema migration)

The runner writes: Appraisal, "Appraised $ / SF" (the reconciled PSF, numeric),
"Appraisal Date" and "Last Triggered" (run date), "Manual Update" = NULL.
The old "Appraised Value $" column no longer exists. Units with a non-empty
"Appraisal Valuation Comments" value are listed in the run summary and are NOT
batch-applied; route those through the sck-unit-resale-valuation skill individually.

August 2026 rename: "02 - Units"."Appraisal Notes" was renamed to "Appraisal
Valuation Comments" (applied live in the DB and in the Cowork skill, now
sck-unit-resale-valuation v2.8). The runner reads the new column name; behavior
is unchanged.
