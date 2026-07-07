# Search Playbook (merged from fl-car-condo-scanner)

## Keywords (cycle keyword x place x recency cue)
car condo, garage condo, luxury motor condo, motor suites, moto cave, auto storage condominium, private garage condominium, motorcoach condo, motorplex, auto clubhouse, luxury car storage, toy storage condos, garage suites, toy barn.

## Recency cues
2026, new, coming soon, now reserving, pre-sale, groundbreaking, breaks ground, proposed, rezoning, site plan, announced.

Examples:
- "garage condo" OR "car condo" {city1} OR {city2} 2026 new
- "motor suites" {city} groundbreaking
- luxury car condo {metro} "now reserving" OR "pre-sale"
- "auto storage condominium" {state} proposed rezoning 2026

## Second pass (mandatory on every hit)
Search the project name and the developer name separately to pull stage, unit count, pricing, principal, and a contact path:
- "{project name}" {city} units price
- "{developer / principal}" garage condo {state}
- "{developer}" headquarters office phone
- site:linkedin.com/company {developer}

## Source types (never rely on one)
a. Open web via the patterns above.
b. Aggregators / market trackers: onlygaragecondos.com + its Substack (treat listings without a named developer as low confidence), operator blogs and "garage condos in {state}" directory pages.
c. Known-operator expansion pages - SEEDS, not the goal. FL: Motor Enclave, Paddock1, Motocave, Luxe Dream Garage, Naples Motor Condos, Auto Clubhouse, Florida Premier, Revault/Newgard. Multi-state: The Vault (Lee Janik), Motor Vault (Phoenix AZ), Motor District (Westfield IN), Storage Caves, ReVest, Stables Motor Condos. A new location from a known operator is a NEW candidate row, never a near-match of the operator's other sites.
d. Regional business press, past ~10 days: Business Observer, Tampa Bay / South Florida / Orlando / Jacksonville / Charlotte / Triangle / Charleston Business Journals, Gulfshore Business, Bisnow metros, Atlanta Agent, urbanize sites, GSA Business Report, TOWN Carolina, Post and Courier.
e. Pre-sale marketing pages: "now reserving", "coming soon", broker pre-sale announcements.
f. Permit/zoning portals: verification of stage/parcel only, not primary discovery.

## Stage taxonomy (financing relevance, highest first)
1. Land Acquisition / Planning - site control, no capital placed.
2. Permitting / Pre-Sale - entitlements moving, reservations opening. PRIME financing window.
3. Pre-Construction / Now Selling - groundbreaking near.
4. Under Construction - bridge/gap/refi still viable.
5. Completed / Sold Out - relationship intel only.
Map to "Project Status": 1-3 -> Planned (stage detail in scan_notes), 4 -> Under Construction, 5 -> Completed.

## Financing classification (set on every insert)
- financing_opportunity: Land Acquisition | Construction | Bridge/Gap | Recap/Takeout.
- financing_relevance: High (early stage + named sponsor + active submarket) | Medium | Low (completed, or no sponsor identified).

## Sub-type (record in scan_notes)
Luxury Car Condo | Flex/Garage Condo | Motorcoach/RV | Boat adjacent | Mixed (auto + showroom/social) | Track-Side.
