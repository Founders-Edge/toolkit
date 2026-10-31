"""Tests for new_round.py / tally.py / report.py / wait.py.   Run: python3 tests/test_scripts.py"""
import json
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
DIMS = ["clarity", "offer", "value", "professionalism"]


def tiny_png(path):
    def chunk(t, b):
        return struct.pack(">I", len(b)) + t + b + struct.pack(">I", zlib.crc32(t + b) & 0xFFFFFFFF)
    raw = b"\x00" + b"\xff\xff\xff" * 4
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 4, 1, 8, 2, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def prompt_path(out, key):
    line = out["spawn"][key]
    assert line.startswith("Read ") and line.endswith(" and follow its instructions exactly."), line
    return Path(line[len("Read "):-len(" and follow its instructions exactly.")])


def run(script, *args):
    return subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, args)], capture_output=True, text=True)


class Base(unittest.TestCase):
    STOP = {"minFirstVotes": 4, "leadAllDims": True, "confirmRounds": 1, "maxRounds": 4}

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.dir = self.root / "acme-20261024"
        self.dir.mkdir()
        self.outdirs = {}
        self.brief = {
            "icp": "RevOps leads", "target": {"name": "Acme", "url": "https://acme.test"}, "useCase": "Acme cleans CRM data",
            "judgeUseCase": "a tool that keeps CRM data clean without manual work",
            "competitors": [{"id": "alpha", "name": "Alpha", "url": "https://alpha.test"},
                            {"id": "beta", "name": "Beta", "url": "https://beta.test"}],
            "judges": [{"id": f"j{i}", "role": r, "title": f"Title {i}", "persona": f"Persona {i}."} for i, r in
                       enumerate(["Buyer", "Buyer", "Influencer", "Influencer", "Decision maker"], 1)],
            "stopRule": self.STOP,
        }
        self.save_brief()
        for sub, stem, nd in [("target", "v0", 2), ("target", "v1", 4), ("competitors", "alpha", 4), ("competitors", "beta", 1)]:
            d = self.dir / "shots" / sub
            d.mkdir(parents=True, exist_ok=True)
            for kind, n in [("desktop", nd), ("mobile", 1)]:
                for i in range(1, n + 1):
                    tiny_png(d / f"{stem}-{kind}-{i:02d}.png")

    def save_brief(self):
        (self.dir / "brief.json").write_text(json.dumps(self.brief))

    def tearDown(self):
        shutil.rmtree(self.root)
        for d in self.outdirs.values():
            shutil.rmtree(d.parent, ignore_errors=True)

    def new_round(self, r, v):
        p = run("new_round.py", self.dir, r, v)
        self.assertEqual(p.returncode, 0, p.stderr)
        out = json.loads(p.stdout)
        self.outdirs[r] = Path(out["outDir"])
        mapping = json.loads((self.dir / "rounds" / f"r{r}" / "mapping.json").read_text())
        return out, mapping

    def judge(self, r, mapping, target_first, target_score, comp_score=6):
        tl = next(l for l, m in mapping.items() if m["kind"] == "target")
        others = [l for l in mapping if l != tl]
        for i in range(1, 6):
            pages = {l: {**{d: (target_score if l == tl else comp_score) for d in DIMS},
                         "first_impression": f"imp {l}", "strengths": f"str {l}",
                         "confusions": [f"conf {l}"], "concerns": [f"conc {l}"], "next_action": "demo"} for l in mapping}
            ranking = [tl] + others if i <= target_first else others + [tl]
            j = {"judge": f"j{i}", "pages": pages, "ranking": ranking, "rationale": f"Page {tl} vs page {others[0]}"}
            (self.outdirs[r] / f"j{i}.json").write_text(json.dumps(j))
        return tl

    def round(self, r, v, target_first, target_score, comp_score=6):
        _, m = self.new_round(r, v)
        self.judge(r, m, target_first, target_score, comp_score)
        p = run("tally.py", self.dir, r)
        self.assertEqual(p.returncode, 0, p.stderr)
        return json.loads(p.stdout)


class NewRound(Base):
    def test_blinding_and_rendered_prompts(self):
        out, mapping = self.new_round(1, "v0")
        jd = Path(out["judgeDir"])
        self.assertNotIn("acme", str(jd).lower())
        self.assertEqual([p.name for p in jd.iterdir() if p.is_dir()], ["judgments"])
        self.assertEqual(sorted(out["spawn"]), [f"j{i}" for i in range(1, 6)])
        for jid in out["spawn"]:
            path = prompt_path(out, jid)
            self.assertEqual(path.parent, jd)                   # prompt lives in the neutral folder
            self.assertTrue((self.dir / "rounds/r1/prompts" / f"{jid}.md").exists())  # archive copy
            text = path.read_text()
            self.assertNotIn("{{", text)
            self.assertNotIn("acme", text.lower())               # no client name / run path
            self.assertNotIn(str(self.dir), text)
            self.assertIn(f"Persona {jid[1:]}.", text)
            self.assertIn(str(jd / "judgments" / f"{jid}.json"), text)
            self.assertIn("| **clarity** |", text)               # rubric pulled from judges.md
            self.assertIn('"ranking"', text)                     # schema pulled from judges.md
            for letter in mapping:
                self.assertIn(f"Page {letter}:", text)
        # alpha + v1 have 4 desktop tiles (the cap) -> flagged; beta (1 tile) is not
        text = prompt_path(out, "j1").read_text()
        alpha = next(l for l, m in mapping.items() if m["id"] == "alpha")
        beta = next(l for l, m in mapping.items() if m["id"] == "beta")
        self.assertIn(f"Page {alpha}:\n  desktop (continues below the last tile):", text)
        self.assertIn(f"Page {beta}:\n  desktop:", text)

    def test_sidecar_overrides_tile_count(self):
        # v1 has 4 desktop tiles (the cap) but its sidecar says the page ended there
        (self.dir / "shots/target/v1-desktop.json").write_text(json.dumps({"truncated": False}))
        (self.dir / "shots/competitors/beta-desktop.json").write_text(json.dumps({"truncated": True}))
        out, mapping = self.new_round(1, "v1")
        text = prompt_path(out, "j1").read_text()
        tl = next(l for l, m in mapping.items() if m["kind"] == "target")
        beta = next(l for l, m in mapping.items() if m["id"] == "beta")
        self.assertIn(f"Page {tl}:\n  desktop:", text)
        self.assertIn(f"Page {beta}:\n  desktop (continues below the last tile):", text)

    def test_one_page_at_a_time_instruction(self):
        out, _ = self.new_round(1, "v0")
        self.assertIn("ONE PAGE AT A TIME", prompt_path(out, "j3").read_text())

    def test_refuses_client_name_in_judge_use_case(self):
        self.brief["judgeUseCase"] = "Acme's CRM cleaner"
        self.save_brief()
        p = run("new_round.py", self.dir, 1, "v0")
        self.assertNotEqual(p.returncode, 0)
        self.assertFalse((self.dir / "rounds" / "r1").exists())

    def test_leak_check_covers_personas_whole_words(self):
        self.brief["judges"][2]["persona"] = "Was pitched by Acme last year."
        self.save_brief()
        p = run("new_round.py", self.dir, 1, "v0")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("j3.persona", p.stderr)
        self.brief["judges"][2]["persona"] = "Hates vendors like Acmetronics and their search tools."
        self.save_brief()
        self.assertEqual(run("new_round.py", self.dir, 1, "v0").returncode, 0)   # no whole-word hit

    def test_requires_judge_use_case(self):
        del self.brief["judgeUseCase"]
        self.save_brief()
        self.assertNotEqual(run("new_round.py", self.dir, 1, "v0").returncode, 0)

    def test_no_reshuffle_and_missing_shots(self):
        self.new_round(1, "v0")
        self.assertNotEqual(run("new_round.py", self.dir, 1, "v0").returncode, 0)
        self.assertNotEqual(run("new_round.py", self.dir, 2, "v9").returncode, 0)


class Tally(Base):
    def test_pass_needs_confirmation_then_wins(self):
        t = self.round(1, "v0", target_first=5, target_score=9)
        self.assertEqual((t["passed"], t["verdict"], t["stop"]), (True, "confirm", False))
        t = self.round(2, "v0", target_first=4, target_score=9)
        self.assertEqual((t["verdict"], t["stop"]), ("winner", True))
        fb = (self.dir / "rounds/r2/feedback.md").read_text()
        self.assertNotIn("Title", fb)          # roles only for the designer
        self.assertIn("Decision maker", fb)

    def test_confirmation_must_be_same_version(self):
        self.round(1, "v0", target_first=5, target_score=9)
        t = self.round(2, "v1", target_first=5, target_score=9)
        self.assertEqual(t["verdict"], "confirm")

    def test_failed_confirmation_continues(self):
        self.round(1, "v0", target_first=5, target_score=9)
        t = self.round(2, "v0", target_first=2, target_score=9)
        self.assertEqual(t["verdict"], "continue")

    def test_confirm_rounds_zero_wins_immediately(self):
        self.brief["stopRule"] = {**self.STOP, "confirmRounds": 0}
        self.save_brief()
        self.assertEqual(self.round(1, "v0", target_first=4, target_score=9)["verdict"], "winner")

    def set_comp(self, r, m, dim, score):
        tl = next(l for l, x in m.items() if x["kind"] == "target")
        comp = next(l for l in m if l != tl)
        for f in self.outdirs[r].glob("j*.json"):
            j = json.loads(f.read_text()); j["pages"][comp][dim] = score; f.write_text(json.dumps(j))

    def test_tie_fails_with_zero_tolerance(self):
        self.brief["stopRule"] = {**self.STOP, "tolerance": 0}
        self.save_brief()
        _, m = self.new_round(1, "v0")
        self.judge(1, m, target_first=5, target_score=8)
        self.set_comp(1, m, "value", 8)
        t = json.loads(run("tally.py", self.dir, 1).stdout)
        self.assertEqual((t["passed"], t["verdict"]), (False, "continue"))
        self.assertFalse(t["leads"]["value"])

    def test_tolerance_passes_close_dims_only(self):
        _, m = self.new_round(1, "v0")                     # default tolerance 0.5
        self.judge(1, m, target_first=5, target_score=8)
        self.set_comp(1, m, "value", 8.4)                  # behind by 0.4: close enough
        t = json.loads(run("tally.py", self.dir, 1).stdout)
        self.assertEqual((t["passed"], t["blockedDims"]), (True, []))
        self.assertFalse(t["leads"]["value"])
        self.set_comp(1, m, "value", 8.8)                  # behind by 0.8: blocks
        t = json.loads(run("tally.py", self.dir, 1).stdout)
        self.assertEqual((t["passed"], t["blockedDims"]), (False, ["value"]))
        self.set_comp(1, m, "value", 8.4)
        run("tally.py", self.dir, 1)
        self.assertIn("close (within 0.5)", (self.dir / "rounds" / "r1" / "feedback.md").read_text())

    def test_needs_input_after_two_fact_blocked_rounds(self):
        for r, v in [(1, "v0"), (2, "v1")]:
            _, m = self.new_round(r, v)
            self.judge(r, m, target_first=5, target_score=8)
            self.set_comp(r, m, "offer", 9.5)
            if r == 2:
                (self.dir / "site" / "v1").mkdir(parents=True)
                (self.dir / "site" / "v1" / "TODO.md").write_text("- pricing\n")
            t = json.loads(run("tally.py", self.dir, r).stdout)
        self.assertEqual((t["verdict"], t["stop"], t["blockedDims"]), ("needs-input", True, ["offer"]))
        p = run("report.py", self.dir)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("facts only you can supply", (self.dir / "report.html").read_text())

    def test_no_needs_input_without_todo_or_on_clarity(self):
        for r, v in [(1, "v0"), (2, "v1")]:
            _, m = self.new_round(r, v)
            self.judge(r, m, target_first=5, target_score=8)
            self.set_comp(r, m, "offer", 9.5)
            t = json.loads(run("tally.py", self.dir, r).stdout)
        self.assertEqual(t["verdict"], "continue")          # no TODO.md: the designer has no missing facts
        (self.dir / "site" / "v1").mkdir(parents=True)
        (self.dir / "site" / "v1" / "TODO.md").write_text("- pricing\n")
        _, m = self.new_round(3, "v1")
        self.judge(3, m, target_first=5, target_score=8)
        self.set_comp(3, m, "clarity", 9.5)                 # clarity is the designer's job
        t = json.loads(run("tally.py", self.dir, 3).stdout)
        self.assertNotEqual(t["verdict"], "needs-input")

    def test_overlay_forces_reshoot(self):
        _, m = self.new_round(1, "v0")
        tl = self.judge(1, m, target_first=5, target_score=9)
        comp = next(l for l in m if l != tl)
        def flag(jid):
            f = self.outdirs[1] / f"{jid}.json"
            j = json.loads(f.read_text()); j["pages"][comp]["overlay"] = True; j["pages"][comp]["overlay_note"] = "cookie banner over hero"
            f.write_text(json.dumps(j))
        flag("j3")                                           # one judge: noted, not a reshoot
        t = json.loads(run("tally.py", self.dir, 1).stdout)
        self.assertNotEqual(t["verdict"], "reshoot")
        self.assertIn("j3: cookie banner over hero", list(t["overlays"].values())[0])
        flag("j4")                                           # two judges agree: reshoot
        t = json.loads(run("tally.py", self.dir, 1).stdout)
        self.assertEqual((t["verdict"], t["stop"]), ("reshoot", False))
        self.assertEqual(run("report.py", self.dir).returncode, 0)
        (self.dir / "rounds/r1.reshot").touch()              # already re-shot once: scores stand
        t = json.loads(run("tally.py", self.dir, 1).stdout)
        self.assertNotEqual(t["verdict"], "reshoot")

    def test_round_cap(self):
        for r in range(1, 5):
            t = self.round(r, "v0", target_first=1, target_score=5)
        self.assertEqual(t["verdict"], "round-cap")

    def test_missing_stray_invalid_and_utf8(self):
        _, m = self.new_round(1, "v0")
        self.judge(1, m, target_first=5, target_score=9)
        o = self.outdirs[1]
        (o / "j5.json").unlink()
        (o / "j1 copy.json").write_text((o / "j1.json").read_text())
        j = json.loads((o / "j2.json").read_text())
        j["ranking"] = j["ranking"][:-1]
        j["pages"][next(iter(j["pages"]))] = 5
        (o / "j2.json").write_text(json.dumps(j))
        j3 = json.loads((o / "j3.json").read_text()); j3["rationale"] = "“Page A” — great"
        (o / "j3.json").write_text(json.dumps(j3, ensure_ascii=False), encoding="utf-8")
        (o / "j4.json").write_text("{not json")
        p = run("tally.py", self.dir, 1)
        self.assertEqual(p.returncode, 3)
        self.assertEqual(sorted(json.loads(p.stdout)["invalid"]), ["j2.json", "j4.json", "j5.json"])


class Report(Base):
    def test_winner_report_with_drift(self):
        self.round(1, "v0", target_first=0, target_score=5, comp_score=7)
        self.round(2, "v1", target_first=5, target_score=9, comp_score=6)
        self.round(3, "v1", target_first=5, target_score=9, comp_score=5)
        (self.dir / "rounds/r2-old").mkdir()
        p = run("report.py", self.dir)
        self.assertEqual(p.returncode, 0, p.stderr)
        html = (self.dir / "report.html").read_text()
        self.assertIn("confirmed across 2 independent rounds", html)
        self.assertIn("<td>5–7</td>", html)             # competitor drift range
        self.assertIn("shots/target/v0-desktop-01.png", html)
        self.assertIn("shots/target/v1-mobile-01.png", html)

    def test_confirm_and_cap_reports(self):
        self.round(1, "v0", target_first=5, target_score=9)
        self.assertEqual(run("report.py", self.dir).returncode, 0)
        self.assertIn("awaiting a confirmation round", (self.dir / "report.html").read_text())
        for r, v, f in ((2, "v1", 0), (3, "v1", 0), (4, "v1", 0)):
            self.round(r, v, target_first=f, target_score=5)
        run("report.py", self.dir)
        self.assertIn("Best-scoring version: v0", (self.dir / "report.html").read_text())


class Slop(Base):
    def setUp(self):
        super().setUp()
        self.brief["slop"] = {"enabled": True, "floor": 5, "maxDrop": 2}
        self.brief["stopRule"] = {**self.STOP, "confirmRounds": 0}
        self.save_brief()

    def slop(self, r, mapping, target_score, comp_score=5):
        tl = next(l for l, m in mapping.items() if m["kind"] == "target")
        pages = {l: {"copy": target_score if l == tl else comp_score, "visual": target_score if l == tl else comp_score,
                     "proof": target_score if l == tl else comp_score,
                     "evidence": [f"copy: buzzwords on {l}"], "most_specific": f"spec {l}", "fix_first": f"fix {l}"}
                 for l in mapping}
        (self.outdirs[r] / "slop.json").write_text(json.dumps({"pages": pages}))

    def full_round(self, r, v, slop_score, first=5, score=9):
        _, m = self.new_round(r, v)
        self.judge(r, m, first, score)
        self.slop(r, m, slop_score)
        p = run("tally.py", self.dir, r)
        self.assertEqual(p.returncode, 0, p.stderr)
        return json.loads(p.stdout)

    def test_prompt_rendered_and_blind(self):
        out, _ = self.new_round(1, "v0")
        text = prompt_path(out, "slop").read_text()
        self.assertNotIn("{{", text)
        self.assertNotIn("acme", text.lower())
        self.assertIn("| **copy** |", text)
        self.assertIn(str(Path(out["outDir"]) / "slop.json"), text)
        # per-judge schema example uses the judge's own id
        self.assertIn('"judge": "j2"', prompt_path(out, "j2").read_text())

    def test_missing_slop_file_is_invalid(self):
        _, m = self.new_round(1, "v0")
        self.judge(1, m, 5, 9)
        p = run("tally.py", self.dir, 1)
        self.assertEqual(p.returncode, 3)
        self.assertIn("slop.json", json.loads(p.stdout)["invalid"])

    def test_gate_blocks_sloppier_version(self):
        t = self.full_round(1, "v0", slop_score=8, first=0, score=5)   # baseline v0 = 8
        self.assertEqual(t["slop"]["baseline"], 8)
        t = self.full_round(2, "v1", slop_score=5.5)                    # buyers love it, but 8-2=6 > 5.5
        self.assertEqual((t["slop"]["gatePassed"], t["passed"], t["verdict"]), (False, False, "continue"))
        fb = (self.dir / "rounds/r2/feedback.md").read_text()
        self.assertIn("more generic than the original", fb)
        self.assertIn("Fix first: fix", fb)
        self.assertNotIn("5.5", fb)                                     # no numeric score for the designer

    def test_gate_allows_small_drop_and_uses_floor_without_baseline(self):
        self.full_round(1, "v0", slop_score=8, first=0, score=5)
        t = self.full_round(2, "v1", slop_score=6.5)
        self.assertEqual((t["slop"]["gatePassed"], t["verdict"]), (True, "winner"))
        # a resumed run with no v0 slop round: floor only
        shutil.rmtree(self.dir / "rounds")
        t = self.full_round(1, "v1", slop_score=4)
        self.assertEqual((t["slop"]["baseline"], t["slop"]["min"], t["slop"]["gatePassed"]), (None, 5, False))

    def test_report_shows_slop(self):
        self.full_round(1, "v0", slop_score=8, first=0, score=5)
        self.full_round(2, "v1", slop_score=7)
        self.assertEqual(run("report.py", self.dir).returncode, 0)
        html = (self.dir / "report.html").read_text()
        self.assertIn("Slop check", html)
        self.assertIn("min 6", html)


class Speed(Slop):
    def test_plateau_stops_early(self):
        self.brief["stopRule"] = {**self.STOP, "maxRounds": 6, "plateauRounds": 2}
        self.save_brief()
        self.full_round(1, "v0", slop_score=7, first=0, score=5)
        self.full_round(2, "v1", slop_score=7, first=2, score=7)      # new best (7)
        t = self.full_round(3, "v1", slop_score=7, first=2, score=6)  # no gain
        self.assertEqual(t["verdict"], "continue")
        t = self.full_round(4, "v1", slop_score=7, first=2, score=6.5)  # 2 rounds without beating 7
        self.assertEqual((t["verdict"], t["stop"]), ("plateau", True))
        self.assertEqual(run("report.py", self.dir).returncode, 0)
        self.assertIn("Stopped early", (self.dir / "report.html").read_text())

    def test_failed_confirmation_is_not_a_plateau(self):
        self.brief["stopRule"] = {**self.STOP, "maxRounds": 6, "plateauRounds": 2}
        self.save_brief()
        self.full_round(1, "v0", slop_score=7, first=5, score=8)         # best avg so far (8)
        t = self.full_round(2, "v1", slop_score=7, first=5, score=7.5)  # passes, not a new best
        self.assertEqual(t["verdict"], "confirm")
        t = self.full_round(3, "v1", slop_score=7, first=2, score=7)    # confirmation fails
        self.assertEqual((t["verdict"], t["stop"]), ("continue", False))

    def test_confirmation_round_reuses_slop(self):
        self.brief["stopRule"] = {**self.STOP, "confirmRounds": 1}
        self.save_brief()
        t = self.full_round(1, "v1", slop_score=7)
        self.assertEqual(t["verdict"], "confirm")
        out, m = self.new_round(2, "v1")                 # same version: no slop judge this time
        self.assertNotIn("slop", out["spawn"])
        self.judge(2, m, 5, 9)
        p = run("tally.py", self.dir, 2)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        t = json.loads(p.stdout)
        self.assertEqual((t["verdict"], t["slop"]["reusedFrom"]), ("winner", 1))


class Wait(Base):
    def setUp(self):
        super().setUp()
        self.brief["timeouts"] = {"judges": 0.02, "designer": 0.02}   # ~1 second
        self.save_brief()

    def test_judges_done(self):
        _, m = self.new_round(1, "v0")
        self.judge(1, m, 5, 9)
        p = run("wait.py", self.dir, "judges", 1)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(json.loads(p.stdout)["status"], "done")

    def test_invalid_judge_file(self):
        _, m = self.new_round(1, "v0")
        self.judge(1, m, 5, 9)
        (self.outdirs[1] / "j2.json").write_text('{"pages": {')
        p = run("wait.py", self.dir, "judges", 1)
        self.assertEqual(p.returncode, 3)
        self.assertEqual(list(json.loads(p.stdout)["invalid"]), ["j2"])

    def test_timeout_names_missing_judges_and_extend(self):
        _, m = self.new_round(1, "v0")
        self.judge(1, m, 5, 9)
        (self.outdirs[1] / "j4.json").unlink()
        p = run("wait.py", self.dir, "judges", 1)
        self.assertEqual(p.returncode, 4)
        self.assertEqual(json.loads(p.stdout)["missing"], ["j4"])
        # the clock persists between calls; --extend adds time after a nudge
        self.judge(1, m, 5, 9)
        p = run("wait.py", self.dir, "judges", 1, "--extend", 1)
        self.assertEqual(p.returncode, 0, p.stdout)

    def test_slop_judge_awaited_when_enabled(self):
        self.brief["slop"] = {"enabled": True}
        self.save_brief()
        _, m = self.new_round(1, "v0")
        self.judge(1, m, 5, 9)
        p = run("wait.py", self.dir, "judges", 1)
        self.assertEqual((p.returncode, json.loads(p.stdout)["missing"]), (4, ["slop"]))

    def test_designer_done_marker(self):
        v = self.dir / "site" / "v1"
        v.mkdir(parents=True)
        self.assertEqual(run("wait.py", self.dir, "designer", "v1").returncode, 4)
        (v / ".done").touch()
        p = run("wait.py", self.dir, "designer", "v1", "--extend", 1)
        self.assertEqual(p.returncode, 0, p.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=1)
