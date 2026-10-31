#!/usr/bin/env python3
"""Set up a blind judging round: shuffle pages, assign letters, copy screenshots.

  python3 new_round.py RUN_DIR ROUND TARGET_VERSION      e.g. new_round.py ./landing-page-review/acme 2 v1

Takes   RUN_DIR/shots/target/<TARGET_VERSION>-{desktop,mobile}-NN.png
        RUN_DIR/shots/competitors/<competitor id>-{desktop,mobile}-NN.png  (ids from brief.json)
Writes  a NEUTRAL judging folder in the system temp dir (random name, nothing else in it):
          <tmp>/lpr-xxxx/<Letter>-{desktop,mobile}-NN.png
          <tmp>/lpr-xxxx/judgments/          judges write <judge id>.json here
        RUN_DIR/rounds/rN/round.json         where that folder is
        RUN_DIR/rounds/rN/mapping.json       letter -> page (never show this to judges)
        RUN_DIR/rounds/rN/pages/             archive copy of what the judges saw
        RUN_DIR/rounds/rN/prompts/<jid>.md   ready-to-send prompt per judge, rendered from the
                                             template in references/judges.md
        RUN_DIR/rounds/rN/prompts/slop.md    slop-judge prompt archive (only if brief.slop.enabled),
                                             from references/slop-judge.md
        <tmp>/lpr-xxxx/prompt-<jid>.md       the same prompts, in the neutral folder
Prints  JSON {"judgeDir", "outDir", "spawn": {jid: one-line instruction}} — send each one-liner
        as the whole prompt of a fresh judge agent; judges never see RUN_DIR.
Order is shuffled fresh every round so position bias can't follow a page.
"""
import json
import random
import re
import shutil
import string
import sys
import tempfile
from pathlib import Path

# Tile caps used by shoot.mjs / capture.js: a page with this many tiles was cut off.
MAX_TILES = {"desktop": 3, "mobile": 2}
REFS = Path(__file__).resolve().parent.parent / "references"
JUDGES_MD = REFS / "judges.md"
SLOP_MD = REFS / "slop-judge.md"


def template_parts(md_path=JUDGES_MD, marker="judge-prompt-template"):
    """Pull the prompt template, rubric table and output schema out of a reference file."""
    md = md_path.read_text(encoding="utf-8")
    tpl = re.search(rf"<!-- {marker}:start -->\s*```text\n(.*?)```\s*<!-- {marker}:end -->", md, re.S)
    rubric = re.search(r"## Rubric.*?\n(\| Dimension.*?)\n\n", md, re.S)
    schema = re.search(r"## Output schema.*?```json\n(.*?)```", md, re.S)
    if not (tpl and rubric and schema):
        sys.exit(f"could not parse template/rubric/schema from {md_path}")
    return tpl.group(1), rubric.group(1).strip(), schema.group(1).strip()


def fill(text, values):
    for k, v in values.items():
        text = text.replace("{{" + k + "}}", v)
    leftover = re.findall(r"{{\w+}}", text)
    if leftover:
        sys.exit(f"unfilled template fields: {leftover}")
    return text


def slop_enabled(brief):
    return bool((brief.get("slop") or {}).get("enabled"))


def client_terms(brief):
    """The client's name and domain stem, for the leak check (e.g. "Acme", "acme")."""
    t = brief.get("target", {})
    terms = {t.get("name", "")}
    host = re.sub(r"^https?://(www\.)?", "", t.get("url", "")).split("/")[0]
    terms.add(host.split(".")[0])
    return [x for x in terms if len(x) >= 2]


def judge_use_case(brief):
    use_case = brief.get("judgeUseCase") or ""
    if not use_case:
        sys.exit("brief.json needs judgeUseCase (the buyer's problem, no product names) — see references/judges.md")
    # Everything judges are told must be free of the client's name (whole-word match, so a
    # short name like "Arc" doesn't trip on "search").
    texts = {"judgeUseCase": use_case}
    for j in brief.get("judges", []):
        texts[f'{j.get("id")}.title'] = j.get("title", "")
        texts[f'{j.get("id")}.persona'] = j.get("persona", "")
    for term in client_terms(brief):
        pat = re.compile(rf"\b{re.escape(term)}\b", re.I)
        hits = [k for k, v in texts.items() if pat.search(v or "")]
        if hits:
            sys.exit(f"{', '.join(hits)} mention the client ({term}) — rephrase without the client's name")
    return use_case


def truncated(d, stem, kind, n_tiles):
    """Whether the page continues below its last tile: shoot.mjs's sidecar if present,
    else fall back to "used every tile" (in-browser captures have no sidecar)."""
    side = d / f"{stem}-{kind}.json"
    if side.exists():
        try:
            return bool(json.loads(side.read_text(encoding="utf-8")).get("truncated"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass
    return n_tiles >= MAX_TILES[kind]


def reuse_slop_from(rounds_dir, rdir, brief):
    """A confirmation round re-judges an unchanged version, so its slop score can't change:
    reuse the previous round's instead of spawning the slop judge again."""
    rnd = int(rdir.name[1:])
    prev = rounds_dir / f"r{rnd - 1}" / "tally.json"
    this_version = json.loads((rdir / "round.json").read_text(encoding="utf-8"))["targetVersion"]
    if prev.exists():
        t = json.loads(prev.read_text(encoding="utf-8"))
        if t.get("targetVersion") == this_version and t.get("slop"):
            return rnd - 1
    return None


def render_prompts(brief, listing, cut, judge_dir, rdir):
    tpl, rubric, schema = template_parts()
    use_case = judge_use_case(brief)
    blocks = []
    for letter, kinds in listing.items():
        lines = [f"Page {letter}:"]
        for kind in ("desktop", "mobile"):
            paths = kinds[kind]
            cut_note = " (continues below the last tile)" if cut[letter][kind] else ""
            lines.append(f"  {kind}{cut_note}:")
            lines += [f"    {p}" for p in paths]
        blocks.append("\n".join(lines))
    pages = "\n\n".join(blocks)
    out = {}
    (rdir / "prompts").mkdir(exist_ok=True)
    for j in brief["judges"]:
        text = fill(tpl, {"title": j.get("title", ""), "role": j.get("role", ""), "persona": j.get("persona", ""),
                          "judge_use_case": use_case, "n": str(len(listing)), "pages": pages,
                          "rubric": rubric, "schema": schema.replace('"judge": "j3"', f'"judge": "{j["id"]}"'),
                          "out_file": str(judge_dir / "judgments" / f"{j['id']}.json")})
        (rdir / "prompts" / f"{j['id']}.md").write_text(text, encoding="utf-8")  # archive
        path = judge_dir / f"prompt-{j['id']}.md"
        path.write_text(text, encoding="utf-8")
        out[j["id"]] = str(path)
    if slop_enabled(brief) and not reuse_slop_from(rdir.parent, rdir, brief):
        stpl, srubric, sschema = template_parts(SLOP_MD, "slop-prompt-template")
        text = fill(stpl, {"n": str(len(listing)), "pages": pages, "rubric": srubric, "schema": sschema,
                           "out_file": str(judge_dir / "judgments" / "slop.json")})
        (rdir / "prompts" / "slop.md").write_text(text, encoding="utf-8")  # archive
        path = judge_dir / "prompt-slop.md"
        path.write_text(text, encoding="utf-8")
        out["slop"] = str(path)
    return out


def tiles(d, stem, kind):
    return sorted(d.glob(f"{stem}-{kind}-[0-9][0-9].png"))


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    run, rnd, version = Path(sys.argv[1]).resolve(), int(sys.argv[2]), sys.argv[3]
    brief = json.loads((run / "brief.json").read_text(encoding="utf-8"))
    if not brief.get("competitors"):
        sys.exit("brief.json has no competitors")
    if not brief.get("judges"):
        sys.exit("brief.json has no judges")
    template_parts()  # fail fast, before creating anything
    if slop_enabled(brief):
        template_parts(SLOP_MD, "slop-prompt-template")
    judge_use_case(brief)

    sources = [({"kind": "target", "id": version}, run / "shots" / "target", version)]
    sources += [({"kind": "competitor", "id": c["id"]}, run / "shots" / "competitors", c["id"]) for c in brief["competitors"]]
    entries = [(meta, {k: tiles(d, stem, k) for k in ("desktop", "mobile")},
                {k: truncated(d, stem, k, len(tiles(d, stem, k))) for k in ("desktop", "mobile")}) for meta, d, stem in sources]
    missing = [m["id"] for m, files, _ in entries if not files["desktop"] or not files["mobile"]]
    if missing:
        sys.exit(f"missing desktop or mobile screenshots for: {', '.join(missing)}")

    rdir = run / "rounds" / f"r{rnd}"
    if (rdir / "mapping.json").exists():
        sys.exit(f"{rdir} already set up — delete it first to re-shuffle")
    random.SystemRandom().shuffle(entries)
    judge_dir = Path(tempfile.mkdtemp(prefix="lpr-"))
    (judge_dir / "judgments").mkdir()
    (rdir / "pages").mkdir(parents=True, exist_ok=True)

    mapping, listing, cut = {}, {}, {}
    for letter, (meta, files, trunc) in zip(string.ascii_uppercase, entries):
        mapping[letter] = meta
        cut[letter] = trunc
        listing[letter] = {}
        for kind, paths in files.items():
            listing[letter][kind] = []
            for i, f in enumerate(paths, 1):
                name = f"{letter}-{kind}-{i:02d}.png"
                shutil.copyfile(f, judge_dir / name)
                shutil.copyfile(f, rdir / "pages" / name)
                listing[letter][kind].append(str(judge_dir / name))
    (rdir / "mapping.json").write_text(json.dumps(mapping, indent=2), encoding="utf-8")
    (rdir / "round.json").write_text(json.dumps({"judgeDir": str(judge_dir), "targetVersion": version}, indent=2), encoding="utf-8")
    reused = reuse_slop_from(rdir.parent, rdir, brief) if slop_enabled(brief) else None
    if reused:
        info = json.loads((rdir / "round.json").read_text(encoding="utf-8"))
        (rdir / "round.json").write_text(json.dumps({**info, "slopFrom": reused}, indent=2), encoding="utf-8")
    prompts = render_prompts(brief, listing, cut, judge_dir, rdir)
    spawn = {k: f"Read {v} and follow its instructions exactly." for k, v in prompts.items()}
    print(json.dumps({"judgeDir": str(judge_dir), "outDir": str(judge_dir / "judgments"), "spawn": spawn}, indent=2))


if __name__ == "__main__":
    main()
