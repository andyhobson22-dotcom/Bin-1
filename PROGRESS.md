# Progress Log

Each improvement iteration appends an entry here. Newest at top.

---

## Iterations 2+3 (parallel agents) — Phase A complete + Leicester database

**Done (agent 1, `sim_2v2.html`):** A.2 movement quality (support depth enforced, awareness-based defender tracking, players go to ground), A.3 ruck micro-loop (`resolveRuckContest` in pure block — fast/slow/turnover/penalty all stat-traced, replaced the magic 35% rip), A.4 fatigue (0–100, −12 contest pts and 35% slower at max, energy bars). Central verification: avg break 30.7%; Curry wins fast ball 53.8% vs lone jackler; isolated Reed into double coverage = 36.4% turnover; fatigued break rate 31%→5%. Commit `0985706`.

**Done (agent 2, `leicester_db.html`):** 23-man Leicester Tigers database, identical schema/viewer to Sale (35 visible + 10 hidden per player, key-count verified 23/23). Cole scrum tech 93/pace 22, Reffell jackling 88, Steward high ball 92, Pollard goal kicking 93. Commit `d7541fe`. Phase C.9 satisfied.

**In flight:** integration agent building `full_match.html` — 15v15 Sale vs Leicester using the proven 2v2 pure engine, both databases, set pieces, kicks, formations (anti-stacking model), hidden stats, tactical pauses, headless 20-match scoreline validation.

**Next after that:** Phase C.8 decision — either fold Match Centre features into `full_match.html` or retire `match_engine_demo.html`; then Phase D (season shell).

---

## Iteration 1 — Phase A.1 complete: 2v2 contest maths tuned + headless harness

**Done:** Pure engine block added to `sim_2v2.html` (PURE-ENGINE-START/END markers, extractable for node testing). Power vs evasive carry profiles — carriers attack to their strengths, commentary reflects the style. Offload attempt gate (low Offload stat = takes the tackle instead). `runHarness(n)` prints outcome distributions.

**Evidence (5000 contests/matchup):** average break rate 30.8% (target ~33%); big hits 12.8% only in the elite-tackler-vs-power-runner matchup, near zero elsewhere; offload success 52–90% for Curry (Offload 58) vs 4–33% for Reed (Offload 42). All BRIEF §6 A.1 targets met. Committed `6a9b01c`, pushed.

**Next task:** Phase A.2 — movement quality in `sim_2v2.html`: support depth (never ahead of carrier), defenders track laterally, tackled players briefly go to ground.

---

## Baseline — loop initialised

**State:** Brief written (`BRIEF.md`). Assets: Sale Sharks DB (canonical schema, 35 visible + 10 hidden stats), 2v2 sim (mechanics testbed, needs tuning), Match Centre (commentary engine, dot overlay removed), player profile demo (approved), Flask season game (paused).

**Next task (from roadmap):** Phase A.1 — tune 2v2 contest maths + add headless distribution test harness.
