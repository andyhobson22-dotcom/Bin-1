# Rugby Union Manager — Project Brief

**This is the source of truth for the project.** Every improvement iteration must read this file first, then `PROGRESS.md` to see what has already been done, then pick the single highest-value next task from the roadmap below.

---

## 1. Vision

A rugby union management game in the spirit of **Championship Manager 3 / Football Manager**: a deep stats-driven simulation where every match outcome traces back to real player attributes, watched through a Championship-Manager-style dot visualiser and text commentary. English Premiership setting. Sale Sharks is the reference/demo club, Tom Curry the reference player.

The owner of this project is a **beginner developer**. All deliverables must be double-clickable standalone HTML files (no build steps, no servers, no frameworks). Instructions to view anything must be: "pull, double-click the file."

---

## 2. Hard Rules (never violate)

1. **Single self-contained HTML files.** Vanilla JS only. No CDNs except the Google Fonts import for Inter.
2. **Every probability calculation traces to at least one real player stat.** No magic numbers driving outcomes without a stat behind them.
3. **Engine logic and UI rendering are separated** into clearly commented sections even within one file (`/* ═══ ENGINE ═══ */`, `/* ═══ UI ═══ */`).
4. **Pure, testable probability functions** — no side effects inside resolvers.
5. **Dots are driven by the engine, not pre-scripted animations.** The engine decides; the dots show it. Movement is smooth (requestAnimationFrame lerp), never teleporting.
6. **Dark theme**: bg `#0a0e13`, cards `#12171e`, text `#f0f4f8`, accent `#3b82f6`, green `#22c55e`, yellow `#eab308`, red `#ef4444`, border `#1e293b`. Font: Inter.
7. **Commit and push every completed increment** to branch `claude/rugby-manager-game-Ecnnt` with a clear message. Verify JS syntax (`node -e "new Function(...)"`) before committing.
8. Home team = blue, away team = red, ball = white.

---

## 3. Player Data Model (canonical schema)

Scale: **1–99** for visible stats. Hidden stats are **tiered: Low / Medium / High / Elite**.

### Visible — Physical (7)
Stopping Power, Explosiveness, Leg Drive, Pace, Acceleration, Agility, Strength

### Visible — Mental (9)
Aggression, Composure, Concentration, Awareness, Running Lines, Discipline, Tenacity, Scanning, Positioning

### Visible — Technical (14)
Long Passing, Handling, High Ball, Offload, Tackling, Rucking, Mauling, Jackling, Grubber, Chipping, Box Kicking, Stepping, Short Passing, **Touch Finder** (Touch Finder lives in Technical, NOT Set Piece)

### Visible — Set Piece (5)
Goal Kicking, Scrum Drive, Scrum Tech, Jumping, Lifting

### Hidden (10, tiered)
Consistency, Big Game Temperament, Injury Proneness, Dirtiness, Work Rate, Versatility, Professionalism, Ambition, Loyalty, Temperament

### Meta
Name, Age, Position, Secondary Positions, Nationality, Height (cm), Weight (kg), Contract End, Wage, Form, Fitness, Morale, Potential

### Position familiarity (for the player profile visualiser)
5 tiers per position: **faded** (none), **red** (minimal), **yellow** (some), **blue** (competent), **green** (natural). e.g. Tom Curry: green 6/7/8, yellow 12, red wings, faded everything else.

---

## 4. Match Engine Architecture (CM3-inspired)

Discrete-event state machine on top of a probability model — NOT physics simulation:

```
while match_not_finished:
    update_time / fatigue / momentum
    choose_next_actor        (who has the ball)
    choose_next_action       (weighted by that player's stats + tactics)
    resolve_action_success   (attacker stats vs defender stats + noise)
    update_ball_position_and_possession
    check_for_score / card / set_piece / injury
    generate_text_commentary
    move_dots_to_reflect_new_state
```

**Key contest resolutions (all attacker-vs-defender weighted comparisons + random noise):**
- **Carry/beat defender**: stepping + agility + pace + strength + explosiveness vs tackling + stopping power + agility + awareness
- **Pass/interception**: short_passing + handling + composure + awareness vs awareness + scanning + pace
- **Offload in tackle**: offload + composure + awareness vs tackler strength + awareness
- **Ruck/jackal**: rucking + strength (arriving players) vs jackling of defenders; Discipline reduces penalty risk
- **Ruck speed is the engine heartbeat**: Slow / OK / Quick / Lightning — quick ball unlocks backline moves
- **Scrum**: scrum_drive + scrum_tech + strength + leg_drive pack vs pack
- **Lineout**: hooker scanning+awareness (throw) vs jumping + lifting contest
- **Kicks**: box_kicking / touch_finder / grubber / chipping / high_ball vs receiver high_ball + positioning, chasers' pace
- **Goal kicks**: goal_kicking vs distance/angle
- **Cards**: high aggression + low discipline, amplified under momentum pressure
- **Momentum**: hidden per-team score; shifts on scores/turnovers/dominant phases; ±modifier on following events; commentary references it

**Tactics (team instructions)** modify probabilities: defensive width, attacking width, breakdown commitment, kick frequency, set piece focus. Position roles (Walking Pillar, Second 8, All Court, Darter, Playmaker, Field Marshal, To The Line, Full Flair, Territory Targeter, Looper, Poacher, Flyer, Kettle, Jackler, Destroyer, Treacle, Work Horse, etc.) and the defensive drop-behind system (1–3 backs as Full Cover/Watcher) exist in the Flask prototype and must eventually reach the HTML engine.

---

## 5. Current Assets (state of the repo)

| File | What it is | State |
|---|---|---|
| `sale_sharks_db.html` | 23-man Sale Sharks database, 35 visible + 10 hidden stats, browsable viewer | **Canonical data source.** Good. |
| `sim_2v2.html` | 2v2 mechanics testbed: run → tackle contest → beat/offload/smashed → dots move in real time | **Active focus.** Mechanics approved in principle, needs polish/tuning. |
| `match_engine_demo.html` | "Match Centre" — full 23v23 match, commentary feed, stats sidebar, tactical pauses at 20'/40'/60' | Works, but dot overlay was rejected; visualiser now separate. |
| `match_sim.html` | First attempt at full 30-dot live pitch | **Broken/superseded** — players stacked on ball. Superseded by 2v2 approach. |
| `player_demo.html` | Player profile screen with position-familiarity pitch visualiser (forwards/backs toggle) | Approved layout. |
| `app.py` + Flask app | Full season game (league, training, transfers, tactics, finances) | **Paused.** Don't touch until HTML engine is proven. |

---

## 6. Roadmap (ordered — the loop picks the topmost unfinished item)

### Phase A — Perfect the 2v2 core (current)
1. **Tune the 2v2 contest maths** so outcomes feel like rugby: ~1 in 3 carries beat the first defender, big hits are rare but memorable, offload success tracks the Offload stat visibly. Log outcome frequencies over 100 simulated contests to verify (add a hidden test harness function that runs contests headlessly and prints distribution to console).
2. **Fix movement quality in `sim_2v2.html`**: support runner should hold depth behind the carrier (never ahead), defenders should track laterally with the carrier, tackled players should briefly go to ground (dot flattens/dims) before the ruck resolves.
3. **Add the ruck micro-loop to 2v2**: after a tackle, both nearby players contest (rucking vs jackling); show ruck speed result; slow ball delays next action, turnover swaps attack.
4. **Add fatigue to 2v2**: repeated contests drain a fitness value that visibly slows dot speed and lowers contest scores.

### Phase B — Scale the sim
5. **4v4** (`sim_4v4.html` or evolve 2v2 file): adds a passing chain (2 support options), defensive line spacing, and the drift/press decision using Positioning + Scanning.
6. **7v7**: adds set-piece-lite (tap restart), kicks (grubber/chip with chase), and zones/territory.
7. **15v15**: full formations from the Flask prototype's position roles; scrums, lineouts, mauls; this becomes the real match engine.

### Phase C — Reunify
8. **Integrate the proven dot engine into the Match Centre** (`match_engine_demo.html`): pitch during passages, commentary between; tactical pauses stay.
9. **Drive both teams from database files**: extract squads to embedded JSON blocks with the full 45-stat schema; build a Leicester database to match `sale_sharks_db.html`.
10. **Hidden stats live in the engine**: Consistency → per-match stat wobble; Big Game → finals/derby modifier; Injury Proneness → injury rolls; Dirtiness → card risk beyond Discipline; Work Rate → off-ball involvement rate.

### Phase D — Game shell
11. Wire the Flask season game to the new engine, or port the season loop to HTML/localStorage (decide when we get there — prefer whatever keeps "double-click to play" true).

### Continuous (do alongside any task when touched)
- Keep `sale_sharks_db.html` schema canonical; propagate schema changes everywhere.
- Improve commentary variety whenever an engine file is edited.
- Keep README-style comments at the top of each HTML file explaining what it is and how to open it.

---

## 7. Quality Bar / Definition of Done for each iteration

- JS syntax verified with node before commit.
- Open-in-browser smoke test via `python3 -m http.server` + playwright screenshot when the change is visual; inspect the screenshot before declaring done.
- Outcome distributions sanity-checked when engine maths change (run the headless harness, print to console, paste summary in commit message).
- Committed AND pushed to `claude/rugby-manager-game-Ecnnt`.
- `PROGRESS.md` updated with: what was done, evidence it works, what the next task is.
- Plain-English summary suitable for a beginner in the commit body.
