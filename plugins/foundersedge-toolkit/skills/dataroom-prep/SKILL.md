---
name: dataroom-prep
description: >
  Help a founder build and organize a fundraising dataroom before they start raising. Use this
  skill whenever someone asks what goes in a dataroom, to build or set up a dataroom, to organize
  their dataroom, what documents investors will ask for, or how to prepare for diligence.
  Triggers on: "prep my dataroom", "build a dataroom", "what goes in a dataroom", "organize my
  dataroom", "what docs do investors need", "get ready for diligence", "set up our data room".

  This is the build-side partner to the diligence-review skill: diligence-review finds the gaps,
  dataroom-prep assembles the folder and tells the founder exactly what each document should
  contain. Tuned for US-based pre-seed/seed venture rounds. Produces a dataroom folder skeleton
  plus a gather-list of what's still missing.

  Always use this skill for dataroom prep — do not assemble the list from memory.
---

# Dataroom Prep — Get Raise-Ready

Builds a clean, investor-ready dataroom: the standard folder structure, the documents that belong
in each section, what each document must actually contain, and a checklist of what the founder
still needs to gather. Tuned for **US pre-seed/seed** rounds.

> **Founders:** a tidy, complete dataroom signals you're organized and lowers an investor's
> perceived risk. Build it *before* you pitch — then run the `diligence-review` skill on it to
> catch gaps the way an investor will.

---

## Workflow

```
1. IDENTIFY    → Company, entity type, where the dataroom will live (folder path)
2. SCAFFOLD    → Create the standard section folders
3. INVENTORY   → For anything the founder already has, file it into the right section
4. SPEC        → For each section, list required docs + what each must contain
5. GATHER-LIST → Produce the checklist of what's still missing, with how to get it
6. HANDOFF     → Tell them to run diligence-review on the assembled dataroom
```

---

## Step 1: Identify

Ask if not given:
- Company name and entity type (Delaware C-corp? LLC converting? — affects which docs exist)
- Where the dataroom should live: a local folder path, or a shared drive
- What they already have on hand

---

## Step 2: Scaffold the structure

Create this folder structure (use the folder path the founder gives). These six sections use the
**same names as the `diligence-review` checklist**, so the dataroom maps 1:1 to how it'll be
reviewed:

```
[Company]-Dataroom/
├── Legal/          # Corporate & legal — formation, bylaws, consents, financing docs
├── Cap Table/      # Equity — cap table export, SPAs, 83(b), option plan, IP assignment
├── Capital/        # Financials — P&L, balance sheet, model, tax, use of funds
├── Traction/       # Market & traction — deck, customer contracts, pipeline, metrics
├── Product/        # Product & IP — overview, demo, filings
└── Team/           # Founder bios, references, employment & advisor agreements
```

(Diligence-review's checklist sections are Legal, Cap Table, Capital, Market/Traction, Product, and
Team — these folders match them one-to-one.)

Also drop a top-level `00-START-HERE.md` index listing what's in each folder (investors appreciate
a map).

---

## Step 3 & 4: What goes in each section

This is the **canonical inventory** of what belongs in a dataroom — the `diligence-review` skill
defers to this list rather than re-specifying it. For each section, the required documents and what
each must actually contain. Mark what the founder has vs. needs — but do **not** judge or classify
the contents here; that's `diligence-review`'s job (see handoff in Step 6).

**Format matters.** The cap table and the financials must be delivered as **spreadsheets or tool
exports** (`.xlsx` / `.csv` / Google Sheet / Carta link), not as prose write-ups. Investors model
dilution and stress-test burn *in a spreadsheet* — a narrative summary is a useful supplement but
never a substitute for the underlying numbers in a workable format.

### Legal — Corporate & Legal
- **Certificate of Incorporation** — state (Delaware expected), date, authorized shares, par value.
- **Bylaws**.
- **Board consents / formation board minutes**.
- **EIN / tax ID confirmation** — the IRS CP-575 (or equivalent) as its own document, not just an
  EIN number quoted inside another file.
- **State qualifications & good-standing certificates** — DE good standing, plus any state where you
  do business.
- **Indemnification agreements** (if any).
- **Prior financing docs** — every signed SAFE / convertible note / prior round docs.

### Cap Table — Cap Table & Equity
- **Cap table (spreadsheet or Carta/Pulley/AngelList export)** — REQUIRED as an actual spreadsheet
  or tool export showing every holder, shares, fully diluted ownership %, all SAFEs/notes with caps
  & discounts, warrants, and the option pool. A prose "cap table summary" doc is a helpful
  supplement but **is not a substitute** — ship the spreadsheet. No cap-table tool yet? Build a
  clean `.xlsx` from the source documents.
- **Founder Stock Purchase Agreements (one per founder)** — share counts, vesting schedule,
  acceleration, vesting commencement date.
- **83(b) election confirmations** — proof each founder filed within 30 days of their stock
  purchase. (This is high-value and often missing — see note below.)
- **Equity Incentive Plan / option plan** — pool size, board & stockholder approval. If only
  *proposed* (not yet adopted), include a short status memo saying so.
- **Option grant records** — any grants made.
- **PIIA / CIIAA (Proprietary Info & Inventions Assignment) per founder & employee** — confirms IP
  is assigned to the company. These IP-assignment agreements live **here** (with equity), not in Team.

### Capital — Financials
Ship these as **spreadsheets**, not prose docs (see "Format matters" above).
- **Income statement / P&L** — last 3 months at minimum, as a spreadsheet (this is the #1 thing
  missing from early datarooms and it blocks burn/runway verification).
- **Balance sheet**.
- **Bank balance / runway summary** — current cash and months of runway.
- **Financial model / projections** — a forward-looking model (12–24 months) built off the signed
  contracts plus pipeline: revenue ramp, hiring plan, burn, and runway under the raise. Investors
  want to see where the money takes you, not only where you've been. Even a simple one-tab
  spreadsheet beats none.
- **Tax filings** — last year's, or a written "did not file / not yet required" note.
- **Use of funds** — how the raise will be spent.

### Traction — Market & Traction
- **Pitch deck** (current version) — include the actual **file (PDF)**, not just a link, so it
  lives with the dataroom.
- **Customer contracts / signed LOIs / pilot agreements** — proof behind any traction claims.
- **Sales pipeline** — current opportunities, ideally as a spreadsheet with stage and value.
- **Key metrics** — a short revenue/usage/growth/retention summary (MRR, active accounts, churn).

### Product — Product & IP
- **Product overview / demo link** — plus screenshots or a short walkthrough.
- **Patent or trademark filings** — only if the founder has claimed IP; the filings must match the
  claim.
- **Technical/architecture overview** (optional, light).

### Team
- **Founder bios / one-pager** — roles and relevant background. Put a copy **here in Team** even if a
  company overview elsewhere covers it — reviewers look in Team for founder background.
- **Org chart / key hires** (if any).
- **Reference list** — 3 references per founder with names + emails (founders forget this; investors
  will ask).
- **Employment & advisor agreements** — offer letters, employment agreements, advisor agreements.
  (IP-assignment agreements — PIIA/CIIAA — live under Cap Table with equity, not here.)

---

## Special note: recent C-corp conversions (very common at pre-seed)

If the company incorporated the C-corp recently (often right before raising, frequently converting
from an LLC), make sure the dataroom also includes:
- **IP assignment from the prior LLC** (often Schedule 1 of the Founder SPA's IP Assignment exhibit).
- **Prior LLC tax filings**, if the LLC operated.
- **83(b) elections** dated within 30 days of the *new* C-corp stock purchase — flag this deadline
  explicitly; a missed filing is a real-money tax error and a QSBS risk.

---

## Step 5: Gather-list

Produce a checklist of what's still missing, each with a one-line "how to get it":

```markdown
# [Company] Dataroom — Still to Gather
- [ ] Last 3 months P&L **as a spreadsheet** — export from QuickBooks/Xero or ask your bookkeeper
- [ ] Cap table **as .xlsx / Carta export** — a prose summary doesn't count
- [ ] Financial model (12–24 mo) — revenue ramp off signed contracts + pipeline, hiring, burn, runway
- [ ] Balance sheet
- [ ] 83(b) confirmations — find the USPS certified-mail receipts / IRS confirmations per founder
- [ ] Founder bios one-pager (in Team) + 3 reference names + emails per founder
- [ ] Pitch deck PDF (the file, not just a link)
- [ ] Signed customer LOIs — pull from email / DocuSign
- ...
```

---

## Step 6: Handoff

Once the dataroom is assembled, tell the founder to run the **`diligence-review`** skill on the
folder — it walks the same six sections, marks each item ✅ / 🔴 / 🟠, and surfaces the gaps an
investor would catch (including the §83(b) deadline tracker). Build here, then pressure-test there.

---

## What this skill does NOT do

- It does not judge, score, or classify the documents — assembling the dataroom is this skill's
  job. To evaluate the finished dataroom (and catch the §83(b) deadline), run the
  **`diligence-review`** skill. Build here, pressure-test there.
- It does not provide legal or tax advice — entity, 83(b), and QSBS items are flags to confirm with
  counsel/an accountant.
- It does not generate the legal documents themselves — it tells you what's needed and what each
  should contain.
- It assumes **US pre-seed/seed venture** norms.
