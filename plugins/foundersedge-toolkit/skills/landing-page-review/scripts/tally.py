#!/usr/bin/env python3
"""Tally one judging round: validate judge JSON, de-anonymize, apply the stop rule.

  python3 tally.py RUN_DIR ROUND        e.g. tally.py ./landing-page-review/acme-20261024 2

Reads   RUN_DIR/brief.json
        RUN_DIR/rounds/rN/mapping.json     {"A": {"kind": "target", "id": "v1"}, "B": {"kind": "competitor", "id": "rivalone"}, ...}
        RUN_DIR/rounds/rN/round.json       -> judgeDir; judges wrote judgeDir/judgments/<judge id>.json
                                           (format in references/judges.md)
Writes  RUN_DIR/rounds/rN/judges/*.json    archive copy of every judge file
        RUN_DIR/rounds/rN/tally.json       aggregated scores + verdict
        RUN_DIR/rounds/rN/feedback.md      de-anonymized digest for the design agent
Prints  a one-line JSON verdict. Exit 0 = valid round, 3 = invalid judge files (re-run those judges).

Verdicts: "winner"   passed the bar, and the same version also passed the previous
                     `confirmRounds` round(s) — judging is noisy, so one pass isn't enough
          "confirm"  passed, but not yet confirmed: re-judge the SAME version (new shuffle,
                     fresh judges), no redesign
          "continue" didn't pass: redesign
          "round-cap" hit maxRounds without a confirmed win
          "plateau"  the last `plateauRounds` rounds didn't beat the best earlier score: stop
          "needs-input" won the vote but trailed only on offer/value for `inputRounds` rounds in a
                     row, and the page has a TODO.md: the gap needs founder facts, not more design: stop
          "reshoot"  2+ judges saw the same overlay (cookie banner, popup) covering a page: dismiss
                     it, re-shoot, touch rounds/rN.reshot, delete rounds/rN and redo round N.
                     Happens at most once per round (the .reshot marker)
Standard library only.
"""
import json
import shutil
import sys
from pathlib import Path
from statistics import mean

DIMS = ["clarity", "offer", "value", "professionalism"]
SLOP_DIMS = ["copy", "visual", "proof"]
DEFAULT_SLOP = {"enabled": False, "floor": 5, "maxDrop": 2}
DEFAULT_STOP = {"minFirstVotes": 4, "leadAllDims": True, "tolerance": 0.5, "confirmRounds": 1, "maxRounds": 5,
                "plateauRounds": 2, "inputRounds": 2}
# Dimensions the design agent can't win without facts from the founder (pricing, trials, customers).
FACT_DIMS = {"offer", "value"}


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def validate(judge, letters):
    """Return a list of problems with one judge's output (empty = valid)."""
    errs = []
    pages = judge.get("pages")
    if not isinstance(pages, dict):
        return ["missing 'pages' object"]
    if set(pages) != set(letters):
        errs.append(f"pages {sorted(pages)} != expected {sorted(letters)}")
    for letter, p in pages.items():
        if not isinstance(p, dict):
            errs.append(f"{letter} must be an object")
            continue
        for d in DIMS:
            v = p.get(d)
            if not isinstance(v, (int, float)) or isinstance(v, bool) or not 1 <= v <= 10:
                errs.append(f"{letter}.{d} must be a number 1-10, got {v!r}")
        for k in ("confusions", "concerns"):
            if not isinstance(p.get(k, []), list):
                errs.append(f"{letter}.{k} must be a list")
    rk = judge.get("ranking")
    if not isinstance(rk, list) or sorted(rk) != sorted(letters):
        errs.append(f"ranking must list every page exactly once, got {rk!r}")
    return errs


def validate_slop(s, letters):
    errs = []
    pages = s.get("pages")
    if not isinstance(pages, dict):
        return ["missing 'pages' object"]
    if set(pages) != set(letters):
        errs.append(f"pages {sorted(pages)} != expected {sorted(letters)}")
    for letter, p in pages.items():
        if not isinstance(p, dict):
            errs.append(f"{letter} must be an object")
            continue
        for d in SLOP_DIMS:
            v = p.get(d)
            if not isinstance(v, (int, float)) or isinstance(v, bool) or not 1 <= v <= 10:
                errs.append(f"{letter}.{d} must be a number 1-10, got {v!r}")
        if not isinstance(p.get("evidence", []), list):
            errs.append(f"{letter}.evidence must be a list")
    return errs


def slop_baseline(run, rnd):
    """The original page's (v0's) slop score from the earliest slop-judged round, if any."""
    for prev in range(1, rnd):
        pt = run / "rounds" / f"r{prev}" / "tally.json"
        if pt.exists():
            t = load(pt)
            if t.get("targetVersion") == "v0" and t.get("slop"):
                return t["slop"]["target"]
    return None


def label(m, brief):
    if m["kind"] == "target":
        return f"YOUR PAGE ({m['id']})"
    comp = next((c for c in brief.get("competitors", []) if c["id"] == m["id"]), {})
    return comp.get("name", m["id"])


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    run, rnd = Path(sys.argv[1]), int(sys.argv[2])
    rdir = run / "rounds" / f"r{rnd}"
    brief = load(run / "brief.json")
    stop_rule = {**DEFAULT_STOP, **brief.get("stopRule", {})}
    mapping = load(rdir / "mapping.json")
    letters = sorted(mapping)
    targets = [l for l in letters if mapping[l]["kind"] == "target"]
    if len(targets) != 1:
        sys.exit(f"mapping.json must contain exactly one target page, found {targets}")
    target = targets[0]
    roles = {j["id"]: j for j in brief.get("judges", [])}

    # Every judge in the brief must have exactly one valid file; nothing else counts.
    jdir = Path(load(rdir / "round.json")["judgeDir"]) / "judgments"
    archive = rdir / "judges"
    archive.mkdir(exist_ok=True)
    judges, invalid = [], {}
    for jid in sorted(roles):
        f = jdir / f"{jid}.json"
        if not f.exists():
            invalid[f.name] = ["missing — this judge has not written its file"]
            continue
        shutil.copyfile(f, archive / f.name)
        try:
            j = load(f)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            invalid[f.name] = [f"not valid JSON: {e}"]
            continue
        errs = validate(j, letters)
        if errs:
            invalid[f.name] = errs
        else:
            j["judge"] = jid
            judges.append(j)
    slop_cfg = {**DEFAULT_SLOP, **(brief.get("slop") or {})}
    slop_raw = None
    slop_from = load(rdir / "round.json").get("slopFrom")
    if slop_cfg["enabled"] and not slop_from:
        f = jdir / "slop.json"
        if not f.exists():
            invalid["slop.json"] = ["missing — the slop judge has not written its file"]
        else:
            shutil.copyfile(f, archive / f.name)
            try:
                slop_raw = load(f)
                errs = validate_slop(slop_raw, letters)
                if errs:
                    invalid["slop.json"] = errs
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                invalid["slop.json"] = [f"not valid JSON: {e}"]
    if not roles:
        sys.exit("brief.json has no judges")
    if invalid:
        print(json.dumps({"round": rnd, "valid": False, "invalid": invalid or {"*": ["no judge files"]}}))
        sys.exit(3)

    n = len(letters)
    pages = {}
    for l in letters:
        scores = {d: round(mean(j["pages"][l][d] for j in judges), 2) for d in DIMS}
        ranks = [j["ranking"].index(l) + 1 for j in judges]
        pages[l] = {
            **mapping[l],
            "label": label(mapping[l], brief),
            "scores": scores,
            "avg": round(mean(scores.values()), 2),
            "firstVotes": sum(r == 1 for r in ranks),
            "meanRank": round(mean(ranks), 2),
            "borda": sum(n - r for r in ranks),
        }

    comps = [l for l in letters if l != target]
    # "Leads" = beats EVERY competitor's mean on that dimension (i.e. the per-dimension max).
    best_comp = {d: max(pages[c]["scores"][d] for c in comps) for d in DIMS} if comps else {d: 0 for d in DIMS}
    leads = {d: pages[target]["scores"][d] > best_comp[d] for d in DIMS}
    # Judge means drift ~1 point between rounds, so "close enough" counts: behind by at most
    # `tolerance` on a dimension still passes it. tolerance 0 means a strict lead (ties fail).
    tol = stop_rule["tolerance"]
    ok = {d: leads[d] or (tol > 0 and round(pages[target]["scores"][d] - best_comp[d], 2) >= -tol) for d in DIMS}
    first = pages[target]["firstVotes"]
    standings = sorted(letters, key=lambda l: (-pages[l]["firstVotes"], pages[l]["meanRank"], -pages[l]["avg"]))

    overlays = {}
    for j in judges:
        for l in letters:
            p = j["pages"][l]
            if p.get("overlay") is True:
                overlays.setdefault(pages[l]["label"], []).append(f'{j["judge"]}: {p.get("overlay_note") or "overlay reported"}')
    # A re-shoot is worth it only if 2+ judges saw the same overlay, and only once per round:
    # if it's still there after a re-shoot, take the scores as they are (logged in tally.json).
    already_reshot = (run / "rounds" / f"r{rnd}.reshot").exists()
    needs_reshoot = not already_reshot and any(len(v) >= 2 for v in overlays.values())

    buyers_passed = first >= stop_rule["minFirstVotes"] and (all(ok.values()) or not stop_rule["leadAllDims"])
    blocked = [d for d in DIMS if not ok[d]]

    # Slop gate: the design agent may not make the page more generic than the original.
    slop = None
    if slop_from:
        # Confirmation round: same version, so reuse the earlier slop result.
        slop = {**load(run / "rounds" / f"r{slop_from}" / "tally.json")["slop"], "reusedFrom": slop_from}
    if slop_raw:
        by_page = {l: {**{d: slop_raw["pages"][l][d] for d in SLOP_DIMS},
                       "score": round(mean(slop_raw["pages"][l][d] for d in SLOP_DIMS), 2)} for l in letters}
        score = by_page[target]["score"]
        baseline = score if mapping[target]["id"] == "v0" else slop_baseline(run, rnd)
        gate_min = slop_cfg["floor"] if baseline is None else max(slop_cfg["floor"], round(baseline - slop_cfg["maxDrop"], 2))
        slop = {"target": score, "baseline": baseline, "min": gate_min, "gatePassed": score >= gate_min,
                "pages": {pages[l]["label"]: by_page[l] for l in letters}}
    passed = buyers_passed and (slop is None or slop["gatePassed"])
    # Count the consecutive earlier rounds where this same version also passed.
    confirmations = 0
    if passed:
        for prev in range(rnd - 1, 0, -1):
            pt = run / "rounds" / f"r{prev}" / "tally.json"
            if not pt.exists():
                break
            p = load(pt)
            if (p.get("targetVersion") != mapping[target]["id"] or p.get("verdict") == "reshoot"
                    or not p.get("passed", p.get("verdict") == "winner")):
                break
            confirmations += 1
    capped = rnd >= stop_rule["maxRounds"]
    # Plateau: none of the last N rounds beat the best target score from before them.
    history = [load(run / "rounds" / f"r{i}" / "tally.json") for i in range(1, rnd)
               if (run / "rounds" / f"r{i}" / "tally.json").exists()]
    avgs = [h["pages"][h["target"]]["avg"] for h in history if h.get("verdict") != "reshoot"] + [pages[target]["avg"]]
    n = stop_rule["plateauRounds"]
    # A failed confirmation round re-judged an unchanged page, so it says nothing about whether design
    # has stopped improving: redesign instead of stopping.
    rejudge = (bool(history) and history[-1].get("passed")
               and history[-1].get("targetVersion") == mapping[target]["id"])
    plateau = bool(n) and not rejudge and len(avgs) > n and max(avgs[-n:]) <= max(avgs[:-n])
    # Needs input: the page wins the vote and holds the slop gate, but keeps trailing only on
    # offer/value while its TODO.md lists missing facts. More design rounds won't close that gap.
    def fact_blocked(t, blocked_dims):
        return (t["firstVotes"] >= stop_rule["minFirstVotes"] and bool(blocked_dims)
                and set(blocked_dims) <= FACT_DIMS and (t.get("slop") or {}).get("gatePassed", True))
    streak = 0
    if fact_blocked({"firstVotes": first, "slop": slop}, blocked):
        streak = 1
        for h in reversed([h for h in history if h.get("verdict") != "reshoot"]):
            if not fact_blocked(h, h.get("blockedDims", [d for d in DIMS if not h["leads"][d]])):
                break
            streak += 1
    needs_input = (not passed and bool(stop_rule["inputRounds"]) and streak >= stop_rule["inputRounds"]
                   and (run / "site" / mapping[target]["id"] / "TODO.md").exists())
    if needs_reshoot:
        verdict = "reshoot"
    elif needs_input:
        verdict = "needs-input"
    elif not passed and plateau and not capped:
        verdict = "plateau"
    elif passed and confirmations >= stop_rule["confirmRounds"]:
        verdict = "winner"
    elif capped:
        verdict = "round-cap"
    else:
        verdict = "confirm" if passed else "continue"

    tally = {
        "round": rnd,
        "valid": True,
        "judges": len(judges),
        "target": target,
        "targetVersion": mapping[target]["id"],
        "firstVotes": first,
        "leads": leads,
        "withinTolerance": ok,
        "blockedDims": blocked,
        "bestCompetitor": best_comp,
        "standings": [pages[l]["label"] for l in standings],
        "pages": pages,
        "stopRule": stop_rule,
        "buyersPassed": buyers_passed,
        "slop": slop,
        "passed": passed,
        "overlays": overlays,
        "confirmations": confirmations,
        "verdict": verdict,
        "stop": verdict in ("winner", "round-cap", "plateau", "needs-input"),
    }
    (rdir / "tally.json").write_text(json.dumps(tally, indent=2), encoding="utf-8")
    (rdir / "feedback.md").write_text(feedback(rnd, tally, judges, roles, mapping, brief, slop_raw), encoding="utf-8")
    print(json.dumps({k: tally[k] for k in ("round", "valid", "targetVersion", "firstVotes", "leads", "blockedDims", "standings", "slop", "overlays", "passed", "verdict", "stop")}))


def feedback(rnd, t, judges, roles, mapping, brief, slop_raw=None):
    tl = t["target"]
    tp = t["pages"][tl]
    out = [f"# Round {rnd} feedback — {tp['label']}", ""]
    out.append(f"First-place votes: **{t['firstVotes']}/{t['judges']}** (need {t['stopRule']['minFirstVotes']}). "
               f"Standings: {' > '.join(t['standings'])}.")
    out.append("")
    out.append("| Dimension | Your page | Best competitor | Lead? |")
    out.append("|---|---|---|---|")
    for d in DIMS:
        lead = "yes" if t["leads"][d] else (f"close (within {t['stopRule']['tolerance']})" if t["withinTolerance"][d] else "**no**")
        out.append(f"| {d} | {tp['scores'][d]} | {t['bestCompetitor'][d]} | {lead} |")
    out.append("")

    out.append("## What judges said about YOUR page")
    for j in judges:
        role = roles.get(j["judge"], {})
        p = j["pages"][tl]
        rank = j["ranking"].index(tl) + 1
        # Role only: full titles/personas would let the designer write to the panel.
        out.append(f"### {j['judge']} — {role.get('role', '?')} (ranked you #{rank})")
        if p.get("first_impression"):
            out.append(f"- First impression: {p['first_impression']}")
        for c in p.get("confusions", []):
            out.append(f"- Confused: {c}")
        for c in p.get("concerns", []):
            out.append(f"- Concern: {c}")
        if p.get("next_action"):
            out.append(f"- Would do next: {p['next_action']}")
        out.append("")

    if slop_raw:
        # Findings only, no numeric score or threshold: the designer should fix the page,
        # not optimize a number.
        sp = slop_raw["pages"][tl]
        out.append("## Generic / template-like elements on YOUR page (slop review)")
        if not t["slop"]["gatePassed"]:
            sl = t["slop"]
            if t["targetVersion"] == "v0" or sl["baseline"] is None or sl["target"] >= sl["baseline"]:
                out.append("**This page reads as too generic to win as it stands (below the slop floor). The "
                           "redesign must make it more specific, whatever the buyer scores.**")
            else:
                out.append("**This version reads as more generic than the original. Fixing this is required "
                           "before it can win, whatever the buyer scores.**")
        out += [f"- {ev}" for ev in sp.get("evidence", [])]
        if sp.get("most_specific"):
            out.append(f"- Most specific thing on the page (keep / build on): {sp['most_specific']}")
        if sp.get("fix_first"):
            out.append(f"- Fix first: {sp['fix_first']}")
        out.append("")

    out.append("## What judges liked about pages they ranked above yours")
    for j in judges:
        above = j["ranking"][: j["ranking"].index(tl)]
        for l in above:
            p = j["pages"][l]
            bits = [p.get("first_impression", ""), p.get("strengths", "")]
            bits = [b if isinstance(b, str) else "; ".join(b) for b in bits if b]
            if bits:
                out.append(f"- **{t['pages'][l]['label']}** (per {j['judge']}): {' — '.join(bits)}")
    out.append("")
    out.append("## Judges' ranking rationales")
    for j in judges:
        if j.get("rationale"):
            text = j["rationale"]
            for l in mapping:  # de-anonymize letters in free text
                text = text.replace(f"Page {l}", t["pages"][l]["label"]).replace(f"page {l}", t["pages"][l]["label"])
            out.append(f"- {j['judge']}: {text}")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    main()
