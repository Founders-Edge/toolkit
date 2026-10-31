---
name: landing-page-review
description: >
  Pit a startup's landing page against its top competitors in front of a blind panel of five
  AI buyer personas built from the startup's ICP, then redesign a local copy of the page until
  the panel picks it. Use this skill whenever someone wants to review, improve, test or
  benchmark their landing page, homepage or marketing page against competitors.
  Triggers on: "review my landing page", "how does my landing page compare", "make my homepage
  convert better", "would buyers pick us over competitors", "benchmark my website against
  competitors", "run my landing page through a panel", "landing page review".

  The panel (2 buyers, 2 influencers, 1 decision maker) scores clarity, offer, value and
  professionalism and force-ranks the lineup; a separate check stops the redesign from getting
  more generic than the original; nothing gets invented, and missing proof becomes a to-do
  list for the founder. The loop ends when 4 of 5 judges rank the page #1, it leads (or is
  within judge noise of) every dimension, and that holds on a confirmation round (max 5 rounds,
  stopping early if scores plateau or the gap needs facts only the founder has). Produces an HTML report.

  Always use this skill for landing-page reviews — do not critique a page from memory or from a
  single screenshot.
---

# Landing Page Review

Puts the founder's landing page in a blind lineup with its top competitors, has a panel of five
buyer personas score and rank them, and keeps redesigning a local copy until the panel picks it.

> **Founders:** the judges are AI personas built from *your* ICP. They're a fast
> stand-in for showing the page to buyers, not a replacement for it. Use the result to decide
> what to test with real people, and fill every `TODO` with real proof before shipping.

**Requirements:** Google Chrome, Node.js 22+ and Python 3, on macOS or Linux. The Claude in
Chrome extension is only needed for pages that block headless Chrome. On Windows, use
`python`, `move` and `start` in place of `python3`, `mv` and `open`.

**Model usage (tell the user before Round 1):** every round runs five judges on Haiku, each
viewing about 20 screenshots, a slop judge on Sonnet, and a Sonnet design agent when a
redesign is needed. The session running this skill does mostly orchestration, so **Sonnet is
enough for it**; suggest it if the user is on Opus.

**Keep screenshots out of your own context.** Every image you Read stays in your context and
is re-billed on every later turn. Rely on the scripts' warnings; when a visual check is
needed, spawn a `general-purpose` agent with `model: "haiku"`, give it the image paths and the
question, and ask for a one-line answer.

**Responsible use:** run this on a page the user owns or is allowed to change. Competitor pages
are captured as screenshots for the user's private evaluation only; don't republish them or
the copied page.

---

## Workflow

```
1. INTAKE      → target page URL (+ ICP if the user has one)
2. SETUP       → run folder, local server, Chrome tab
3. CAPTURE     → snapshot the target page + page intel (headless Chrome)
4. RESEARCH    → ICP and use case, find + verify competitors → user confirms
5. BRIEF       → brief.json with the 5 judge personas
6. SCREENSHOT  → target v0 + competitors at 1440px and 390px
7. ROUND LOOP  → new_round → blind judges + slop judge → tally → winner / confirm / redesign
8. REPORT      → report.html, summary, stop server
```

Paths below: `{skill}` = this skill's folder, `{run}` = the run folder, `{port}` = the local
server port. **Shell variables don't survive between Bash calls**, so always write these out as
literal absolute paths.

**Running it straight through.** When the user asks you to run it without stopping, or nobody
is available to answer questions, never ask. Infer the ICP if it's missing, pick the use case
and the 3 strongest verified competitors yourself (keeping 1–2 verified reserves), skip opening
the report, and log every choice you'd normally confirm, with its reasoning, in
`{run}/decisions.md`. Anything this file says to "tell the user" goes there too.

---

## Step 1: Intake

Ask in one message (plain text, since both answers are free-form):

1. **Which page?** URL of the landing, marketing or home page to improve.
2. **Who is the ICP?** (optional) Role, company type and size, and what they're trying to get
   done. One or two sentences is plenty, e.g. "Heads of RevOps at 50–500 person B2B SaaS
   companies who are drowning in CRM hygiene work."

If they don't give an ICP, infer it in Step 4 from the page itself: who the copy addresses, the
use cases and customer logos it shows, the FAQ, pricing tiers, and "for teams / for enterprise"
language. Mark it `"icpSource": "inferred"` in `brief.json` and include it in the Step 4
confirmation.

## Step 2: Setup

Pick `{run}` = `<cwd>/landing-page-review/<company-slug>-<YYYYMMDD>` (absolute), then:

```bash
mkdir -p {run}/site/v0 {run}/shots/target {run}/shots/competitors {run}/rounds
node --version   # need >= 22 for scripts/shoot.mjs
```

Serve the run folder so captured and redesigned pages load like real websites. Start it with
`run_in_background`, then confirm it's serving **this** run. Other runs may be serving their own
folders on nearby ports, so a 200 alone proves nothing. Check for a marker file:

```bash
echo "{run}" > {run}/.lpr-run
python3 -m http.server 8765 --bind 127.0.0.1 --directory {run}     # background
curl -s http://127.0.0.1:8765/.lpr-run                            # must print {run}; else try 8766…
```

Only if you capture in Claude in Chrome (the Step 3 fallback), load its tools in **one**
ToolSearch call:
`select:mcp__claude-in-chrome__tabs_context_mcp,mcp__claude-in-chrome__tabs_create_mcp,mcp__claude-in-chrome__navigate,mcp__claude-in-chrome__javascript_tool,mcp__claude-in-chrome__computer`
Call `tabs_context_mcp`, then always create your **own** tab with `tabs_create_mcp`. Never
drive a tab you didn't create, since other runs may share the browser. If a call later fails
because the tab or group is gone, create a new tab and carry on.

If you need Claude in Chrome and it isn't connected, tell the user and stop.

## Step 3: Capture the target page

Capture headlessly by default:

```bash
node {skill}/scripts/capture_headless.mjs <target url> {run}/dl '{"prefix":"lpr-{slug}-v0"}'
mv {run}/dl/lpr-{slug}-v0.html {run}/site/v0/index.html
```

It prints the same result as the in-browser capture below (page intel, `fonts`, `warnings`).
Skip to "Move its embedded fonts" unless the result shows a bot wall, an empty H1 list, or a
"page text dropped" warning. Then capture in Claude in Chrome instead: navigate your tab to the
target URL. Clear any stale copy first
(`rm -f ~/Downloads/lpr-{slug}-v0*.html`; Chrome renames repeat downloads, so `mv` would grab
the old one). Read `{skill}/scripts/capture.js` once, then run it with **one**
`javascript_tool` call:

```js
window.__LPR_OPTS = { prefix: "lpr-{slug}-v0" };
/* full contents of capture.js */
```

It scrolls the page (firing lazy images and reveal animations), dismisses cookie banners, and
downloads a self-contained `lpr-{slug}-v0.html`: asset URLs absolute, stylesheets inlined from
their original text, web fonts embedded, and framework JS stripped on framework sites (Next,
Nuxt, Gatsby, Webflow, React) so edits aren't overwritten by re-hydration. When
`html.scriptsStripped` is true, tell the user the local copy is a static render: carousels or
tabs may freeze, and the design agent re-adds any that matter with plain JS.

It returns compact **page intel** (title, meta description, H1, H2s, CTA labels, the first 300
characters of copy) plus `fonts` and `warnings`. For the full copy, read the downloaded HTML.

- If the call returns `{}` or a pending promise, query `JSON.stringify(window.__LPR_RESULT)`
  again until its `status` is `done` or `error`.
- Chrome may ask the user to "allow multiple downloads" the first time. Tell them to allow it.
- **Act on every warning.** A custom element that won't render (e.g. a `<mux-player>` video)
  needs its script restored or a static poster image in its place. A third-party embed (forms,
  schedulers, video) may render empty, so restore it or rebuild it natively. Otherwise v0 is
  judged on breakage the live page doesn't have.

Move its embedded fonts into shared files (this cuts the HTML the design agent reads every
round by more than half), and compare it with the live page. After an in-browser capture, first
`mv ~/Downloads/lpr-{slug}-v0.html {run}/site/v0/index.html`.

```bash
python3 {skill}/scripts/extract_assets.py {run}/site/v0/index.html
node {skill}/scripts/shoot.mjs --out {run}/shots/target \
  v0=http://127.0.0.1:{port}/site/v0/index.html live=<target url>
```

Have a Haiku agent compare **every** `v0-*` tile with the matching `live-*` tile, desktop and
mobile, and report differences in a few lines. Check the H1 text first: many startup sites A/B-test their hero, so a different
headline in `live` means a different variant, not a broken capture. In that case compare
layout, typeface and styling only. Record the captured variant (H1 + primary CTA) in
`brief.json → capturedVariant`. Fix anything broken in the copy (blank sections, empty
embeds, missing styles, wrong typeface); re-capture with `stripScripts: false` if needed. Then
delete the `live-*` files.

## Step 4: ICP, use case + competitors

From the page intel and the snapshot text, write the **use case** in one sentence: what problem
it solves, for whom, and the category a buyer would search for. Infer the ICP now if needed.

Research competitors with 2–3 parallel WebSearch calls (category + "alternatives", "vs",
"best {category} tools for {ICP}"). Roundups go stale, since startups pivot, shut down and get
acquired, so **verify every candidate**: WebFetch its current homepage and confirm the hero
still sells the same use case to the same ICP. Propose the 4 strongest verified **direct**
competitors, each with the page a buyer would land on (usually the homepage).

Confirm in **one** AskUserQuestion call with two questions (three if the ICP was inferred:
"Is this the ICP?" first):
- "Is this the use case?" with your sentence as option 1 and a close alternative as option 2.
- "Which competitors should be in the lineup?" (multiSelect), up to 4 candidates, each labeled
  with name and a one-line description that includes its URL.

Require 2–4 competitors. More than 4 makes each judge's job too long to do well.

## Step 5: Brief

Write `{run}/brief.json`:

```json
{
  "icp": "…", "icpSource": "user | inferred",
  "target": { "name": "Acme", "url": "https://acme.example" },
  "capturedVariant": { "h1": "…", "cta": "…" },
  "useCase": "…",
  "judgeUseCase": "a tool to … (the buyer's problem, no product or company names)",
  "competitors": [ { "id": "rivalone", "name": "RivalOne", "url": "https://rivalone.example", "why": "…" } ],
  "reserves": [ { "id": "…", "name": "…", "url": "…", "why": "…" } ],
  "judges": [ { "id": "j1", "role": "Buyer", "title": "…", "persona": "…" } ],
  "stopRule": { "minFirstVotes": 4, "leadAllDims": true, "tolerance": 0.5, "confirmRounds": 1,
                "maxRounds": 5, "plateauRounds": 2, "inputRounds": 2 },
  "slop": { "enabled": true, "floor": 5, "maxDrop": 2 },
  "models": { "judges": "haiku", "designer": "sonnet", "slop": "sonnet" },
  "timeouts": { "judges": 5, "designer": 12 },
  "screenshotMethod": "headless"
}
```

- **`judgeUseCase`** is what judges are told they're shopping for. `new_round.py` refuses to
  run if it names the client.
- **Models:** you steer; sub-agents are pinned for cost and speed. Always pass `model`
  explicitly from `brief.models`, and never let sub-agents inherit an expensive parent model.
  For sharper critique, set judges to `sonnet`.
- **Timeouts** (minutes) cap how long you wait for sub-agents before stopping and re-spawning
  them. In test runs a whole judging round took about 1.5 minutes (4 at most) and a design pass
  2–5 minutes, while stalled agents ran past 30. Raise them if your judges or designer run on
  slower models.
- **Slop judge** (on by default): a non-voting judge that scores how generic and
  template-like each page is, and blocks a version that's more generic than the original from
  winning. See **`references/slop-judge.md`**.
- Build the five judges (2 Buyer, 2 Influencer, 1 Decision maker) from the ICP following
  **`references/judges.md`**. Show the user their one-line titles and continue; this isn't a
  gate. Competitor `id`s are lowercase slugs used as file names.

## Step 6: Screenshot the field

One command shoots every competitor, three at a time, at desktop (1440px layout, up to 3 tiles
of 1800px, saved at 0.75 scale) and mobile (390px, up to 2 tiles of 1600px):

```bash
node {skill}/scripts/shoot.mjs --out {run}/shots/competitors rivalone=https://rivalone.example rivaltwo=https://rivaltwo.example …
```

`v0` was already shot in Step 3. shoot.mjs dismisses consent banners (twice, including
inside shadow roots), hides chat widgets, slide-ins and popups on every page (`--keep-popups`
turns that off), unlocks pages that scroll inside a container, and prints warnings. For
every page, act on the rendering warnings (widow warnings matter only for redesigned versions
of the client's page, v1 and later), and have one Haiku agent look at every page's
`-desktop-01.png` and answer two questions per page in one line each:
1. **Rendering:** no captcha, blank page, single-viewport capture, or overlay covering the
   hero. A consent banner or popup that survived must be gone before judging: dismiss it and
   re-shoot.
2. **Positioning:** the hero still sells the same use case to the same ICP. If not, swap in a
   reserve (see **`references/advanced.md`**).

If a competitor bot-walls headless Chrome, swap in a verified reserve; when running straight
through, always do that. Only if the target itself, or every candidate, is walled, switch the
whole run to in-browser screenshots (see **`references/advanced.md`**). Competitor screenshots are taken **once** and reused every
round. Only the target changes.

## Step 7: The round loop

Track the **current target version** `vN`, starting at `v0`. Each round judges the current
version.

**7a. Set up the blind round**
```bash
python3 {skill}/scripts/new_round.py {run} R vN
```
This shuffles pages, assigns letters, copies the screenshots and renders every judge's prompt
into a **neutral temp folder** (random name, no trace of the client), writes the secret
`mapping.json`, and prints a one-line `spawn` instruction per judge.

**7b. Judge.** Spawn all five judges **in parallel in a single message** as fresh
`general-purpose` background agents (never `fork`) with `model: brief.models.judges`, each
with its `spawn` line as the entire prompt. In the same message, spawn the slop judge with its
`spawn` line and `model: brief.models.slop` — only if there is one: confirmation rounds
re-judge an unchanged page, so they reuse the earlier slop result. Add nothing else. Then wait
for them with a time limit (`brief.timeouts.judges`), using a Bash timeout of 10 minutes:

```bash
python3 {skill}/scripts/wait.py {run} judges R
```

| exit | status | next |
|---|---|---|
| 0 | `done` | 7c |
| 3 | `invalid` | delete those judges' files, re-spawn only them with their `spawn` line plus the errors, then `wait.py … --extend 5` |
| 4 | `timeout` | stop the judges in `missing` (TaskStop) and re-spawn each once with its `spawn` line, then `wait.py … --extend 5` |
| 5 | `waiting` | run it again: the clock keeps going |

If the same judge fails a second time, re-spawn it on `sonnet`. Haiku sometimes writes broken
JSON over and over. If a spawn fails with "concurrent subagent limit", other runs are using the
slots: spawn the rest one at a time as earlier ones finish. Running more than three reviews at
once makes this likely.

**7c. Tally**
```bash
python3 {skill}/scripts/tally.py {run} R
```
It requires exactly one valid file per judge (exit code 3 lists any that aren't, as above).

Give the user a one-line status:
> Round 2 · v1 · 3/5 first-place votes · leads clarity, offer · behind on value (6.2 vs 7.0)

**7d. Act on the verdict.** A round **passes** when at least 4 of 5 judges rank the target #1,
the target's mean on each of the four dimensions is no more than `tolerance` (0.5) behind the
best competitor's, and the slop gate holds (`tally.slop.gatePassed`). Judge means drift about a
point between rounds, so a smaller gap is noise; set `tolerance: 0` to require a strict lead. Judges score relative to the lineup,
so one pass can be noise; the tally's `verdict` handles that. (If the original page itself
scores below the slop floor, it can't pass unchanged: the redesign has to make it more specific.)

| verdict | meaning | next |
|---|---|---|
| `winner` | passed, and the same version passed the previous `confirmRounds` round(s) | Step 8 |
| `confirm` | passed, not yet confirmed | **no redesign**: re-judge the same `vN` next round |
| `continue` | didn't pass (buyers, slop gate, or both) | 7e |
| `reshoot` | 2+ judges reported the same overlay covering a page (`tally.overlays`) | re-shoot that page with shoot.mjs, which hides popups (in an in-browser run, dismiss it by hand in your tab), `touch {run}/rounds/rR.reshot`, delete `{run}/rounds/rR`, and redo round R. At most once per round: after that the scores stand |
| `needs-input` | won the vote but trailed only on offer and/or value for `inputRounds` rounds in a row, and the page has a `TODO.md` | Step 8: the gap needs facts only the founder has (pricing, a trial, customers), not more design |
| `plateau` | the last `plateauRounds` rounds didn't beat the best earlier score (a failed confirmation round doesn't count: redesign) | Step 8 |
| `round-cap` | `maxRounds` reached without a confirmed win | Step 8 |

**7e. Redesign.** Spawn **one** design agent (`general-purpose`,
`model: brief.models.designer`) with the prompt template in **`references/designer.md`**. Give
it the ICP, use case and competitors inline. Don't point it at `brief.json`, which holds the
full judge personas. It writes `site/v{N+1}/` (`index.html`, `CHANGELOG.md`, maybe `TODO.md`),
self-checks its work, and writes an empty `site/v{N+1}/.done` last. Wait for it with a time
limit (`brief.timeouts.designer`):

```bash
python3 {skill}/scripts/wait.py {run} designer v{N+1}
```

On exit 5 (`waiting`), run it again. On exit 4 (`timeout`), send the design agent one nudge
(SendMessage: "Time's up: finish the edit you're on, write CHANGELOG.md, then .done") and wait
with `--extend 5`. If it still hasn't finished, stop it. Keep `site/v{N+1}/index.html` if it
exists and add a line to its `CHANGELOG.md` saying the pass was cut short. Otherwise re-spawn
the design agent once and wait with `--extend 12`.

When it returns, **always re-shoot the new version yourself**, because designers sometimes
edit after their last self-check:

```bash
node {skill}/scripts/shoot.mjs --out {run}/shots/target v{N+1}=http://127.0.0.1:{port}/site/v{N+1}/index.html
```

Check its warnings (don't Read the tiles yourself). If shoot.mjs warns about one-word last
lines in headings, send the page back to the design agent to fix, once; then move on. Then make `v{N+1}` current
and start the next round. If the target's average score drops versus the previous version,
tell the next design agent and include the previous round's `feedback.md` too.

## Step 8: Report

```bash
python3 {skill}/scripts/report.py {run}
```

Open `{run}/report.html` for the user (`open` on macOS) unless running straight through. Stop
the background `http.server`. Then summarize:
- The verdict and final standings (first-place votes, the four dimension scores vs. the best
  competitor), and how many rounds confirmed it
- The slop check: original vs. final score, and whether the gate ever blocked a version
- How much competitor scores drifted across rounds (the report's range column). Gaps smaller
  than that are noise
- The 3–5 changes that moved the scores most, from the CHANGELOGs
- **Needs your input:** every `TODO.md` item (lead with it on a `needs-input` verdict). These are placeholders for proof (quotes, logos,
  metrics, pricing) the design agent was not allowed to invent
- Anything the design agent took from an A/B variant other than `capturedVariant`
- Where the winning page is: `{run}/site/v{final}/index.html`. At the round cap, point to the
  best-scoring version the report names
- A reminder that these are AI personas. Validate the winner with a handful of real ICP
  buyers before shipping.

To resume a finished run later, see **`references/advanced.md`**.

---

## Rules

- **Blind means blind.** Judges only ever get their `spawn` line, which points to a neutral
  folder: no client name, no run folder. Fresh judge agents every round.
- **No invented proof.** The design agent may not fabricate customers, metrics, logos,
  testimonials or pricing (see `references/designer.md`). Gaps become HTML comments plus
  `TODO.md` entries, never visible placeholders or empty proof shells.
- **Don't game the judges.** Never feed judges the previous round's feedback or tell them the
  page changed. The design agent sees judge roles, never personas, and slop findings, never
  slop scores.
- **Same conditions for every page.** Same viewport sizes, tile sizes and capture method for
  every page in the run.
- Keep the user posted with one line per phase. Don't dump judge JSON into the chat.
