# FoundersEdge Toolkit

<p align="center">
  <img src="assets/hero.png" alt="A founder picking tools out of a toolbox at her laptop" width="700">
</p>

**Free, open [Claude](https://claude.com/claude-code) skills to help you get ready to raise — from [FoundersEdge](https://foundersedge.com).**

These are the same checks investors run on your company. We think you should get to run them
first. Point Claude at your deck or dataroom, and these skills will tell you what's strong,
what's missing, and what an investor will ask about — *before* you're in the room.

## Skills

| Skill | What it does | Run it when |
|-------|--------------|-------------|
| `deck-review` | Checks your pitch deck for the essentials investors look for (contact info, founder credibility, problem, why-this-team, the ask), runs the solo-founder build/raise/scale test, and applies two investability gates — investable US C-corp, and venture scale (comps that hit >$100M revenue or $1B+ valuation). | Before you send your deck to anyone. |
| `dataroom-prep` | Builds an investor-ready dataroom — the standard folder structure, what each document must contain, and a gather-list of what's still missing. | When you're getting organized to raise. |
| `diligence-review` | Walks a standard pre-seed/seed diligence checklist (Capital, Cap Table, Market, Product, Team, Legal) against your dataroom, marks each item ✅ / 🔴 / 🟠, and writes a "Diligence Review" summary. | After building your dataroom — every 🔴 it surfaces is a question an investor will eventually ask. |
| `investor-update` | Drafts a tight, skimmable investor update (TL;DR, metrics, highlights, lowlights, asks, runway) in your own voice. | Every month once you have investors. |
| `investor-outreach` | Helps you get investor meetings without a warm intro: an honest readiness check, an ideal investor persona, a channel brainstorm, messaging for the channels you choose built on five ingredients, a pre-send checklist, and a 30-investor experiment with a tracker. | When you're building your investor list or about to send cold outreach. |
| `landing-page-review` | Puts your landing page in a blind lineup with your top competitors, has a panel of five AI buyer personas built from your ICP score and rank them, then redesigns a local copy until the panel picks yours. A slop check stops the redesign from getting more generic, and nothing gets invented: missing proof becomes a to-do list for you. | Before you spend on traffic, or when your homepage isn't converting. |

## Get started

You'll need [Claude Code](https://claude.com/claude-code). Then, inside Claude Code:

```
/plugin marketplace add Founders-Edge/toolkit
/plugin install foundersedge-toolkit
```

That's it. Most skills need nothing else. `landing-page-review` is the exception: it also needs
Google Chrome, Node.js 22+ and Python 3 (plus the [Claude in Chrome](https://claude.com/chrome)
extension, but only for sites that block headless browsers). It runs a panel of AI judges over
several rounds, so it uses more model time than the other skills; run it from a Sonnet session.

### No Claude Code? Use `investor-outreach` in the Claude app

`investor-outreach` also works in the Claude desktop, web and mobile apps:

1. Download
   [investor-outreach.zip](https://github.com/Founders-Edge/toolkit/raw/main/downloads/investor-outreach.zip).
2. In Claude, open **Customize > Skills**, click **+**, then **Create skill**, then
   **Upload a skill**, and choose the ZIP.
3. Start a new chat and ask for help in plain English.

Not using Claude at all? [prompts/investor-outreach.md](prompts/investor-outreach.md) is a
copy-paste version you can use in any AI assistant.

Now just ask in plain English:

> *"Review my pitch deck at ~/Documents/deck.pdf"*
> *"Help me set up a dataroom"*
> *"Run diligence on my dataroom at ~/Documents/MyCo-dataroom"*
> *"Draft my monthly investor update"*
> *"Help me plan cold outreach to investors for my pre-seed round"*
> *"Review my landing page at https://mycompany.com against our competitors"*

## What's inside

```
toolkit/
├── .claude-plugin/
│   └── marketplace.json          # marketplace catalog
├── downloads/                    # ZIPs for uploading a skill in the Claude app
├── prompts/                      # copy-paste prompt versions
└── plugins/
    └── foundersedge-toolkit/
        ├── .claude-plugin/
        │   └── plugin.json        # plugin manifest
        └── skills/
            ├── deck-review/
            │   └── SKILL.md
            ├── dataroom-prep/
            │   └── SKILL.md
            ├── diligence-review/
            │   └── SKILL.md
            ├── investor-outreach/
            │   └── SKILL.md
            ├── investor-update/
            │   └── SKILL.md
            └── landing-page-review/
                ├── SKILL.md
                ├── references/
                ├── scripts/
                └── tests/
```

## Contributing

Found something a skill gets wrong, or have an idea that would help founders? We'd love the
help — see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE) — use these skills freely, on yourself or with the founders you work with.
