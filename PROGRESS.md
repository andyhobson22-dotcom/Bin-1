# Progress Log

Each improvement iteration appends an entry here. Newest at top.

---

## Iteration 1 — Phase A.1 complete: 2v2 contest maths tuned + headless harness

**Done:** Pure engine block added to `sim_2v2.html` (PURE-ENGINE-START/END markers, extractable for node testing). Power vs evasive carry profiles — carriers attack to their strengths, commentary reflects the style. Offload attempt gate (low Offload stat = takes the tackle instead). `runHarness(n)` prints outcome distributions.

**Evidence (5000 contests/matchup):** average break rate 30.8% (target ~33%); big hits 12.8% only in the elite-tackler-vs-power-runner matchup, near zero elsewhere; offload success 52–90% for Curry (Offload 58) vs 4–33% for Reed (Offload 42). All BRIEF §6 A.1 targets met. Committed `6a9b01c`, pushed.

**Next task:** Phase A.2 — movement quality in `sim_2v2.html`: support depth (never ahead of carrier), defenders track laterally, tackled players briefly go to ground.

---

## Baseline — loop initialised

**State:** Brief written (`BRIEF.md`). Assets: Sale Sharks DB (canonical schema, 35 visible + 10 hidden stats), 2v2 sim (mechanics testbed, needs tuning), Match Centre (commentary engine, dot overlay removed), player profile demo (approved), Flask season game (paused).

**Next task (from roadmap):** Phase A.1 — tune 2v2 contest maths + add headless distribution test harness.
