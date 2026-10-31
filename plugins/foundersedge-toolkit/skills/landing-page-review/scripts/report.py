#!/usr/bin/env python3
"""Build RUN_DIR/report.html from every tallied round.

  python3 report.py RUN_DIR

Shows the verdict, per-round score progression vs. the best competitor,
before/after screenshots, each version's changelog, and the concerns judges
still raised in the final round. Image paths are relative, so open the file
from inside the run folder. Standard library only.
"""
import html
import json
import sys
from pathlib import Path

DIMS = ["clarity", "offer", "value", "professionalism"]
e = html.escape


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def chart(rounds):
    """Inline SVG: your page's avg score vs best competitor avg, per round."""
    if not rounds:
        return ""
    W, H, P = 560, 220, 36
    xs = lambda i: P + (W - 2 * P) * (i / max(1, len(rounds) - 1))
    ys = lambda v: H - P - (H - 2 * P) * ((v - 1) / 9)
    you = [r["pages"][r["target"]]["avg"] for r in rounds]
    comp = [max([p["avg"] for l, p in r["pages"].items() if l != r["target"]] or [0]) for r in rounds]

    def line(vals, cls):
        pts = " ".join(f"{xs(i):.1f},{ys(v):.1f}" for i, v in enumerate(vals))
        dots = "".join(f'<circle cx="{xs(i):.1f}" cy="{ys(v):.1f}" r="4" class="{cls}"><title>{v}</title></circle>' for i, v in enumerate(vals))
        return f'<polyline points="{pts}" class="{cls}" fill="none" stroke-width="2.5"/>{dots}'

    grid = "".join(f'<line x1="{P}" x2="{W - P}" y1="{ys(v):.1f}" y2="{ys(v):.1f}" class="grid"/>'
                   f'<text x="{P - 8}" y="{ys(v) + 4:.1f}" text-anchor="end" class="axis">{v}</text>' for v in (2, 4, 6, 8, 10))
    labels = "".join(f'<text x="{xs(i):.1f}" y="{H - 10}" text-anchor="middle" class="axis">R{r["round"]}</text>' for i, r in enumerate(rounds))
    return (f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Average rubric score by round">{grid}{labels}'
            f'{line(comp, "comp")}{line(you, "you")}</svg>'
            '<p class="legend"><span class="sw you"></span>Your page <span class="sw comp"></span>Best competitor (avg of 4 dimensions)</p>')


def shots(run, version, kind):
    d = run / "shots" / "target"
    return sorted(p.relative_to(run).as_posix() for p in d.glob(f"{version}-{kind}-*.png"))


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    run = Path(sys.argv[1])
    brief = load(run / "brief.json")
    rdirs = sorted((p for p in (run / "rounds").glob("r*") if p.name[1:].isdigit()), key=lambda p: int(p.name[1:]))
    rounds = [load(r / "tally.json") for r in rdirs if (r / "tally.json").exists()]
    if not rounds:
        sys.exit("no tallied rounds yet")
    last = rounds[-1]
    first_v, last_v = rounds[0]["targetVersion"], last["targetVersion"]
    # At the round cap the last version isn't necessarily the best one.
    # Ties break on how many dimensions the page held, then on the buyer average.
    held = lambda r: sum((r.get("withinTolerance") or r["leads"]).values())
    best = max(rounds, key=lambda r: (r["firstVotes"], held(r), r["pages"][r["target"]]["avg"]))
    best_v = best["targetVersion"]

    verdict = {
        "winner": f"Clear winner: {last['firstVotes']}/{last['judges']} judges ranked your page #1 and it leads"
                  f"{' (or is within ' + str(last['stopRule']['tolerance']) + ' of)' if last['stopRule'].get('tolerance') else ''} every dimension"
                  f" — confirmed across {last.get('confirmations', 0) + 1} independent rounds.",
        "plateau": f"Stopped early: scores stopped improving for {last['stopRule'].get('plateauRounds', 2)} rounds. "
                   f"Best-scoring version: {best_v} (round {best['round']}, {best['firstVotes']}/{best['judges']} first-place votes) — site/{best_v}/index.html.",
        "needs-input": f"Stopped: your page wins the vote ({last['firstVotes']}/{last['judges']} first-place votes) but keeps trailing on "
                       f"{' and '.join(last.get('blockedDims', []))}, which needs facts only you can supply (see Needs your input below), "
                       f"not more design. Best version so far: {last_v} — site/{last_v}/index.html.",
        "reshoot": f"Round {last['round']} needs a re-shoot: judges saw an overlay covering {', '.join(last.get('overlays', {}))}.",
        "confirm": f"Passed in round {last['round']} ({last['firstVotes']}/{last['judges']} first-place votes), awaiting a confirmation round.",
        "round-cap": f"Stopped at the round cap ({last['stopRule']['maxRounds']}). Your page got {last['firstVotes']}/{last['judges']} first-place votes in the last round. "
                     f"Best-scoring version: {best_v} (round {best['round']}, {best['firstVotes']}/{best['judges']} first-place votes) — site/{best_v}/index.html.",
        "continue": f"In progress: {last['firstVotes']}/{last['judges']} first-place votes after round {last['round']}.",
    }[last["verdict"]]

    slop_note = ""
    if any(r.get("slop") for r in rounds):
        slop_note = ('<p class="sub">Slop check: a separate judge scores how specific vs. generic/template-like each page is '
                     '(copy, visual, proof; 10 = least generic). A version can only win if it stays at or above the minimum shown: '
                     'the floor, or the original page\'s score minus the allowed drop.</p>')
        sp = last.get("slop") or {}
        if sp:
            slop_note += ('<div class="wrap"><table><tr><th>Page</th><th>copy</th><th>visual</th><th>proof</th><th>slop score</th></tr>' +
                          "".join(f"<tr><td>{e(k)}</td><td>{v['copy']}</td><td>{v['visual']}</td><td>{v['proof']}</td><td>{v['score']}</td></tr>"
                                  for k, v in sorted(sp["pages"].items(), key=lambda kv: -kv[1]["score"])) + "</table></div>")
    rows = []
    for r in rounds:
        tp = r["pages"][r["target"]]
        cells = "".join(
            f'<td class="{"lead" if r["leads"][d] else "lag"}">{tp["scores"][d]}<small> vs {r["bestCompetitor"][d]}</small></td>' for d in DIMS)
        sl = r.get("slop")
        slop_cell = (f'<td class="{"lead" if sl["gatePassed"] else "lag"}">{sl["target"]}<small> min {sl["min"]}</small></td>'
                     if sl else "<td>—</td>")
        rows.append(f'<tr><td>R{r["round"]}</td><td>{e(r["targetVersion"])}</td><td><b>{r["firstVotes"]}</b>/{r["judges"]}</td>'
                    f'{cells}{slop_cell}<td>{e(" › ".join(r["standings"]))}</td></tr>')

    # Judges score relative to the lineup, so unchanged competitors still move between
    # rounds. Show each competitor's avg range across rounds as a noise gauge.
    def drift(p):
        if p["kind"] == "target":
            return "—"
        avgs = [pg["avg"] for r in rounds for pg in r["pages"].values() if pg["kind"] == "competitor" and pg["id"] == p["id"]]
        return f"{min(avgs)}–{max(avgs)}" if len(avgs) > 1 else "—"

    standings = "".join(
        f'<tr><td>{e(p["label"])}</td>' + "".join(f"<td>{p['scores'][d]}</td>" for d in DIMS) +
        f'<td>{p["avg"]}</td><td>{p["firstVotes"]}</td><td>{p["meanRank"]}</td><td>{drift(p)}</td></tr>'
        for p in sorted(last["pages"].values(), key=lambda p: (-p["firstVotes"], p["meanRank"])))

    def gallery(kind):
        before, after = shots(run, first_v, kind), shots(run, last_v, kind)
        if not before and not after:
            return ""
        col = lambda title, imgs: f'<figure><figcaption>{e(title)}</figcaption>' + "".join(f'<img src="{e(i)}" loading="lazy" alt="">' for i in imgs) + "</figure>"
        return f'<div class="ba {kind}">{col("Before · " + first_v, before)}{col("After · " + last_v, after)}</div>'

    changelogs = []
    for v in sorted((run / "site").glob("v*"), key=lambda p: int(p.name[1:]) if p.name[1:].isdigit() else 0):
        cl = v / "CHANGELOG.md"
        if cl.exists():
            changelogs.append(f'<details><summary>{e(v.name)}</summary><pre>{e(cl.read_text(encoding="utf-8"))}</pre></details>')

    todos = run / "site" / last_v / "TODO.md"
    todo_html = f'<h2>Needs your input</h2><pre>{e(todos.read_text(encoding="utf-8"))}</pre>' if todos.exists() else ""

    fb = run / "rounds" / f"r{last['round']}" / "feedback.md"
    comps = "".join(f'<li><b>{e(c["name"])}</b> — <a href="{e(c["url"])}">{e(c["url"])}</a>{" · " + e(c.get("why", "")) if c.get("why") else ""}</li>'
                    for c in brief.get("competitors", []))
    judges = "".join(f'<li><b>{e(j["id"])}</b> · {e(j.get("role", ""))} · {e(j.get("title", ""))}</li>' for j in brief.get("judges", []))

    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Landing Page Review</title>
<style>
:root{{--bg:#fafaf9;--fg:#1c1917;--muted:#78716c;--line:#e7e5e4;--card:#fff;--you:#2563eb;--comp:#a8a29e;--good:#15803d;--bad:#b91c1c}}
@media (prefers-color-scheme:dark){{:root{{--bg:#0c0a09;--fg:#f5f5f4;--muted:#a8a29e;--line:#292524;--card:#1c1917;--you:#60a5fa;--comp:#78716c;--good:#4ade80;--bad:#f87171}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 -apple-system,system-ui,sans-serif}}
main{{max-width:1100px;margin:0 auto;padding:32px 16px 80px}}h1{{margin:0 0 4px;font-size:28px}}h2{{margin:40px 0 12px;font-size:19px}}
.sub{{color:var(--muted);margin:0}}.verdict{{margin:20px 0;padding:16px 18px;border-radius:10px;background:var(--card);border:1px solid var(--line);font-weight:600}}
.verdict.winner{{border-color:var(--good)}}.wrap{{overflow-x:auto}}table{{border-collapse:collapse;width:100%;background:var(--card)}}
th,td{{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left;white-space:nowrap}}th{{font-size:12px;text-transform:uppercase;color:var(--muted)}}
td small{{color:var(--muted)}}td.lead{{color:var(--good);font-weight:600}}td.lag{{color:var(--bad)}}
svg{{width:100%;max-width:560px;height:auto}}.grid{{stroke:var(--line)}}.axis{{fill:var(--muted);font-size:11px}}
polyline.you{{stroke:var(--you)}}polyline.comp{{stroke:var(--comp);stroke-dasharray:5 4}}circle.you{{fill:var(--you)}}circle.comp{{fill:var(--comp)}}
.legend{{color:var(--muted);font-size:13px}}.sw{{display:inline-block;width:12px;height:12px;border-radius:2px;margin:0 4px 0 12px;vertical-align:-1px}}.sw.you{{background:var(--you)}}.sw.comp{{background:var(--comp)}}
.ba{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}.ba.mobile{{max-width:560px}}figure{{margin:0}}figcaption{{font-weight:600;margin-bottom:6px}}
figure img{{display:block;width:100%;border:1px solid var(--line)}}pre{{white-space:pre-wrap;background:var(--card);border:1px solid var(--line);padding:12px;border-radius:8px;font-size:13px}}
details{{margin:6px 0}}summary{{cursor:pointer;font-weight:600}}a{{color:var(--you)}}
@media (max-width:640px){{.ba{{grid-template-columns:1fr}}}}
</style></head><body><main>
<h1>Landing Page Review — {e(brief.get("target", {}).get("name", ""))}</h1>
<p class="sub">{e(brief.get("target", {}).get("url", ""))} · ICP: {e(brief.get("icp", ""))}</p>
<p class="sub">Use case: {e(brief.get("useCase", ""))}</p>
<div class="verdict {last["verdict"]}">{e(verdict)}</div>

<h2>Score progression</h2>
{chart(rounds)}
<div class="wrap"><table><tr><th>Round</th><th>Version</th><th>#1 votes</th>{"".join(f"<th>{d}</th>" for d in DIMS)}<th>Slop check</th><th>Standings</th></tr>{"".join(rows)}</table></div>

{slop_note}
<h2>Final standings (round {last["round"]})</h2>
<div class="wrap"><table><tr><th>Page</th>{"".join(f"<th>{d}</th>" for d in DIMS)}<th>Avg</th><th>#1 votes</th><th>Mean rank</th><th>Avg range, all rounds</th></tr>{standings}</table></div>
<p class="sub">Scores are relative to the lineup: judges see every page side by side, so competitor scores move between rounds even though their pages never change. The range column shows how much. Treat gaps smaller than that as noise.</p>

<h2>Before / after — desktop</h2>{gallery("desktop")}
<h2>Before / after — mobile</h2>{gallery("mobile")}
{todo_html}
<h2>What changed each version</h2>{"".join(changelogs) or "<p class='sub'>No iterations yet.</p>"}
<h2>Final-round judge feedback</h2><pre>{e(fb.read_text(encoding="utf-8")) if fb.exists() else ""}</pre>
<h2>Panel &amp; field</h2><ul>{judges}</ul><ul>{comps}</ul>
</main></body></html>
"""
    out = run / "report.html"
    out.write_text(page, encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
