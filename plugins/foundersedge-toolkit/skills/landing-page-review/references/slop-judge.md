# The Slop Judge

One extra judge per round that scores how **generic, low-effort and AI-template-like** each
page looks. It is not a buyer and gets no vote in the ranking. It acts as a **gate**: a
version can't win if the design agent made it sloppier.

Why it exists: the design agent is itself an LLM, and LLMs drift toward the median page
(purple-to-blue gradient, centered hero, three identical icon cards, "seamless / unlock /
elevate" copy). The newer drift is the "AI editorial" kit: a serif display headline with an
italic accent phrase, monospace eyebrow labels and numbered cards. It looks crafted at a
glance, which is why it's easy to miss. In testing, a design agent swapped a sans-serif
hero for exactly this, and the slop judge still scored its visuals 8. Buyer personas tend to reward that kind of fluent, polished generic copy, so
they won't catch the drift. Readers' trust drops on content that feels generic and
inauthentic. The harm is genericness, not AI origin, so the judge scores **specificity and
effort**, never "was this written by AI".

Enable it in `brief.json`:

```json
"slop": { "enabled": true, "floor": 5, "maxDrop": 2 },
"models": { "judges": "haiku", "designer": "sonnet", "slop": "sonnet" }
```

Gate (applied by `tally.py`): the target's slop score (mean of the three dimensions) must be
**≥ `floor`** and **≥ the original page's (v0's) score minus `maxDrop`**. A round only passes if
the buyer panel passes it *and* the gate holds. The judge scores every page in the lineup
(blind, same letters as the buyers), so competitors give a sense of the category's baseline.

## Rubric (1–10, higher = less slop)

| Dimension | 1 | 5 | 10 |
|-----------|---|---|----|
| **copy** | The swap test passes: put a competitor's name in and every line still reads true. Stacked buzzwords (seamless, unlock, elevate, empower, revolutionize, supercharge, next-generation), "not X, it's Y" pivots, triads everywhere, empty intensifiers. | The category is clear but claims are generic. | Concrete nouns, named users and workflows, real numbers, mechanisms ("how it works"), a distinct voice. |
| **visual** | One of the two default looks. The old one: purple/blue gradient (often on headline text), centered hero, then rows of identical rounded icon cards, glow blobs or glassmorphism, emoji used as icons. The newer "AI editorial" one: a condensed or high-contrast serif display headline with one phrase set in italic and the accent color ("…your AI needs. *Simply by asking.*"), small uppercase monospace labels over every section, and 01 / 02 / 03 numbered cards. | A clean template with one or two deliberate choices (palette, type pairing, layout). | Clear art direction that couldn't be mistaken for the default and fits the brand. |
| **proof** | Invented-looking stat cards, a fake dashboard with round meaningless numbers, faceless testimonials ("Sarah K., CEO"), stock or abstract imagery in place of the product. | Real product UI but unsourced claims. | Named customers, sourced numbers, the real product doing a real task, specific results. |

## False-positive guard (include verbatim in the prompt)

Plain, clear, short writing is **not** slop. A single em dash, a standard CTA like "Start free
trial", the Inter font, or a three-column feature row is not slop on its own. Penalize clusters
of tells, or a failure of specificity. **Specificity is the antidote:** a page full of concrete,
checkable detail scores high even with a common layout.

A company's own brand (logo, a consistent signature color, a recurring brand graphic) is a
deliberate choice, not a tell. Judge how it's used, not that it exists. Every deduction must
cite something visible on the page.

## Prompt template

`scripts/new_round.py` renders this into the neutral judge folder (`prompt-slop.md`, archived
to `rounds/rN/prompts/slop.md`) when `brief.slop.enabled` is true, with a `spawn` line like the
buyer judges'. Spawn it in the same parallel message: a fresh `general-purpose` agent with
`model: brief.models.slop` (default `sonnet`) and its `spawn` line as the entire prompt.

<!-- slop-prompt-template:start -->
```text
You are a senior brand designer and conversion copywriter reviewing landing pages for
"slop": generic, low-effort, template-default content that could belong to any company.
You are not a buyer and you are not ranking the pages. You are scoring how specific and
deliberate each page is.

There are {{n}} pages, labelled only by letter. For each you get desktop screenshots (1440px
wide, top to bottom) and mobile screenshots (390px wide). Use the Read tool to view EVERY image
listed below. Use only Read (for these images) and Write (for your answer). Don't browse the
web, search, run commands or list directories. Pages marked "continues below" were cut off at
a fixed length, so judge only what's shown.

{{pages}}

Score each page 1–10 on three dimensions (higher = less slop):

{{rubric}}

Rules:
- Plain, clear, short writing is NOT slop. A single em dash, a standard CTA like "Start free
  trial", the Inter font, or a three-column feature row is not slop on its own. Penalize
  clusters of tells, or a failure of specificity. Specificity is the antidote: a page full of
  concrete, checkable detail scores high even with a common layout.
- A company's own brand (logo, a consistent signature color, a recurring brand graphic) is a
  deliberate choice, not a tell. Judge how it's used, not that it exists.
- Watch for the "AI editorial" look as closely as the purple-gradient one: a serif display
  headline with one phrase in italic and the accent color, uppercase monospace labels over
  every section, and 01 / 02 / 03 numbered cards. Two or more of these together cap visual at
  5 unless the rest of the page shows clear, specific art direction. Name the elements you saw.
- Use the swap test for copy: would this line still be true with a competitor's name in it?
- Every score below 8 needs evidence: quote the exact words or describe the exact element
  and where it is (e.g. "desktop-02, feature grid").
- Don't guess whether AI made the page. Score specificity and effort only.

Write ONLY valid JSON to {{out_file}}, matching this exact shape (one entry per letter):
{{schema}}
Then reply with just the word "done".
```
<!-- slop-prompt-template:end -->

## Output schema

```json
{
  "pages": {
    "A": {
      "copy": 6, "visual": 4, "proof": 5,
      "evidence": [
        "copy: hero 'Unlock seamless workflows' passes the swap test",
        "visual: desktop-01 purple-to-blue gradient on headline + three identical icon cards (desktop-02)"
      ],
      "most_specific": "The single most concrete, non-generic thing on this page.",
      "fix_first": "The one change that would most reduce slop on this page, stated as positive direction (what to show), not just what to remove."
    }
  }
}
```

`tally.py` validates it the same way as buyer files. If the slop judge's file is missing or
invalid, the round is invalid (exit 3): re-spawn just the slop judge.

## Calibration

Before trusting the gate on a new kind of site, sanity-check the judge: an obviously
handcrafted page with real proof should land at 7 or above, and a template page full of
buzzwords at 4 or below. If it doesn't, tighten the evidence requirement rather than adding
more banned words. A ban list just pushes the design agent to the next most likely tell.
