# The Judge Panel

Five blind judges, each a sub-agent with one persona drawn from the user's ICP. Fresh agents
every round: a judge must never remember a previous round or see which page is the client's.

## Panel composition (fixed: 2 buyers, 2 influencers, 1 decision maker)

Build all five from the ICP the user gave in Step 1. Make them **specific and different from
each other**. Vary the company size, seniority, skepticism and what each one is trying to get
done. Five copies of the same person is one judge counted five times.

| ID | Role | Who they are | What they scan for |
|----|------|--------------|--------------------|
| `j1` | **Buyer** | The hands-on user who feels the pain daily and would actually use the product | "Does this solve *my* problem? Can I try it today? Is it obvious what it does?" |
| `j2` | **Buyer** | A second buyer from a different company size or sub-segment, more skeptical | Proof it works for someone like them, pricing signals, effort to get started |
| `j3` | **Influencer** | Technical or functional evaluator the decision maker asks to vet tools (e.g. staff engineer, ops lead, security, RevOps) | Credibility, integrations, how it works, red flags, "is this real or vaporware?" |
| `j4` | **Influencer** | Adjacent stakeholder who has to live with the choice (e.g. finance partner, team lead, procurement) | Risk, switching cost, clarity of pricing/terms, who else uses it |
| `j5` | **Decision maker** | Holds the budget and signs (VP / Head of / founder, depending on the ICP) | Business outcome, ROI in one glance, trust, "why this vendor over the others?" |

Write each persona into `brief.json` → `judges[]`:

```json
{ "id": "j3", "role": "Influencer", "title": "Staff platform engineer, 400-person fintech",
  "persona": "Asked by their VP to shortlist tools. Has been burned by tools that demo well and break in prod. Skims for architecture, integrations and anything that smells like hand-waving. Has ~90 seconds per page." }
```

The `persona` is 2–4 sentences of first-person context: the job to be done, what they've been
burned by, and how much time they give a page. Don't name or hint at any of the pages.

## Rubric (each page, each judge)

Score 1–10 on each dimension. Use the full range. A 5 is mediocre, not "fine".

| Dimension | Question the judge answers |
|-----------|----------------------------|
| **clarity** | Within ~5 seconds of the hero, do I know what this is, who it's for and what it does? Is the hierarchy easy to scan? |
| **offer** | Is it clear what I get and what I should do next (trial, demo, pricing, signup)? Is the CTA compelling and low-friction? |
| **value** | Is the payoff for *someone like me* concrete and credible (outcomes, proof, specifics vs. generic claims)? |
| **professionalism** | Does it look trustworthy and well made: visual polish, consistency, no broken or awkward bits, on mobile too? |

**Overall** is the judge's forced ranking of all pages, best first, with no ties. It's a gut
call ("which one would I click through on?"), not the average of the four scores.

## Judge prompt template

You don't fill this in by hand. `scripts/new_round.py` renders it for every judge into the
round's neutral judge folder (`prompt-<judge id>.md`, archived to `rounds/rN/prompts/`),
substituting `{{…}}` from `brief.json`, the rubric table and the output schema in this file,
and the round's neutral image paths. It flags pages whose screenshots stop before the page
ends, and prints a one-line `spawn` instruction per judge ("Read <path> and follow its
instructions exactly.").

Spawn the five judges **in parallel, in one message**, as fresh `general-purpose` agents with
`model` set to `brief.models.judges` (default `haiku`), each with its `spawn` line as the
entire prompt. Never use `fork`, which would inherit the whole conversation, client name
included.

<!-- judge-prompt-template:start -->
```text
You are {{title}} ({{role}}). {{persona}}

You're shopping for: {{judge_use_case}}

There are {{n}} vendor pages, labelled only by letter. For each page you get desktop
screenshots (1440px wide, read top to bottom in order) and mobile screenshots (390px wide,
same). Use only Read (for these images) and Write (for your answer). Don't browse the web,
search, run commands or list directories: judge only what's on these pages, the way a buyer
would.

Work ONE PAGE AT A TIME, in letter order: view every image for Page A, then write down your
notes and scores for Page A, before you open any image of Page B. Then Page B, and so on.
Never go back and forth between pages while scoring, and check that every note you file under
a letter describes the images whose file names start with that letter. Rank only after all
pages are scored.

Screenshots stop at a fixed length. When a page is marked "continues below", content such as
pricing or a footer may exist further down. Don't penalize a page for something missing
below the cut; judge what a visitor sees in the part shown.

{{pages}}

Judge them as yourself, a real {{role}} with limited time, not as a designer. Score each page
1–10 on clarity, offer, value and professionalism (definitions below), note anything that
confused you or made you hesitate, then force-rank all pages (no ties).

Set a page's "overlay" to true only if a cookie/consent banner, popup or modal hides its
headline, hero or a main section in any screenshot, and describe it in "overlay_note". A small
floating chat button or launcher that real visitors also see is NOT an overlay: mention it in
"concerns" if it bothers you. Either way, score what you can see.

{{rubric}}

Use the full range: 5 is mediocre, not "fine". Overall is your forced ranking, best first:
a gut call on which one you'd click through on, not the average of your scores.

Refer to pages only as "Page A", "Page B", etc. Be blunt and specific. "Hero says
'AI-powered platform' but never says what it does" is useful; "could be clearer" is not.

Write ONLY valid JSON to {{out_file}}, matching this exact shape (one entry in "pages" per
letter):
{{schema}}
Then reply with just the word "done".
```
<!-- judge-prompt-template:end -->

## Output schema (`<outDir>/<judge id>.json`, archived to `rounds/rN/judges/`)

```json
{
  "judge": "j3",
  "pages": {
    "A": {
      "clarity": 7, "offer": 5, "value": 6, "professionalism": 8,
      "first_impression": "One sentence: what I think this is after 5 seconds.",
      "strengths": "What works best on this page.",
      "confusions": ["Specific thing I didn't understand, and where on the page."],
      "concerns": ["Specific thing that made me trust it less or hesitate to act."],
      "next_action": "What I'd actually do next: book demo / start trial / check pricing / leave.",
      "overlay": false,
      "overlay_note": ""
    }
  },
  "ranking": ["C", "A", "B"],
  "rationale": "2–3 sentences: why my #1 beat my #2, and what would change my mind."
}
```

If any judge sets `"overlay": true`, `tally.py` reports it as `overlays` (and marks the round
verdict `reshoot` when 2+ judges flag the same page): follow SKILL.md 7d (re-shoot, mark the
round, delete it, redo it). It happens at most once per round.

`scripts/tally.py` needs exactly one valid file per judge in `brief.json` (`j1`–`j5`). It
rejects missing files and files that don't match this shape (all letters present, scores
1–10, ranking a permutation of the letters). If it exits 3, re-spawn **only** the judges it
names, with the same prompt plus the validation errors.

## Blinding rules

- Judges see only the neutral temp folder from `new_round.py`. Never pass `mapping.json`,
  any path inside the run folder (its name contains the client's slug), the client's name or
  the competitor list.
- Brand names and logos stay visible in the screenshots. That's realistic, since buyers
  recognize brands. What the judges don't know is **which page is the client's**, or that
  any page is being iterated on.
- New letters and a new shuffle every round (`new_round.py` does this), and new judge agents
  every round, with the same personas.
- `brief.judgeUseCase` is what judges are told they're shopping for. Phrase it as the buyer's
  problem, with no product or company names, e.g. "a platform to ship accurate, compliant AI
  features in a regulated company". `new_round.py` refuses to render if it names the client.
