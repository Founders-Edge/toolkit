# FoundersEdge Toolkit

> Open, founder-facing [Claude](https://claude.com/claude-code) skills from **[FoundersEdge](https://foundersedge.vibe)**.
> These are tools we use on the investing side, sanitized and shared so founders can run them on
> themselves *before* they pitch.

Internal FoundersEdge workflows (CRM automation, deal memos, term sheets) live in a separate
private repository. This repo contains only skills that are safe and useful to share publicly.

## Skills

| Skill | What it does | Run it when |
|-------|--------------|-------------|
| `diligence-review` | Walks a standard pre-seed/seed diligence checklist (Capital, Cap Table, Market, Product, Team, Legal) against your dataroom, marks each item ✅ / 🔴 / 🟠, and writes a "Diligence Review" summary. | Before you start raising — every 🔴 it surfaces is a question an investor will eventually ask. |

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
            └── diligence-review/
                └── SKILL.md        # the skill definition
```

## License

Shared by FoundersEdge for founders to use freely.
