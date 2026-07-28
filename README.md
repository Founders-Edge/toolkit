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

## Get started

You'll need [Claude Code](https://claude.com/claude-code). Then, inside Claude Code:

```
/plugin marketplace add Founders-Edge/toolkit
/plugin install foundersedge-toolkit
```

That's it. Now just ask in plain English:

> *"Review my pitch deck at ~/Documents/deck.pdf"*
> *"Help me set up a dataroom"*
> *"Run diligence on my dataroom at ~/Documents/MyCo-dataroom"*
> *"Draft my monthly investor update"*

## What's inside

```
toolkit/
├── .claude-plugin/
│   └── marketplace.json          # marketplace catalog
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
            └── investor-update/
                └── SKILL.md
```

## Contributing

Found something a skill gets wrong, or have an idea that would help founders? We'd love the
help — see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE) — use these skills freely, on yourself or with the founders you work with.
