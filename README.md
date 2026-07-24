# FoundersEdge Toolkit

> Open, founder-facing [Claude](https://claude.com/claude-code) skills from **[FoundersEdge](https://foundersedge.com)**.
> These are tools we use on the investing side, sanitized and shared so founders can run them on
> themselves *before* they pitch.

Internal FoundersEdge workflows (CRM automation, deal memos, term sheets) live in a separate
private repository. This repo contains only skills that are safe and useful to share publicly.

## Skills

| Skill | What it does | Run it when |
|-------|--------------|-------------|
| `deck-review` | Checks your pitch deck for the essentials investors look for (contact info, founder credibility, problem, why-this-team, the ask), runs the solo-founder build/raise/scale test, and applies two investability gates — investable US C-corp, and venture scale (comps that hit >$100M revenue or $1B+ valuation). | Before you send your deck to anyone. |
| `dataroom-prep` | Builds an investor-ready dataroom — the standard folder structure, what each document must contain, and a gather-list of what's still missing. | When you're getting organized to raise. |
| `diligence-review` | Walks a standard pre-seed/seed diligence checklist (Capital, Cap Table, Market, Product, Team, Legal) against your dataroom, marks each item ✅ / 🔴 / 🟠, and writes a "Diligence Review" summary. | After building your dataroom — every 🔴 it surfaces is a question an investor will eventually ask. |
| `investor-update` | Drafts a tight, skimmable investor update (TL;DR, metrics, highlights, lowlights, asks, runway) in your own voice. | Every month once you have investors. |

## Install

These are [Claude Code](https://claude.com/claude-code) skills, distributed as a plugin marketplace.

```
/plugin marketplace add Founders-Edge/toolkit
/plugin install foundersedge-toolkit
```

Then just ask Claude, e.g. *"run diligence on my dataroom at ~/Documents/MyCo-dataroom"*.

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

See [CONTRIBUTING.md](CONTRIBUTING.md). Fixes and improvements to existing skills are welcome;
new skills should be founder-facing and generally useful, not fund-specific.

## License

[MIT](LICENSE) — use these skills freely, on yourself or with the founders you work with.
