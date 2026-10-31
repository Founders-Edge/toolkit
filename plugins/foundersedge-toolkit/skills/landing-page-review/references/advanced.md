# Advanced: fallbacks, resuming, run folder

Read this only when SKILL.md sends you here.

## In-browser screenshots (bot-walled pages)

**Fairness rule: one screenshot method for the whole run.** If any page bot-walls headless
Chrome (shoot.mjs warns, or the image shows a captcha / "Just a moment"), switch the **entire
run** to in-browser capture. Set `"screenshotMethod": "in-browser"` in the brief, then for every
page navigate the run tab to it (competitors live, the target at
`http://127.0.0.1:{port}/site/vN/index.html`) and:

1. `rm -f ~/Downloads/lpr-shot-<slug>-<id>-*` (only this run's files: other runs may be
   downloading at the same time). Chrome renames repeat downloads to `name (1).png`, so
   leftover files would be picked up instead of the new ones.
2. Run `{skill}/scripts/shots.js` (paste it whole into `javascript_tool`) with
   `window.__LPR_OPTS = { prefix: "lpr-shot-<slug>-<id>" }`, using the competitor id or `vN`
   for the target.
3. Strip the prefix while moving: for each `~/Downloads/lpr-shot-<slug>-<id>-*.png`, move it to
   `{run}/shots/<competitors|target>/<id>-….png`. Delete any old `<id>-*` tiles there first.

In this mode the design agent still self-checks with shoot.mjs, but you re-shoot every new
target version in-browser before `new_round.py`, so all judged images come from one method.
Mention in the final report that html2canvas renders some CSS less faithfully. In-browser
captures have no truncation sidecar, so judges are told a page continues below whenever it
used every tile.

## Resuming a run

To keep iterating on an existing run (a winner from an older version of the skill, or a
round-cap run with a new budget):

1. Reuse `{run}` and restart the local server (Step 2, marker check included).
2. Bring `brief.json` up to the current schema: `judgeUseCase`, `capturedVariant`, `reserves`,
   `slop`, `models` (including `slop`), `timeouts`, and `stopRule.confirmRounds`. Missing
   `stopRule` keys (`tolerance`, `inputRounds`) take their defaults. Raise `stopRule.maxRounds`
   if needed.
3. Re-shoot the latest `site/vN` and every competitor with the current shoot.mjs, so judged
   images match the current capture method (shoot.mjs clears each page's old tiles itself).
4. Rounds judged by an older version of the skill don't count as confirmations: the first
   resumed round of a passing version is never its own confirmation. Note this in
   `decisions.md`.
5. Continue at Step 7 with the next round number and the latest version as current.

## Competitor changes mid-run

If a competitor turns out to have pivoted, shut down or been acquired and now sells something
else (check its hero during Step 6), swap in a verified reserve before Round 1. After Round 1,
keep the lineup unless the page no longer loads, so scores stay comparable. Log either case in
`decisions.md`.

## Run folder

```
landing-page-review/<slug>-<date>/
├── brief.json                 ICP, use case, competitors, judge personas, stop rule, models
├── decisions.md               choices made without the user, with reasoning
├── site/v0/index.html         captured original
├── site/vN/{index.html,CHANGELOG.md,TODO.md}
├── shots/target/vN-{desktop,mobile}-NN.png (+ vN-{desktop,mobile}.json sidecars)
├── shots/competitors/<id>-{desktop,mobile}-NN.png (+ sidecars)
├── rounds/rN/{mapping.json,round.json,prompts/,pages/,judges/*.json,tally.json,feedback.md}
└── report.html
```
