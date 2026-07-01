---
name: diligence-review
description: >
  Run a pre-termsheet diligence checklist on an early-stage startup. Use this skill whenever
  someone asks to do diligence, run the diligence checklist, review a dataroom, complete
  pre-investment due diligence, prepare a dataroom for fundraising, or "run diligence on [company]".
  Triggers on: "do diligence on", "diligence checklist", "review the dataroom for",
  "pre-termsheet review of", "check if my dataroom is ready".

  This skill walks a standard pre-seed/seed diligence checklist (Capital, Cap Table, Market,
  Product, Team, Legal) against a company's dataroom (a local folder of PDFs/docs), marks each
  item ✅ complete / 🔴 outstanding / 🟠 moving forward but flagged, and produces a written
  "Diligence Review" summary.

  Works two ways:
  - **Founders** can run it on their own dataroom to find gaps before they pitch investors.
  - **Investors** can run it as part of pre-termsheet diligence.

  Always use this skill for diligence reviews — do not attempt the checklist from memory.
---

# Diligence Review Skill

Walks a standard pre-termsheet diligence checklist, sources answers from a dataroom (plus call
notes and founder confirmation where available), and writes a single "Diligence Review — [Company]"
summary.

> **Founders:** run this on your own dataroom *before* you start raising. Every 🔴 it surfaces is
> a question an investor will eventually ask — better to find it yourself first.

---

## Workflow

```
1. IDENTIFY     → Company, dataroom location
2. INVENTORY    → List dataroom files; categorize by checklist section
3. EXTRACT      → Read each PDF/doc; pull facts mapped to checklist items
4. CROSS-REF    → Compare extracted facts to the founder's stated answers (call notes, claims)
5. CLASSIFY     → Mark each checklist item ✅ / 🔴 / 🟠 with one-line evidence
6. WRITE        → Produce the "Diligence Review — [Company]" summary
7. SUMMARIZE    → Surface 🔴 items + 🟠 flags and next steps
```

---

## Step 1: Identify

Required inputs (ask if not given):
- Company name
- Dataroom location: a local folder path (and/or links/files the company has shared)
- Who is preparing the review (the founder, or the reviewing investor)

---

## Step 2: Inventory the dataroom

Use `Glob` to list the folder. Build a quick categorization table — which files map to which
checklist sections. A dataroom built with the `dataroom-prep` skill is already organized into
`Legal / Cap Table / Capital / Traction / Product / Team` folders that map 1:1 to these sections.
Common buckets:

| File pattern | Maps to checklist sections |
|---|---|
| Certificate of Incorporation, Bylaws, Board Consent | Legal: DE C-corp, articles |
| Founder SPA / Stock Purchase Agreement | Cap Table: founder vesting, ownership |
| PIIA (Proprietary Info & Inventions Assignment) | Cap Table: IP assignment clauses |
| Equity Incentive Plan, Stock Option Notice | Cap Table: option plan, founder ownership |
| Indemnification Agreements | Legal: officer/director indemnification |
| State Corp Qualification, Foreign SOI | Legal: state qualification, good standing |
| Cap table (.xlsx, Carta export) | Cap Table: ownership, SAFEs, warrants, debt |
| Income statement / P&L / Balance sheet | Capital: burn, runway |
| Tax filing | Capital: filed taxes |
| Customer contracts / MSAs / SOWs | Market: traction validation |
| IP filings / patent docs | Product: patents |
| Founder reference list | Team: references |

If the company tracks documents elsewhere (a CRM record, a shared drive, a pitch-deck link),
gather those too — but the local dataroom folder is the source of truth for this review.

---

## Step 3: Extract facts from each file

Read each PDF in the dataroom (use `Read` on PDF files — the Read tool handles PDFs). For each
document, capture:
- **Document type** (e.g., "Certificate of Incorporation")
- **Effective date** (formation date, signing date, vesting start)
- **Parties** (founders, board members, state of incorporation)
- **Key terms** (vesting schedule, share counts, IP assignment language present?)

Build an internal facts table before classifying checklist items. Do NOT skim — quote the
exact clause when it is checklist-relevant (e.g., the vesting schedule, the IP assignment
trigger language, the share counts).

**Large dataroom optimization:** if there are >20 files, dispatch parallel `Explore` or `Read`
agents grouped by checklist section.

---

## Step 4: Cross-reference stated claims

Pull together whatever the founder has stated elsewhere — call notes, transcripts, the pitch
deck, prior emails — and compare against the documents:
- Burn rate stated in calls vs. P&L in the dataroom
- Customer count / ARR stated vs. customer contracts in the dataroom
- Founder ownership stated vs. the cap table

Note any divergence — this is a 🟠 flag candidate.

---

## Step 5: Classify each checklist item

Use this status legend strictly:

| Mark | Meaning |
|------|---------|
| ✅ | Complete / addressed — evidence present and consistent |
| 🔴 | Outstanding — evidence missing or unclear; blocks termsheet |
| 🟠 | Moving forward but flagging — partial evidence, minor concern, or intentional accept-and-monitor |

Every item gets a one-line evidence pointer: file name + page/section, or "(asked founder — pending)".

### Full checklist (in note order)

**Capital — Financial records**

- [ ] Filed taxes last year (if applicable)
- [ ] Burn rate per last 3 months matches the founder's answer
- [ ] Actual financials / customer contracts match reported traction
- [ ] Anticipated runway 12+ months post-investment
- [ ] Investor update cadence (frequency)
- [ ] Use of funds / founder salaries

**Cap Table**

- [ ] Founders + founding team own ≥80% equity
- [ ] All founders vesting (or willing to re-vest) over 4 years
- [ ] Founder + employee/contractor contracts have IP assignment clause
- [ ] Less than $1M in SAFEs/Notes on the balance sheet
- [ ] Prior SAFE/Notes — any equity warrants?
- [ ] Any debt? Founder loans?
- [ ] Any foreign investors that could trigger CFIUS?
- [ ] Any accelerator participation?

**Market Need & Timing**

- [ ] Customer contracts validate founder claims
- [ ] Sales pipeline / marketing plan matches target customer

**Product**

- [ ] Patents / registered IP — filings match reported
- [ ] Prior employer IP claim risk?

**Team**

- [ ] 3 reference checks (if outside personal network)
- [ ] Public reputation & lawsuit check

**Legal**

- [ ] Articles of incorporation — DE C-corp (or chosen entity), timeline matches tax answer
- [ ] Parent companies / subsidiaries
- [ ] Required certifications/permits/licenses
- [ ] Legally in good standing
- [ ] Advisors/employees with shares/options across states — state filing requirements
  considered (confirm with counsel; CA, NY, WA, IL, FL most common)
- [ ] No outstanding lawsuits
- [ ] "Anything I didn't ask that I should have?"
- [ ] Pre-termsheet consideration checklist complete
- [ ] QSBS plan
- [ ] If buying common stock, valuation comparison vs. the offered price

---

## Step 6: Write the review

Produce a single written summary titled `Diligence Review — [Company]`. If you keep these in a
CRM, shared drive, or notes app, save it there; otherwise write it to a Markdown file next to the
dataroom.

If a prior "Diligence Review — [Company]" already exists, **preserve it** — append a new dated
section rather than overwriting earlier findings.

### Summary template

```markdown
# Diligence Review — [Company]
**Reviewer:** [name] · **Last updated:** YYYY-MM-DD · **Dataroom:** [path or link]

## Status summary
- ✅ Complete: N items
- 🔴 Outstanding: N items
- 🟠 Flagged: N items

## Capital
- ✅ Filed taxes last year — [evidence]
- 🔴 Burn rate match — no P&L in dataroom; need last 3 mo income statement
- ...

## Cap Table
- ...

## Market Need & Timing
- ...

## Product
- ...

## Team
- ...

## Legal
- ...

## Outstanding items (🔴) — blockers before termsheet
1. [item] — owner: [founder/reviewer]
2. ...

## Flags (🟠) — accept-and-monitor
1. [item] — rationale: [why moving forward]
```

---

## Step 7: Summarize

After writing, surface to chat:
- Count of ✅ / 🔴 / 🟠
- Top 3 🔴 items that must be resolved before a termsheet
- Any 🟠 items that need judgment to accept

---

## Data Source Priority

1. Dataroom documents (legal source of truth for formation, vesting, IP)
2. CRM / deal record, if one exists (current cap, check size, ownership, stage)
3. Call notes / transcripts (founder's stated traction, runway, plans)
4. Founder confirmation (for any item not in 1–3)

---

## Special pattern: LLC → C-corp conversion

Pre-seed companies often incorporate the C-corp **right before** raising. When you see a recent
formation date (within 30–90 days of diligence), assume an LLC→C-corp conversion and check:

1. **IP assignment from the prior LLC** — typically lives in Schedule 1 of the Founder SPA
   Exhibit A (Intellectual Property Assignment Agreement). Look for an explicit reference to the
   predecessor LLC name (e.g., "[Company], LLC"). All software, branding, customer lists, and
   patent rights should be enumerated. ✅ when present and complete.
2. **Prior LLC tax filings** — even if the C-corp filed no taxes, the LLC may have. Ask the
   founder for the LLC's last K-1 / Schedule C / 1065 if applicable.
3. **Debt or accrued payables from LLC days** — founders often paid expenses personally; ask
   explicitly.
4. **Vesting commencement date deferred** — new C-corp founders often set a future Vesting
   Commencement Date (e.g., Jan 1 of next year) so the cliff aligns with the calendar. This is
   normal but flag 🟠 because founders are 0% vested at termsheet.
5. **§83(b) election deadline** — 30 days from the SPA execution date. **Compute and surface this
   deadline explicitly** in the review. A missed filing = ordinary income tax on vest = QSBS
   risk. Confirm every founder filed.
6. **State Blue Sky filings:**
   - California §25102(o) notice filed within 30 days of the first grant
   - Any state where a founder, director, advisor, or option grantee resides triggers state-
     specific filing requirements (CA, NY, WA, IL, FL most common). Extract addresses from
     SPAs / PIIAs and flag for counsel review.

## Special pattern: §83(b) election deadline tracker

When you read a Founder SPA, **always extract the Effective Date and compute Effective Date + 30
days** as the §83(b) filing deadline. Surface this as a dated 🔴 item if the deadline has not yet
passed and there is no confirmation of filing in the dataroom. This is the highest-value proactive
flag a diligence review can produce — missing this date is a real-money tax error.

## Reading order for a typical formation dataroom (heuristic)

When the dataroom is mostly formation/legal docs (typical at pre-seed), read in this order to
maximize information per file:

1. **Cert of Incorporation** → state, date, authorized shares, par value, incorporator
2. **Founder SPAs (one per founder)** → each founder's share count, vesting, acceleration,
   addresses (state Blue Sky), PIIA cross-reference, §83(b) deadline
3. **PIIA (one per founder)** → CA §2870 / state law, prior-employer IP rep, no third-party
   confidential info retained
4. **Equity Incentive Plan** → option pool size, ISO vs NSO, plan history (board approval,
   stockholder approval, §25102(o) status)
5. **State qualification + good standing certs** → DE in good standing, foreign qualifications

Skip-deeper-read for: bylaws, board consents (formation), indemnification agreements (form),
option grant templates — these are typically standard and only need a glance to confirm presence.

## Common dataroom gaps (mark 🔴 when missing)

Many early-stage datarooms ship only formation + cap table docs — the financials, traction, and
team-reference materials are the items most often missing, and each blocks a checklist item.

> The canonical per-section list of what *should* be in a dataroom lives in the **`dataroom-prep`**
> skill — this skill judges what's present rather than re-specifying the inventory. (If you're a
> founder finding gaps here, `dataroom-prep` is where you go to build them.)

When a needed document is missing, don't just mark it 🔴 — phrase the entry as a question the
founder can act on, e.g.:
"🔴 Burn rate match — no income statement in dataroom; **ask founder for last 3 mo P&L**"
