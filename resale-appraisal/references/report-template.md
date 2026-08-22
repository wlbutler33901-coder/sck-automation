<!-- no-dash rule -->

NO DASH PUNCTUATION (entire report): never use em-dashes, en-dashes, or spaced hyphens as punctuation in prose or bullets. Use a colon after bullet headers, commas or periods elsewhere, and write ranges with "to". Hyphenated compounds and negative signs are fine. EXCEPTION: structural "### Tab N - X" and "**Table N - X**" labels keep their hyphen separators, the application parses them.
# Unit Re-Sale Report Template (Reference Model)

Render the final report to match this structure exactly. Fill every value from `computed.json`; write the narrative from `narrative_stats`. Percentages show sign and two decimals; `$/SF` two decimals; values with commas. **Do not alter any number the engine produced.**

SECTION BOUNDARY RULES:
- The report consists of sections 1-3 and ENDS after the Methodology paragraph. Never emit a numbered "## 4" heading, a "Comparable Sales Analysis" section, a five-year projection, or any placeholder text after Methodology. The application computes projections.
- There is NO Listing Summary for unit re-sales (units are owner reports, not listings; `"02 - Units"` has no Listing Detail column).
- NEVER include a confidence statement — no sentence of the form "Confidence is Medium-High: ..." anywhere.

AUDIENCE AND VOICE: unit owners first (they are checking their property's value — lead with the number), buyers and developers second. Professional but accessible; institutional rigor underneath. Compact — no padding. No em-dashes.

MARKDOWN FORMAT: document title "# Luxury Garage Condo Unit Market Value Report"; sections "## 1. Property Summary", "## 2. Value Estimate", "## 3. Market Value Summary"; tabs "### Tab 1 - Value Summary", "### Tab 2 - Comparable Sales", "### Tab 3 - Comp Adjustments"; bold lead-in labels on their own line for subsections; proper pipe tables; bold every key figure.

---

## 1. Property Summary
- **Project Name:** {subject.project}
- **Address:** {subject.address}
- **Unit Number:** {subject.unit_number}  (the ACTUAL unit number - never "Average" or "Pre-Construction")
- **Parcel ID:** {subject.parcel_id}
- **City:** {subject.city}
- **Region:** {subject.region}
- **Submarket:** {subject.submarket}
- **Year Built:** {subject.year_built}  (actual year - never "Projected Delivery")
- **Number of Units:** {subject.num_units}
- **Unit Size (SF):** {subject.unit_size_sf} SF
- **Amenity Tier:** {subject.amenity_tier}
- **Wealth Index (All):** {subject.wealth_index}

## 2. Value Estimate
- **Estimated Market Value:** ${estimated_market_value}
- **Value Per SF:** ${value_psf}/SF
- **Finish-Level Range:** ${finish_level_band.low_value} to ${finish_level_band.high_value} (${low_psf} to ${high_psf}/SF)
- **Effective Date:** {appraisal_date}

## 3. Market Value Summary

TAB 1 - VALUE SUMMARY

**Valuation Overview** - THREE paragraphs separated by blank lines, NEVER one block. 130 to 170 words total. LENGTH DISCIPLINE (v3.0, matches the Cowork skill sck-unit-resale-valuation): every sentence carries a figure or a disclosure, and NO figure is restated across paragraphs.
- Paragraph 1 - EXACTLY 2 sentences, 55 to 70 words. Sentence one: market value, $/SF, unit, project, tier, size. Sentence two: the comp evidence as ONE compound clause LEADING WITH THE SAME-PROJECT COUNT ("{class_a} of {n_comps} comparables are sales inside {project} itself", noting the subject's own prior sale if among them), then the score band and the largest adjustment driver. Every figure bold. NO framing lead-ins ("That conclusion rests on a deep evidence base" and similar are padding).
- Paragraph 2 (ONE sentence, stands alone): the {n} comparables average an unadjusted ${x}/SF, a {+x.xx%} total adjustment reconciles them, and adjusted values span ${min} to ${max}/SF, the finish-level band a shell versus a built-out unit could realize. Do NOT restate the value, $/SF, or unit size carried by paragraph 1.
- Paragraph 3 (ONE sentence, stands alone): the standing buildout caveat - finish level is not observable in recorded sales, so the value reflects a market-average buildout (customized units may exceed it; shells may trail it) - plus a brief outlier/thin-data clause only if applicable. No confidence label.

Table 1 - Value Summary (three rows only):
| Line | $/SF |
| Comp Average | $X.XX |
| Total Adjustment | +X.XX% |
| Market Value (N,NNN SF) | $X.XX/SF ($XXX,000) |

TAB 2 - COMPARABLE SALES

**Comp Selection** - ONE sentence covering set size, same-project share (class counts, and whether the subject's own prior sale is included), score band, and the New Construction vs Re-Sale mix (variety is deliberate - it brackets unobservable finish levels). Then ONE short positioning sentence on where this anchors the unit in its project's market.

Table 2 - Comparable Sales: # | Project | Unit # | Address | Class | Mos Ago | Tier | Sale Type | SF | Score. LOCKED COLUMN SET: emit exactly these columns, in exactly this order, on every run, with NO conditional additions or omissions. Never add Submarket, Region, or any other context column to this table; submarket and region context belongs in the narrative and Table 5 only. The frontend parser matches headers exactly. NO $/SF column (pricing lives in Table 3). Column rules:
- Project = the comp's CANONICAL project name from engine field `project` (comp["Project Name"]) VERBATIM, exactly as in "01 - Projects" and identical to Table 5's form; never street shorthand, never fold the unit in (the website joins this to load the project thumbnail).
- Unit # = engine field `unit` alone; mark the subject's own prior sale with a dagger on the Unit # cell plus a one-line footnote.
- Address = engine field `address`; render "N/A" if null, never fabricate.
- Subject row S first (its own Project / Unit / Address); averages row last with Project, Unit #, Address blank.

TAB 3 - COMP ADJUSTMENTS

**Adjustments** - TWO short sentences, 45 to 65 words (v3.0 length discipline), plus a conditional cap disclosure. Sentence one: the method framing plus the DOMINANT driver with its figure. Sentence two: names the NEXT-LARGEST drivers with their figures and NOTHING else. Signs always shown. CUT closing interpretive clauses ("keeping the in-submarket evidence largely intact" and similar). CUT CATEGORY RATE-DEFINITION CLAUSES ("size differences at 2% per 100 SF", "4.0% per point", "the 5.0% pre-construction incentive", "tier gaps translated to the subject's tier") - the six bullets below already define every category rate. The ONE exception is sale timing, which may carry "compounded at the measured X.X% rate" because that figure is the rate the engine actually measured and applied this run (growth_pct_used) rather than a fixed definition - never assert a rate the engine did not use. CAP DISCLOSURE (honest, conditional): when the engine's own per-comp values show a category landing EXACTLY on its cap (Sale Timing 25%, Wealth Index 25%, Unit Size 20%), append one sentence naming the capped categories and their caps, and state that the applied adjustment is held at the cap rather than the full computed difference. SILENT when nothing is capped. BUILD QUALITY CAP (v2.9): build quality clips at +/-8%; when the engine flags a comp as capped (the MEASURED difference exceeded the ceiling), append "Build quality at {+/-X.X}%, the category ceiling, with the measured difference exceeding it and capped." Table 4 lists SIX categories (Sale Timing, Wealth Index, Amenity Tier, Build Quality, Sale Type, Unit Size) plus Total. Pattern: "Each comparable is translated to the subject through six standardized adjustments applied additively to its unadjusted $/SF; the dominant driver is unit size at -X.XX%. The next largest are sale timing at +X.XX% and sale type at +X.XX%. On at least one comparable unit size reached its cap of 20%, so the applied adjustment is held at the cap rather than the full computed difference." Then these six bullets EXACTLY, category names bold, NO prose after the bullets:
- **Sale Timing**: compounded at the blended regional/statewide repeat-sales appreciation rate. Capped at 25%.
- **Wealth Index**: 4.0% per index point of difference. Capped at 25%.
- **Amenity Tier**: 5% to 20% depending on tier gap.
- **Sale Type** - 5.0% pre-construction incentive added to new-construction comps (the subject is a re-sale).
- **Build Quality**: 2.0% per Build Quality Index point of difference (construction materials plus common area finish above the tier floor). Capped at 8%.
- **Unit Size**: 2% per 100 SF of size difference. Capped at 20%.

Table 3 - Comp Adjustments: # | Project | Unit # | Wealth Index | Sale Timing | Amenity Tier | Build Quality Adj | Unit Size | Sale Type | Net Adj % | $/SF | Net Adj. $ PSF. (v2.9 adds Build Quality Adj after Amenity Tier and before Unit Size; legacy five-category reports without it still validate.) LOCKED COLUMN SET: emit exactly these columns, in exactly this order, on every run, with NO conditional additions or omissions. Never add Submarket, Region, or any other context column to this table; submarket and region context belongs in the narrative and Table 5 only. The frontend parser matches headers exactly. Project and Unit # follow the SAME split and canonical-name rules as Table 2 (Address not repeated).
- $/SF = the comp's unadjusted sale price per SF. Net Adj. $ PSF = the engine's per-comp `adj_psf` exactly (never recompute).
- Averages row last. TIE-OUTS: the averages row's Net Adj % must equal Table 1's Total Adjustment exactly, and its $/SF must equal Table 1's Comp Average exactly. Its Net Adj. $ PSF is the plain average of the column and will sit within a few dollars of the reconciled value - that small gap is expected covariance, never "correct" it.

Table 4 - Adjustment Component Averages: | Component | Avg Adj % | for the five categories plus Total, directly below Table 3, bold label "**Table 4 - Adjustment Component Averages**". Total must tie to Table 1's Total Adjustment. This table feeds the application's Total Adjustment breakdown popup - always present.

**Table 5 - Competitive Set** — directly below Table 4, bold label plus a TWO-SENTENCE intro paragraph immediately under the label, before the table. Sentence 1 (composition) - 35 to 45 words in the COMPRESSED form (v3.0 length discipline), cutting connective padding: "The subject's competitive set is the {N} {Region} projects competing for the same regional buyer pool, ranked by comps used: {k} Premium-Tier and {j} Standard-Tier." Count the ranked projects by tier rather than listing a tier-mix phrase. Sentence 2 (takeaway) - 50 to 65 words: position the subject's valued **$/SF** against the set's Avg $/SF range, then give ONE pricing or absorption implication grounded strictly in the table's own figures (Avg $/SF gaps, Comps Used, Mos Since Last Sale), KEEPING the full timing explanation and its figures. NEVER restate the range twice. Derive BOTH sentences only from the engine's competitive_set.selected rows and the valued $/SF: no cross-region color, no outside figures, no forecasts. SAME-PROJECT-ONLY CASE (common for units): when ZERO non-subject projects supplied retained comps, sentence 1 instead states plainly that all {n} valuation comps come from inside {Project} and that the table ranks the same-region projects competing for its buyer pool (all comparability backfill); NEVER count the subject project as a contributor and NEVER include the subject project as a Table 5 row. Columns: | Rank | Project | Submarket | Tier | Avg $/SF | Comps Used | Mos Since Last Sale | Score |. Comps Used is the number of the project's sales in the FINAL valuation comp set; contributing projects rank first (Score = average Selection Score of those comps, tying Table 5 to Table 2); backfill rows come ONLY from the subject's own region, comparability-ranked, with ranks 4 and 5 only at comparability 6.5 or higher. If fewer than 3 same-region projects exist, render only those that do (1 or 2 rows is acceptable), append the engine's note, and say so honestly in sentence 1 (for example "only {N} competing projects in the subject's region"): NEVER pad with cross-region projects. Render EXACTLY the engine's competitive_set.selected rows in order; ranks 4 and 5 appear only when the engine included them. Never add, drop, or reorder projects, and never recompute scores.

**Methodology** - closing paragraph, LAST ITEM IN THE REPORT: "This valuation employs a comparable sales approach anchored on sales within the subject's own project, drawing on 1,600+ Florida garage condominium transactions. Comparables are scored on three weighted factors (Recency 50%, Same-Project Class 35%, Size Match 15%) with a same-project core of up to 12 sales and adjacent-project backfill; an asymmetric outlier guard removes data errors while preserving genuine finish-level dispersion. Five standardized adjustments follow, and the final value is the comp average $/SF adjusted by the equal-weighted total adjustment, times subject square footage."


## CLOSING DISCLOSURE (required, both document halves)
The FINAL element of the Market Value Report AND of the Sale Listing Summary is this exact three-sentence footnote, italicized, with no heading above it:

*This report is a market analysis prepared by Storage Condo King from recorded comparable sales. It is not an appraisal and was not prepared by a licensed appraiser. Values shown are estimates and are not a substitute for an appraisal.*

Rules: last element after all other content, never omitted, collapsed, or truncated. Plain italic markdown only (no box, no bold, no all-caps, no icon). The PDF renderer restyles it (taupe, small, tan hairline rule); the site renders the italic markdown as-is.

---

# UNIT SUMMARY SPEC (owner-facing block; the final section of the single report document)

Mirror of the Cowork skill sck-unit-resale-valuation v3.2. The renderer NEVER reads this file at
runtime: render_report.py's sentence builders emit the prose, so this spec and that file must
always be edited together. The block is appended after the valuation half's closing disclosure,
separated by a horizontal rule, and opens with the exact H1 `# Unit Summary` (a frontend parsing
contract: do not alter that string).

SECTION ORDER (fixed, v3.2): Unit Value Summary, Your Unit, Market Summary, Location Overview,
Unit Highlights. Market Summary sits ABOVE Location Overview, matching the developer sale listing
order. Content moves with its section.

NO AUTHORED LINKS anywhere in the block (v3.1). The website renders the tab strip and the listing
calls to action, so an authored `#tab-...`, `/pre-sale-deals` or `#contact` link duplicates a live
control. Sections end on their last prose sentence or last bullet.

WHOLE-DOLLAR PSF throughout the block; the valuation Tables above keep 2-decimal precision for
tie-outs. Every figure comes from engine output; no valuation math in the renderer.

## Unit Value Summary
Value, $/SF and effective date, the finish-level band, the prior-sale trend line when the unit's
own sale is in the comp set, the product bow, and the concentration disclosure when same-project
share exceeds 80%. CLOSES with one action sentence (v3.2) tying value to what the unit has earned
and the owner's option to list it for sale on Storage Condo King. Prose only, no link, never
hard-sell.

## Your Unit
LEAD SENTENCE carries PRODUCT CHARACTER ONLY: project, tier, market or corridor position, and what
the product is built for. It must NOT contain the unit number, unit size, year built, or a tier-pill
restatement; the site's hero grid renders all of those directly above this tab.
Then EXACTLY 4 bold-headed bullets, in order:
- **Unit Profile:** address + parcel. Omitted ONLY when the unit has neither.
- **Construction:** read from "01 - Projects" for the subject's project: "Construction Materials",
  "Common Area Finish Level", and the flood zone with its risk read, as one plain sentence
  mirroring the developer sale Construction Materials bullet, e.g.
  "Tilt wall concrete, Luxury common areas, FEMA Flood Zone X (low risk)." Any null component
  renders "-" in its slot; NEVER drop the component and NEVER drop the bullet. SFHA zones
  (A, AE, AH, AO, AR, A99, V, VE) read "high risk"; every other zone reads "low risk".
- **Value Basis:** comp count and the same-project share.
- **Finish-Level Range:** the band in dollars and $/SF.

## Market Summary
OPENS on market depth as liquidity: "The {submarket} submarket recorded N sales in the trailing
twelve months at a $X/SF median, a re-sale market deep enough to price and absorb a listing."
When N is under 10, emit the honest count WITHOUT the depth claim. Then the unit's value, its comp
count and source shares, the average before adjustments and the net adjustment, and the competitive
set positioning. CLOSES with one sentence stating the owner's compounded growth or position as
EQUITY, never as advice.

## Location Overview
The project's Location Summary narrative extract, spliced with the ranked demographic strengths and
the wealth-index percentile clause. Prose submarket names. Falls back to demographic strengths when
no Location Summary exists.

## Unit Highlights
EXACTLY 5 bold-headed bullets (v3.1), chosen by this priority order, taking the first five that
qualify and dropping the rest silently. Bullets are NEVER merged to fit:
  1. Prior Sale Trend (only when the unit's own prior sale is in the comp set; suppresses cleanly
     and the next candidate moves up)
  2. Current Value
  3. Value Anchor (keeps the >80% concentration clause)
  4. Trophy Quality Product (keeps the finish-level range)
  5. Competitive Positioning (never names a project)
  6. Dynamic Growth Market (keeps the honest-cap language when it renders)
  7. Local Demand Drivers
The renderer raises on any count other than 5 and validate() independently counts the rendered
bullets, failing the run loudly rather than shipping a 6-bullet report.

## VOICE (v3.2)
Plain owner language over analyst language, figures untouched: "recent sales, weighted toward the
newest" not "time-adjusted evidence"; "the comp set's average before adjustments" not "unadjusted
average"; "sales recorded" not "transaction pool"; "no sales recorded in the last 60 months" not
"no qualifying sales in the analysis window"; "gives less to cross-check against other projects"
not "limits cross-market validation".

## CLOSING DISCLOSURE
The block ends with the same three-sentence italic footnote that closes the valuation half, so the
stored document carries it exactly twice.
