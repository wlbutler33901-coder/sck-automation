# SCK Automation Learnings

Read the last ~30 entries at the start of every routine run. Append only real lessons (failures, corrections, surprises, workarounds), one line each, newest last. Commit after appending.

- 2026-07-19 | make-pipeline | Bare webhook hits (link scanners) crashed the email module and auto-disabled the scenario | Filter added in Make: payloads without subject+html are dropped silently; never remove it
- 2026-07-20 | permit-scanner | Chromium TLS reset by the egress proxy on every site | Drive chromium via Playwright but fulfill requests through Node fetch (harness documented in the permit playbook)
- 2026-07-27 | scanner | run_type logged as 'nightly_scan' then 'project_scan' instead of 'scan', digest missed rows | run_type is a constant: exactly 'scan'; digest keeps a tolerant IN-list as a backstop
- 2026-07-31 | enrichment | id sequence on "05 - Developers - New" collided with an existing row on insert | Sequences resynced to MAX(id); never supply explicit ids on staging inserts; on collision retry once
- 2026-08-01 | scanner | "Bonita Auto Vault" staged as new; it is Bonita Motor Vault (live) | Dedup is multi-signal at COUNTY level: distinctive-token match after stripping generic product words, address, parcel, developer
- 2026-08-03 | enrichment | Routine instructions referenced an outreach TEMPLATE / TIDBIT MENU not present in the repo skill (v3 zip never merged to main); drafting correctly skipped rather than improvised | Version self-check added: skills carry a marker section; when instructions and skill drift, log SKILL-OUT-OF-DATE loudly; after every skill update, verify the commit is on origin/main
- 2026-08-03 | scanner | 3am run did not execute (no run_summary); digest warned correctly | Detection works; check the routine Runs list for the failure reason; 14-day lookback self-heals coverage the next night
