---
name: deck-review
description: >
  Check a startup pitch deck for the essentials and signals an early-stage investor looks for,
  before the founder sends it out. Use this skill whenever someone asks to review their deck,
  check if their pitch deck is ready, find what's missing from their deck, or asks whether their
  company is "investable" or "venture scale." Triggers on: "review my deck", "is my pitch deck
  ready", "check my pitch deck", "what's missing from my deck", "is my company investable",
  "are we venture scale", "would an investor fund this".

  This is a founder-facing essentials-and-investability check, tuned for US-based venture
  investment. It does NOT score against a proprietary rubric — it confirms the deck contains the
  information investors need, flags common gaps, and runs two hard investability gates:
  (1) is the company an investable US C-corp, and (2) is the business plausibly venture scale.

  Always use this skill for deck reviews — do not freelance a critique from memory.
---

# Deck Review — Founder Essentials & Investability

Confirms a pitch deck contains the information an early-stage US investor needs to say yes (or to
take a meeting), flags the gaps that most often sink a raise, and runs two hard gates: **is this an
investable entity** and **is this venture scale**. Produces a written "Deck Review — [Company]"
summary with a clear readiness verdict.

> **Founders:** every gap this surfaces is a question an investor will ask in the first meeting.
> Better to fix it in the deck than fumble it live. This is tuned for **US-based venture
> investment** — if you're raising elsewhere or on a non-venture path, some checks won't apply.

---

## Workflow

```
1. IDENTIFY     → Company, deck file/link, stage, who's reviewing (usually the founder)
2. READ         → Read the full deck; map slides to the essentials checklist
3. ESSENTIALS   → Mark each essential ✅ present / 🔴 missing / 🟠 present-but-weak
4. GATE 1       → Investable entity? (US C-corp vs LLC / foreign / other)
5. GATE 2       → Venture scale? (comps that hit >$100M revenue or $1B+ valuation)
6. COMMON GAPS  → Check the frequent-killer list (no ask, no traction, vague market, etc.)
7. WRITE        → Produce the "Deck Review — [Company]" summary + readiness verdict
8. SUMMARIZE    → Top fixes before sending, and any gate failures
```

---

## Step 1: Identify

Ask if not given:
- Company name
- The deck (a file path, PDF, or link) — read the actual deck, don't review from a description
- Stage (pre-seed / seed) and how much they're raising, if stated
- Geography of incorporation and where the team is based (needed for Gate 1)

---

## Step 2 & 3: Essentials checklist

Read every slide. Mark each item ✅ present / 🔴 missing / 🟠 present-but-weak, each with a
one-line pointer to the slide (or "not in deck").

**Can an investor reach you and know who you are?**

- [ ] **Contact information** — a real email (and ideally name + role) on the deck. A deck with no
  way to reply is a surprisingly common miss.
- [ ] **Clear founder information** — full names, roles, and a one-line credibility marker per
  founder (prior company, domain expertise, relevant build/sales experience). A logo wall of past
  employers is not enough — say *what they did*.
- [ ] **Why this team** — an explicit answer to "why are *you* the people to win this?" Founder-
  market fit. If it's implied but never stated, mark 🟠.

**Is the opportunity articulated?**

- [ ] **Problem well articulated** — a specific, painful, real problem stated plainly (not buried
  in jargon or solution-speak). An investor should understand who hurts and how much within one
  slide.
- [ ] **Solution is clear** — what the product actually does, ideally in one sentence a non-expert
  gets. Flag 🟠 if it's all adjectives ("AI-powered, next-gen platform") and no concrete "it does X."
- [ ] **Why now** — what changed (tech, regulation, behavior) that makes this the moment. Optional
  at pre-seed but a strong signal when present.
- [ ] **Market** — who the customer is and a credible sense of size. (For a full TAM/SAM/SOM, that's
  a separate exercise; here just confirm the deck isn't hand-waving "it's a $T market.")
- [ ] **Traction or evidence** — whatever proof exists: revenue, users, pilots, LOIs, waitlist,
  or strong product progress. At pre-seed, conviction + early signal; missing entirely is 🟠/🔴.
- [ ] **The ask** — how much they're raising and, ideally, use of funds. A deck with no ask makes
  the investor guess. Missing = 🔴.

**Solo-founder test (apply only if there is exactly one founder):**

A solo founder is investable, but the deck must answer the three doubts every investor has. Mark
🟠 (or 🔴 if entirely absent) when the deck doesn't make these clear:

- [ ] **Can they BUILD it?** — technical capability on the team or a credible plan to get it (first
  hire, technical advisor, or the founder's own track record shipping product).
- [ ] **Can they FUNDRAISE & SELL?** — evidence the founder can get in rooms and close — prior
  raises, sales background, design-partner logos, or visible momentum.
- [ ] **Can they SCALE / hire a team?** — a sense they can recruit and lead, not do everything
  alone forever. Early advisors or a hiring plan help.

---

## Step 4: Gate 1 — Is this an investable entity?

This is a hard gate for US venture money. Determine the entity from the deck/founder:

| Situation | Verdict |
|---|---|
| **Delaware C-corp** | ✅ Standard investable structure. |
| **C-corp in another US state** | 🟠 Investable, but most institutional investors expect/convert to a Delaware C-corp. Note it. |
| **LLC** | 🔴 Not directly venture-investable. Priced equity rounds and SAFEs assume a C-corp; QSBS doesn't apply to LLCs. Flag that they'll need to convert to a (Delaware) C-corp before/at the round. |
| **Foreign entity / no US entity** | 🔴 Note that US institutional investors typically require a US (Delaware) C-corp or a flip structure. |
| **Not stated** | 🟠 Ask the founder — this must be known before terms. |

If the deck implies the company isn't yet incorporated as a C-corp, that's the **single most
important fix** — surface it at the top of the verdict.

---

## Step 5: Gate 2 — Is this venture scale?

Venture investors need outcomes that can return a fund — businesses that can plausibly reach
**$100M+ in revenue** or a **$1B+ valuation**. A great business is not automatically a venture
business. Assess honestly:

1. **Comps test** — name 1–3 companies in or adjacent to this space that have **crossed ~$100M in
   revenue or reached a $1B+ valuation/outcome**. If such comps exist, the market has demonstrated
   venture-scale ceilings → ✅. If you genuinely can't name any, that's a 🔴/🟠 worth stating
   plainly — the market may be real but not venture scale (a good small-business or
   lifestyle-business space).
2. **Math sanity** — does a believable path to ~$100M revenue exist (price × reachable customers)?
   If hitting $100M would require an implausible share of a tiny market, flag it.
3. **Margin / model** — is the business model one that compounds (software-like margins, network
   effects, repeatable expansion) vs. linear services that don't scale?

State the verdict directly. Founders are better served by an honest "this looks like a strong
business but not an obvious venture-scale one, and here's why" than by false encouragement.

---

## Step 6: Common gaps that sink raises

Check for these frequent killers and flag any present:

- No ask / no use of funds.
- No contact info or no clear way to follow up.
- Problem stated as a solution ("the problem is they don't use our product").
- Vague or top-down-only market ("1% of a $50B market" with no bottom-up logic).
- All vision, no evidence — no traction, pilots, or product progress of any kind.
- Team slide with logos but no roles or relevant accomplishments.
- Too long (>15–20 slides for pre-seed/seed) or wall-of-text slides.
- Competition slide that claims "no competitors" (reads as "I haven't looked").
- Numbers that don't reconcile across slides (users, revenue, market).
- Solo founder with none of the build/raise/scale doubts addressed (see Step 3).

---

## Step 7: Write the review

Produce a single written summary titled `Deck Review — [Company]`. Save it next to the deck (or
wherever the founder keeps notes).

### Summary template

```markdown
# Deck Review — [Company]
**Reviewed:** YYYY-MM-DD · **Stage:** [pre-seed/seed] · **Raise:** [$ / not stated]

## Readiness verdict
[One of: READY TO SEND · NEEDS WORK · NOT YET]
One-paragraph plain-English summary.

## Investability gates
- **Entity:** [✅/🟠/🔴] — [C-corp / LLC / foreign / unknown] — [implication]
- **Venture scale:** [✅/🟠/🔴] — comps: [Company A ($Xrev/$Yval), …] — [verdict]

## Essentials
- ✅ Contact info — slide N
- 🔴 The ask — not in deck
- 🟠 Why this team — implied on team slide, never stated
- ... (every essential, with slide pointer)

## Solo-founder check (if applicable)
- Build / Fundraise & Sell / Scale — [status each]

## Top fixes before sending
1. [highest-impact fix]
2. ...
3. ...

## Flags (🟠) — worth addressing but not blockers
- ...
```

---

## Step 8: Summarize to chat

After writing, surface:
- The **readiness verdict** (Ready to send / Needs work / Not yet).
- Both **gate results** (entity + venture scale) — call out any 🔴 first; an LLC or a non-venture-
  scale market changes everything.
- The **top 3 fixes** before the deck goes out.

---

## What this skill does NOT do

- It does not assign a numeric score or grade.
- It does not give legal or tax advice — entity and QSBS notes are flags to confirm with counsel.
- It does not size the market in detail (price × volume TAM/SAM/SOM is a separate exercise).
- It assumes **US-based venture investment** norms; adapt judgment for other geographies or
  non-venture funding paths.
