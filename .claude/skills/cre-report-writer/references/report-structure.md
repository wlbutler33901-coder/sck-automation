# Report Structure - Priority Order, Numbering, First Appearance

This file governs the shape of the daily brief. The SKILL.md governs what goes in it. Where the
two disagree on ordering, numbering, or windowing, this file wins.

## Report window - high water mark (mandatory)

The PRIMARY window is everything created since the LAST report row, never a fixed lookback:

```sql
SELECT coalesce(max(created_at), now() - interval '26 hours') AS window_start
FROM "Development Scanner - Report Summary";
```

Both source tables are then pulled with `created_at > window_start`. The 7 day CONTEXT window
is unchanged.

Why this is a hard rule: the report runs about 09:40 UTC and the scanners write their rows
between 07:37 and 08:47 UTC, so a fixed 26 hour window reached back past the PREVIOUS morning's
scan output and captured almost every row twice. Measured across the Aug 1 to Aug 3 2026
reports, 22 of 34 New Projects entries were repeats of the prior day (12 of 21, then 9 of 11,
then 1 of 2), including Estero Oaks Portal id 98 presented as a first appearance two days
running. The high water mark closes that by construction and is immune to clock drift, DST
shifts, and late report starts.

Corollary: a second report run in the same morning after a successful insert correctly sees an
empty window. That is not a bug; do not widen the window to compensate.

## Section order (highest priority first)

Compose exactly these, in this order. An empty section says so explicitly in one line.

| # | Section | Include when | Supabase column |
|---|---|---|---|
| 1 | EXECUTIVE SUMMARY | Always | "Executive Summary" |
| 1c | WEEKLY ROLLUP | MONDAYS ONLY. Omit entirely on other days. | "Weekly Rollup" (null on non-Mondays) |
| 2 | NEW PROJECTS | Always. First appearance only, see below. | "New Projects" |
| 3 | PROJECT UPDATES | Always. Everything previously reported with new activity. | "Project Updates" |
| 4 | STAGE PROGRESSIONS | Always | "Stage Progressions" |
| 5 | NEW DEVELOPERS IDENTIFIED | Always | "New Developers Identified" |
| 6 | FINANCING LENS | Always, compact | "Top Opportunities" |
| 7 | ROTATION AND COVERAGE AUDIT | Always | "Rotation Audit" |
| 8 | DATA QUALITY NOTES | Always | "Data Quality Notes" |
| 9 | WARNINGS | ONLY if a cluster did not run, a track is pending, or a portal is blocked. Omit the section header entirely on a clean night. | folded into "Data Quality Notes" |

WARNINGS MOVED TO THE BOTTOM on 2026-08-22, matching the sck-morning-digest change made the same
day. It used to be section 0, a banner at the top. It is now section 9, the LAST section, after
Data Quality Notes, on every day the report runs INCLUDING the Monday rollup edition. Nothing
about its content changes: it is still mandatory whenever a cluster did not run, a track is
pending, or a portal is blocked, still omitted entirely on a clean night, and still folded into
the "Data Quality Notes" column in Supabase. Only its position moved. Any section elsewhere that
says a line is promoted into WARNINGS still promotes it; that section now sits at the end.

Rationale for the order: sections 2 to 5 are the ones that can change what Will does today, in
descending order of how likely that is. Section 6 stays secondary until the financing phase
turns on. Sections 7, 8 and 9 are operational health and belong at the bottom. The report leads
with what was FOUND, not with what broke: a clean night should read as a clean night, and a bad
night still ends with the full warning list rather than opening with it.

## Section 2 sort order - entitlements first

Within each financing-relevance band, items tagged [ENTITLEMENT] sort ABOVE permit items regardless
of missing cost. Cost ordering applies below that, descending, unknown-cost last.

An item is [ENTITLEMENT] when it comes from a development-application feed (the St. Petersburg
ArcGIS MultiFamily_Layer, the City of Sarasota microapp da search) OR its record type is a
rezoning, a site plan, or a development application. The reason is financeability: at that stage
capital is not yet placed, so those are the most financeable leads in the report. A permit means
the capital decision is already made.

TRANSITION, next 7 days only: rows created before the "Est. Cost" column existed may carry a cost
figure in prose only. Parse the prose for sorting during that window. After it, the "Est. Cost"
column is authoritative and prose is not consulted for ordering.

## Numbering, not bullets

Every item inside every section carries a numeric index restarting at 1 within its section.

- Markdown: `1.` `2.` `3.` ordered lists. Never `- ` bullets for report items.
- Email HTML: `<ol>` and `<li>`. Never `<ul>`.
- A multi field project entry is ONE numbered item, pipe separated on one line.
- Section 9 WARNINGS is also numbered.

The one exception is a sub detail hanging off a numbered item, which may use an indented
`- ` line. Every such line ends with a period.

## First appearance only (section 2 versus section 3)

A project enters NEW PROJECTS on exactly one day of its life: the day its identity key is first
seen in either scanner table. Every later touch, no matter how it arrives, goes to PROJECT
UPDATES. Recycled press coverage of a project already in the database is the single most common
cause of a padded NEW PROJECTS count and must never inflate it.

### Identity key, resolved in this order

1. Normalized parcel or folio number, lowercase, dashes and spaces stripped.
2. Permit or case number extracted from "Municipality Posting Look-Up Value".
3. Normalized project name plus city, using
   `regexp_replace(lower(trim(x)), '[\u2013\u2014]', '-', 'g')`.

### The check

For every candidate in the PRIMARY window, run this before placing it. If `first_seen` is at or
before `window_start`, the item is an UPDATE, not a NEW PROJECT.

```sql
WITH norm AS (
  SELECT
    coalesce(
      nullif(regexp_replace(lower(coalesce("Parcel / Folio Number", '')), '[^a-z0-9]', '', 'g'), ''),
      regexp_replace(lower(trim(coalesce("Project Name", ''))), '[\u2013\u2014]', '-', 'g')
        || '|' || lower(trim(coalesce("City", '')))
    ) AS ident,
    created_at
  FROM "Development Scanner - Municipality Portals"
  UNION ALL
  SELECT
    regexp_replace(lower(trim(coalesce("Project Name", ''))), '[\u2013\u2014]', '-', 'g')
      || '|' || lower(trim(coalesce("City", ''))) AS ident,
    created_at
  FROM "Development Scanner - News Scanner"
)
SELECT ident, min(created_at) AS first_seen, count(*) AS touches
FROM norm
WHERE ident <> '|' AND ident <> ''
GROUP BY ident;
```

Place each candidate by comparing its `first_seen` against `window_start`.

### Backfills

A genuinely first seen item whose underlying event is old (permit "Posting Date" or article
event more than 60 days before the report date) is still NEW, but carries a [BACKFILL] tag and
sorts last in section 2 regardless of cost. The King of Vape pattern: a 2024 era record entering
the table for the first time is a discovery, not news.

### First appearance applies to NEW DEVELOPERS too (section 5)

A developer name is listed in section 5 only when its `min(created_at)` across BOTH tables
(normalized, ILIKE match on the developer and sponsor columns) is inside the PRIMARY window.
This replaces the old 7 day definition, which by spec re listed the same names every day for a
week; Catalyst Development and McDowell Housing each appeared as "first seen" in three
consecutive reports. Once listed, a developer never appears in section 5 again.

### PROJECT UPDATES item format

`N. **Name** (Portal id X / News id Y) | what is new since it was last reported | city, county |
stage now, stage before if it moved | source link.`

The phrase "what is new" is the whole point of the section. If nothing is materially new, the
item does not belong in the report at all; it is a re-scrape and gets dropped silently. Never
pad this section to make the day look busy.

## Section 6 - FINANCING LENS is MOVEMENT ONLY

The numbered items are ONLY new entrants and changes since the last report: a lead that was not in
the lens before, or one whose stage, cost, or status moved. Determine movement by comparing against
the prior rows of the "Top Opportunities" column in "Development Scanner - Report Summary"; that
column is the memory of what was already reported.

The standing pipeline does NOT get numbered items. It compresses to ONE unnumbered line, capped at
five entries:
`Standing pipeline: 1. {name} ({$}, {stage}) 2. {name} ({$}, {stage}) ...`

A quiet week is allowed to produce zero numbered items and just the standing line. Re-listing an
unchanged lead as if it were news is the failure this rule exists to stop.

## Section 1c - WEEKLY ROLLUP (Mondays only)

Compose this section ONLY on Mondays and write the same content to the "Weekly Rollup" column. On
every other day the section is omitted entirely and the column is null.

Contents, in this order:
1. SEVEN DAY TOTALS: new projects, updates, and the sum of known "Est. Cost" over the last 7 days.
   Say plainly how many rows carried a known cost, since the sum is only over those.
2. CLUSTER COVERAGE MATRIX: all 14 scheduled cluster-nights of the week (7 Track A + 7 Track B),
   each marked ran, zero, blocked, or missed, built from the run-logging queries in the permit
   scanner's references/run-logging.md. "zero" means the cluster ran and found nothing; "missed"
   means it left no trace. Those are different findings and must never be merged.
3. TOP 5 FINANCEABLE ITEMS of the week, entitlements favored per the section 2 sort.
4. THE CALUSA OUTREACH LANE per references/calusa-outreach-template.md: list EVERY candidate
   considered with its outcome (drafted, drafted-needs-address, skipped and why), not just the
   three drafted, so no Monday selection is ever invisible. A drafted-needs-address item names its
   contact path. Follow the list with exactly this reminder line:
   Attach the condensed Calusa Financing Capabilities PDF in Outlook before sending each.

## Section 7 - Rotation and coverage audit

Built from the queries in the permit scanner's references/run-logging.md. Report, numbered:

1. Cluster ids that ran last night, per track, with portals completed and blocked.
2. Cluster ids scheduled in the last 7 days that left NO trace in the log at all. Name them
   and give the date they should have run. This is the miss list. A scheduled night with no
   trace that predates the cluster's first ever run_started row is labeled no logged history
   yet, pre deployment or newly activated, and is not treated as a confirmed miss; only nights
   after a cluster's first run_started row count as real misses.
3. Portals that returned zero qualifying permits, distinguished plainly from portals that were
   never reached. These are different findings and must never be merged into one line.
4. Tracks currently PENDING and therefore uncovered.

If the permit scanner wrote no `run_started` row for last night, section 9 WARNINGS leads with
that fact and the Executive Summary repeats it in its first sentence.

## Section 8 additions

Section 8 also lists, numbered, any change_type learning rows logged since the last report, one
line each, so learnings surface to Will daily even before they are folded into LEARNINGS.md.

## Counts written to Supabase

- "New Projects Count" is the count of items in section 2 only, after the first appearance
  filter. It is not the number of rows created last night.
- "Updates Count" is the count of items in section 3.
- "Projects Reviewed" and "Articles Reviewed" stay as they are, raw rows in the window.
