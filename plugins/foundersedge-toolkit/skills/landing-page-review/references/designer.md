# The Design Agent

One sub-agent per iteration, spawned with `model: brief.models.designer` (default `sonnet`). It takes the latest version of the client's page plus the round's
de-anonymized judge feedback, and produces the next version. It is **not** blind: it knows
which page is the client's and who the competitors are.

## Mandate

- **Free redesign.** Layout, hierarchy, copy, typography, color and section order can all
  change if that's what wins. Rebuilding the page from scratch is allowed when the original
  structure is the problem.
- **Fix what the judges said, in priority order:**
  1. Dimensions where the page doesn't lead (`feedback.md` table, marked **no**)
  2. Confusions raised by 2+ judges
  3. Concerns raised by the decision maker (`j5`)
  4. Everything else
- **Fix the page, not the panel.** Answer the concerns judges raised as a real buyer would
  want them answered. Write for the ICP you were given, not for the judges as individuals
  (`feedback.md` shows only their roles, on purpose).
- **Be specific, not median.** You're an LLM, and LLM pages drift toward one look:
  purple-to-blue gradients, a centered hero over rows of identical icon cards, glow blobs,
  and "seamless / unlock / elevate / empower" copy that would fit any company. A separate
  slop review checks for this, and a version that reads more generic than the original
  **cannot win**, however the buyers score it. Don't work from a ban list (avoiding one tell
  just produces the next). Work from positive direction instead:
  - **Copy:** every claim should fail the swap test (it shouldn't stay true with a
    competitor's name in it). Use concrete nouns, the real workflow, real numbers from the
    source, and how the product actually works.
  - **Visual:** keep and sharpen the client's own brand (logo, signature color, signature
    graphic) and pick one clear art direction. **Keep the client's typefaces** (they're already
    in `site/assets/fonts/`) in the roles v0 gives them: don't promote a font the original only
    uses in small places to the headline. Change type only when judges criticize it. Never
    reach for the "AI editorial" kit: a serif display headline with an italic accent phrase
    in the brand color, monospace eyebrow labels on every section, 01 / 02 / 03 numbered
    cards. The slop review penalizes it as hard as purple gradients. Show the real product (actual UI, real
    output) wherever the source has it.
  - **Proof:** use the source's real proof as it stands. Gaps become TODOs (see below).
  - If `feedback.md` has a "slop review" section, treat its "Fix first" as high priority and
    build on what it says is most specific.
- **Learn from the winners.** `feedback.md` lists what judges liked about pages ranked above
  the client. Borrow the *pattern* (e.g. "pricing visible above the fold", "one-line what-it-is
  under the logo"), never the copy or the visuals.
- **Typography: no widows.** Set `text-wrap: balance` on headings, card titles and CTA lines,
  and `text-wrap: pretty` on paragraphs. Bind the last two words with `&nbsp;` where a heading
  still ends on a lone word ("…govern production / AI."). shoot.mjs warns about every heading
  whose last line is a single word; fix every one before you finish.
- **Design for visitors, not the screenshot.** Screenshots stop at a fixed length, but never
  trim spacing, hide sections on mobile, or reorder content just to fit more into the capture.
  The page should read well at its natural length.
- **Desktop and mobile both count.** Every change must hold up at 1440px and 390px. Use real
  responsive CSS (media queries, fluid layout), not a desktop page that merely shrinks.

## Hard rule: no invented claims

The page may only state facts that appear in the original page, `brief.json`, or something
the user told you. Do **not** invent:

- customer names, logos, testimonials or quotes
- metrics ("10x faster", "2,000 teams", "$3M saved"), ratings or review counts
- certifications, awards, press mentions, integrations or partners
- pricing or plan details that aren't in the source

When a judge's concern can only be fixed with proof the client hasn't provided (e.g. "no
social proof"), do **not** fake it, and don't put a visible `[TODO]` on the page either.
Judges would read it as an unfinished draft, which would tank professionalism and give away
which page is being worked on. Instead:

- Strengthen what *is* provable (sharper claims from the source, a clearer "how it works",
  a visible pricing or demo path).
- **Don't build empty shells for proof you don't have:** no scorecard, dashboard, stat card or
  metric tile with placeholder or no numbers ("Baseline before optimization", "—%"). They read as
  fake proof. Fill them with real facts from the source, or leave the element out.
- Write the missing slot as an HTML comment where it belongs, e.g.
  `<!-- TODO: customer quote — name, title, company (answers j5: "no proof anyone uses this") -->`.
- Add a line to `TODO.md`. The final report surfaces `TODO.md` as "Needs your input".

Rephrasing, tightening or reordering existing claims is fine. So is making a vague claim
specific *only* when the specifics already exist somewhere in the source material.

## Inputs (paths passed in the prompt)

- `site/v{N}/index.html`: the current version (v0 is the captured original)
- `rounds/r{R}/feedback.md`: de-anonymized judge feedback and scores vs. the best competitor
- `rounds/r{R}/pages/` + `mapping.json`: the screenshots judges saw, for looking at how the
  competitors handled what the client got dinged on
- ICP, use case and competitors, given inline in the prompt. Don't read `brief.json`: it
  holds the judges' full personas, and writing to those is gaming the panel.
- The previous round's `feedback.md` when scores dropped (the orchestrator includes it)
- `site/v{N}/TODO.md` if it exists (carry unresolved items forward)

## Outputs (write all into `site/v{N+1}/`)

| File | Contents |
|------|----------|
| `index.html` | The new page. Web fonts live in `{run}/site/assets/fonts/`, so keep their URLs pointing to `../assets/fonts/…` (as v0 does) rather than embedding them. Inline CSS in `<style>` is preferred so the file is self-contained. Remote images and fonts from the original may stay as absolute URLs. Keep JS minimal and only for real interactivity (menus, tabs). No frameworks, no build step. |
| `CHANGELOG.md` | One bullet per change: **what changed → which judge concern it answers** (quote or cite `j#`). |
| `TODO.md` | Every placeholder the user has to fill, with the judge concern that motivated it. Omit the file if there are none. |

## Self-check before finishing

The design agent screenshots its own work and looks at it before handing back:

```bash
node {skill}/scripts/shoot.mjs --out {run}/shots/target \
  v{N+1}=http://127.0.0.1:{port}/site/v{N+1}/index.html
```

Always self-check with shoot.mjs, even in an in-browser run. The orchestrator re-shoots your
final version before judging, so make every edit **before** your last self-check. Then Read
`v{N+1}-desktop-01.png` and `v{N+1}-mobile-01.png` and check:
- Nothing overlaps, overflows or gets cut off at 390px, and there's no horizontal scroll
- No broken images or unstyled sections
- The hero answers *what is it, who is it for, what do I do next* without scrolling
- No visible placeholder text such as "[TODO", "Lorem" or "Customer name", and no empty proof
  shells
- shoot.mjs printed no "one-word last line" warning for your page

Fix anything broken and re-shoot. Those screenshots are the ones the next judging round uses.

When everything is written, create an empty `site/v{N+1}/.done` as your very last step. The
orchestrator waits on that file and stops design passes that run past the time limit, so
don't polish forever: fix what the judges raised, self-check, and finish.

## Prompt template

```
You are a senior conversion-focused web designer. Produce v{N+1} of a client's landing page.

ICP: {icp}
What the page sells: {use case}
Competitors in the judging round: {names + urls}

Read references/designer.md at {skill}/references/designer.md and follow it exactly,
especially the no-invented-claims rule.

Inputs:  {run}/site/v{N}/index.html, {run}/rounds/r{R}/feedback.md,
         {run}/site/v{N}/TODO.md (if it exists),
         {if scores dropped: {run}/rounds/r{R-1}/feedback.md — "scores fell vs. the previous
          version; decide whether to revert specific changes"}
         judge screenshots in {run}/rounds/r{R}/pages/ (letter → page in mapping.json)
Outputs: {run}/site/v{N+1}/index.html, CHANGELOG.md, TODO.md (if needed)
Preview: the run folder is served at http://localhost:{port}/

Self-check with shoot.mjs as described, fix issues, write {run}/site/v{N+1}/.done, then reply with a 5-line summary of the
biggest changes.
```
