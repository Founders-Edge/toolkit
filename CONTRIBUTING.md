# Contributing

Thanks for helping make these skills better for founders. This repo holds founder-facing
[Claude Code](https://claude.com/claude-code) skills — tools founders run on themselves before
they pitch. Contributions are welcome under a few ground rules.

## What we accept

- **Fixes and sharpening of existing skills** — clearer instructions, corrected checklists,
  better edge-case handling, typo fixes. This is the most valuable kind of contribution.
- **New skills**, if they are founder-facing and generally useful (fundraise prep, investor
  communication, company hygiene). Open an issue describing the skill before writing it so we
  can agree it fits.

## What we don't accept

- Fund-specific or investor-side workflows (deal memos, sourcing, CRM automation) — those live
  in a separate private repo.
- Anything containing real company data, names, or documents. Examples in skills must be
  invented and clearly generic.
- Skills that give legal, tax, or securities advice. Skills can help founders *organize* and
  *prepare*; they must tell users to consult professionals for the rest.

## How to contribute

1. Fork the repo and create a branch.
2. Make your change. Each skill is a single `SKILL.md` under
   `plugins/foundersedge-toolkit/skills/<skill-name>/`.
3. Test it: install the plugin from your fork
   (`/plugin marketplace add <your-fork>` in Claude Code) and run the skill end-to-end
   against a realistic (invented) founder scenario.
4. Open a pull request. Describe what changed and, for behavior changes, paste a short
   before/after example of the skill's output.

## Style for skills

- Write instructions for the model in plain, direct language — imperatives, not descriptions.
- Keep the frontmatter `description` specific about *when* the skill should trigger.
- Prefer checklists and concrete criteria over vague guidance ("mark 🔴 if X is missing"
  beats "evaluate completeness").
- Founder-first tone: candid, practical, never condescending.

## License

By contributing, you agree your contributions are licensed under the [MIT License](LICENSE).
