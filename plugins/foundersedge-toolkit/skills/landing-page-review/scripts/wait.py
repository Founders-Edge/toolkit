#!/usr/bin/env python3
"""Wait for background sub-agents to finish, with a time limit, so a stalled agent can't hang the run.

  python3 wait.py RUN_DIR judges ROUND     every judge file (and slop.json, if spawned) for round N
  python3 wait.py RUN_DIR designer vN      the design agent's site/vN/.done marker
  add --extend MIN to give an agent more time after you nudged it

Limits come from brief.json "timeouts" (minutes): judges 5, designer 12 by default. They were
set from test runs: a whole judging round took 1.5 min median (4 max), and a design
pass 2–5 min, while the stalled agents ran past 30 min.

The clock starts on the first call and is kept in RUN_DIR/.waits/, so you can call again after
"waiting". Each call waits at most 8 minutes, which keeps it under the Bash tool's 10-minute cap.

Prints one JSON line. Exit 0 = done, 3 = some judge files are invalid (re-spawn those judges with
the errors), 4 = timed out (see "missing"), 5 = still waiting (call again). Standard library only.
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tally import DEFAULT_SLOP, load, validate, validate_slop  # noqa: E402

DEFAULT_TIMEOUTS = {"judges": 5, "designer": 12}
MAX_CALL = 8 * 60
POLL = 5


def judge_status(run, rnd):
    """Return (missing, invalid) for one round's judge files."""
    rdir = run / "rounds" / f"r{rnd}"
    brief = load(run / "brief.json")
    letters = sorted(load(rdir / "mapping.json"))
    round_info = load(rdir / "round.json")
    jdir = Path(round_info["judgeDir"]) / "judgments"
    expected = {j["id"]: validate for j in brief.get("judges", [])}
    if {**DEFAULT_SLOP, **(brief.get("slop") or {})}["enabled"] and not round_info.get("slopFrom"):
        expected["slop"] = validate_slop
    missing, invalid = [], {}
    for name, check in expected.items():
        f = jdir / f"{name}.json"
        if not f.exists():
            missing.append(name)
            continue
        try:
            errs = check(load(f), letters)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            errs = [f"not valid JSON: {e}"]
        if errs:
            invalid[name] = errs
    return missing, invalid


def main():
    argv = sys.argv[1:]
    extend = 0.0
    if "--extend" in argv:
        i = argv.index("--extend")
        extend = float(argv[i + 1])
        del argv[i:i + 2]
    if len(argv) != 3 or argv[1] not in DEFAULT_TIMEOUTS:
        sys.exit(__doc__)
    run, kind, which = Path(argv[0]), argv[1], argv[2]
    brief = load(run / "brief.json")
    limit = {**DEFAULT_TIMEOUTS, **(brief.get("timeouts") or {})}[kind] * 60

    waits = run / ".waits"
    waits.mkdir(exist_ok=True)
    key = which
    if kind == "judges":  # a redone round (after a reshoot) gets a new judge folder and a fresh clock
        key += "-" + Path(load(run / "rounds" / f"r{which}" / "round.json")["judgeDir"]).name
    clock = waits / f"{kind}-{key}.json"
    state = load(clock) if clock.exists() else {"start": time.time(), "extra": 0}
    state["extra"] += extend * 60
    clock.write_text(json.dumps(state))
    deadline = state["start"] + limit + state["extra"]
    call_end = time.time() + MAX_CALL

    while True:
        if kind == "judges":
            missing, invalid = judge_status(run, int(which))
        else:
            missing, invalid = ([] if (run / "site" / which / ".done").exists() else [which]), {}
        elapsed = round((time.time() - state["start"]) / 60, 1)
        out = {"kind": kind, "which": which, "elapsedMin": elapsed, "missing": missing, "invalid": invalid}
        if not missing:
            status, code = ("invalid", 3) if invalid else ("done", 0)
        elif time.time() >= deadline:
            status, code = "timeout", 4
        elif time.time() >= call_end:
            status, code = "waiting", 5
        else:
            time.sleep(POLL)
            continue
        print(json.dumps({"status": status, **out}))
        sys.exit(code)


if __name__ == "__main__":
    main()
