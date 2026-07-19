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

**Valuation Overview** - THREE compact paragraphs, no headers between them:
- Paragraph 1 (2-3 sentences): market value and $/SF; the unit and project (tier); the comp evidence LEADING WITH THE SAME-PROJECT COUNT ("{class_a} of {n_comps} comparables are sales inside {project} itself", and note if the subject's own prior sale is among them); the largest adjustment driver. Every figure bold.
- Paragraph 2 (ONE sentence, ~35 words): the {n} comparables average an unadjusted ${x}/SF and a {+x.xx%} total adjustment reconciles to ${x}/SF (${value} at {N,NNN} SF), with adjusted values spanning ${min} to ${max}/SF, the finish-level band a shell versus a built-out unit could realize.
- Paragraph 3 (ONE compact sentence): the standing buildout caveat - finish level is not observable in recorded sales, so the value reflects a market-average buildout (customized units may exceed it; shells may trail it) - plus a brief outlier/thin-data clause only if applicable. No confidence label.

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

**Adjustments** - ONE sentence combining the method framing with this run's two largest average drivers (signs, causes, and the applied rate from engine metadata growth_pct_used - never assert a rate the engine did not use), on this pattern: "Each comparable is translated to the subject through five standardized adjustments applied additively to its unadjusted $/SF; this run's largest drivers are sale timing (+X.X%, compounded at the measured X.X% rate) and sale type (+X.X%, the 5.0% pre-construction incentive added to new-construction comps)." Then these five bullets EXACTLY, category names bold, NO prose after the bullets:
- **Sale Timing**: compounded at the blended regional/statewide repeat-sales appreciation rate. Capped at 25%.
- **Wealth Index**: 4.0% per index point of difference. Capped at 25%.
- **Amenity Tier**: 5% to 20% depending on tier gap.
- **Sale Type** - 5.0% pre-construction incentive added to new-construction comps (the subject is a re-sale).
- **Unit Size**: 2% per 100 SF of size difference. Capped at 20%.

Table 3 - Comp Adjustments: # | Project | Unit # | Wealth Index | Sale Timing | Amenity Tier | Unit Size | Sale Type | Net Adj % | $/SF | Net Adj. $ PSF. LOCKED COLUMN SET: emit exactly these columns, in exactly this order, on every run, with NO conditional additions or omissions. Never add Submarket, Region, or any other context column to this table; submarket and region context belongs in the narrative and Table 5 only. The frontend parser matches headers exactly. Project and Unit # follow the SAME split and canonical-name rules as Table 2 (Address not repeated).
- $/SF = the comp's unadjusted sale price per SF. Net Adj. $ PSF = the engine's per-comp `adj_psf` exactly (never recompute).
- Averages row last. TIE-OUTS: the averages row's Net Adj % must equal Table 1's Total Adjustment exactly, and its $/SF must equal Table 1's Comp Average exactly. Its Net Adj. $ PSF is the plain average of the column and will sit within a few dollars of the reconciled value - that small gap is expected covariance, never "correct" it.

Table 4 - Adjustment Component Averages: | Component | Avg Adj % | for the five categories plus Total, directly below Table 3, bold label "**Table 4 - Adjustment Component Averages**". Total must tie to Table 1's Total Adjustment. This table feeds the application's Total Adjustment breakdown popup - always present.

**Table 5 - Competitive Set** — directly below Table 4, bold label plus a TWO-SENTENCE intro paragraph immediately under the label, before the table. Sentence 1 (composition): the set size, the region constraint, and what anchors the set: projects supplying valuation comps rank first, remaining same-region projects follow by comparability, and name the tier mix (pattern: "The subject's competitive set groups the {N} {Region} projects competing for the same regional buyer pool: the {k} projects supplying valuation comps rank first, backfilled by comparability, spanning {tier mix}."). Sentence 2 (takeaway): position the subject's valued **$/SF** against the set's Avg $/SF range or rank, then give ONE pricing or absorption implication grounded strictly in the table's own figures (Avg $/SF gaps, Comps Used, Mos Since Last Sale). Derive BOTH sentences only from the engine's competitive_set.selected rows and the valued $/SF: no cross-region color, no outside figures, no forecasts. SAME-PROJECT-ONLY CASE (common for units): when ZERO non-subject projects supplied retained comps, sentence 1 instead states plainly that all {n} valuation comps come from inside {Project} and that the table ranks the same-region projects competing for its buyer pool (all comparability backfill); NEVER count the subject project as a contributor and NEVER include the subject project as a Table 5 row. Columns: | Rank | Project | Submarket | Tier | Avg $/SF | Comps Used | Mos Since Last Sale | Score |. Comps Used is the number of the project's sales in the FINAL valuation comp set; contributing projects rank first (Score = average Selection Score of those comps, tying Table 5 to Table 2); backfill rows come ONLY from the subject's own region, comparability-ranked, with ranks 4 and 5 only at comparability 6.5 or higher. If fewer than 3 same-region projects exist, render only those that do (1 or 2 rows is acceptable), append the engine's note, and say so honestly in sentence 1 (for example "only {N} competing projects in the subject's region"): NEVER pad with cross-region projects. Render EXACTLY the engine's competitive_set.selected rows in order; ranks 4 and 5 appear only when the engine included them. Never add, drop, or reorder projects, and never recompute scores.

**Methodology** - closing paragraph, LAST ITEM IN THE REPORT: "This valuation employs a comparable sales approach anchored on sales within the subject's own project, drawing on 1,600+ Florida garage condominium transactions. Comparables are scored on three weighted factors (Recency 50%, Same-Project Class 35%, Size Match 15%) with a same-project core of up to 12 sales and adjacent-project backfill; an asymmetric outlier guard removes data errors while preserving genuine finish-level dispersion. Five standardized adjustments follow, and the final value is the comp average $/SF adjusted by the equal-weighted total adjustment, times subject square footage."


## CLOSING DISCLOSURE (required, both document halves)
The FINAL element of the Market Value Report AND of the Sale Listing Summary is this exact three-sentence footnote, italicized, with no heading above it:

*This report is a market analysis prepared by Storage Condo King from recorded comparable sales. It is not an appraisal and was not prepared by a licensed appraiser. Values shown are estimates and are not a substitute for an appraisal.*

Rules: last element after all other content, never omitted, collapsed, or truncated. Plain italic markdown only (no box, no bold, no all-caps, no icon). The PDF renderer restyles it (taupe, small, tan hairline rule); the site renders the italic markdown as-is.
