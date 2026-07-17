# Improve the Rugby Manager build — one iteration

You are running one iteration of a continuous improvement loop on this rugby union manager game.

## Procedure (follow exactly)

1. **Read `BRIEF.md`** — it is the source of truth: vision, hard rules, stat schema, engine architecture, roadmap.
2. **Read `PROGRESS.md`** — see what previous iterations completed and what was flagged as next.
3. **Pick exactly ONE task**: the topmost unfinished roadmap item from BRIEF.md §6 (or the "next task" named at the top of PROGRESS.md if it matches the roadmap order). Do not batch multiple roadmap items into one iteration.
4. **Implement it completely** while obeying every Hard Rule in BRIEF.md §2 — standalone HTML, vanilla JS, stats-driven probabilities, engine/UI separation, smooth engine-driven dots, dark theme.
5. **Verify before committing** (BRIEF.md §7):
   - `node -e "..."` syntax check on any edited HTML's script block.
   - If engine maths changed: run the headless distribution harness and check outcome frequencies look like real rugby; note the numbers.
   - If visuals changed: serve with `python3 -m http.server`, screenshot with playwright, and actually look at the screenshot.
6. **Commit and push** to `claude/rugby-manager-game-Ecnnt`. Plain-English commit body a beginner can follow.
7. **Update `PROGRESS.md`**: prepend an entry — what was done, evidence it works (numbers/screenshot findings), and name the next roadmap task. Commit and push that too.

## Constraints

- One roadmap task per iteration. Small and shippable beats big and broken.
- Never break an existing file: if a change risks regressing something the owner approved (player profile layout, DB viewer, 2v2 core loop), verify that file still works.
- Never touch the Flask app (`app.py`, `models/`, `engine/`, `game/`, `templates/`) — it is paused per the brief.
- If a roadmap item turns out to be genuinely blocked, note why in PROGRESS.md and take the next item instead.
- If everything in Phases A–C is complete, use the iteration to raise quality: commentary variety, tuning from harness data, code cleanup within files — and say so in PROGRESS.md.
