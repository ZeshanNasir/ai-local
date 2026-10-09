import json
import unittest
from pathlib import Path
from unittest import mock

from labbench import bench, cost, embed, netcheck, ollama, report, scoring, start, stats, workloads

REPO = Path(__file__).resolve().parent.parent / "data" / "synthetic" / "coding" / "repo"
FIXED = '''def apply_discount(price_cents: int, percent: int) -> int:
    if not 0 <= percent <= 100:
        raise ValueError("percent must be between 0 and 100")
    return (price_cents * (100 - percent) + 50) // 100
'''


class Scoring(unittest.TestCase):
    def test_json_is_found_inside_prose(self):
        self.assertEqual(scoring.parse_json('Sure: {"a": 1} done'), {"a": 1})
        self.assertIsNone(scoring.parse_json("no json here"))

    def test_log_abstention_and_evidence(self):
        want = {"supports": True, "evidence": [4]}
        ok = json.dumps({"supports_conclusion": True, "evidence_lines": [4, 5]})
        self.assertTrue(scoring.score_log(ok, want)["passed"])
        self.assertEqual(scoring.score_log(json.dumps({"supports_conclusion": True, "evidence_lines": [1]}), want)["why"], "missing_evidence")
        self.assertEqual(scoring.score_log(json.dumps({"supports_conclusion": False, "evidence_lines": []}), want)["why"], "false_abstention")
        none = {"supports": False, "evidence": []}
        self.assertEqual(scoring.score_log(json.dumps({"supports_conclusion": True, "evidence_lines": [2]}), none)["why"], "wrong_abstention")

    def test_doc_scoring(self):
        want = {"status": "answered", "sources": ["a"], "contains": "14"}
        self.assertTrue(scoring.score_doc(json.dumps({"status": "answered", "answer": "14 days", "sources": ["a"]}), want)["passed"])
        self.assertEqual(scoring.score_doc(json.dumps({"status": "answered", "answer": "7 days", "sources": ["a"]}), want)["why"], "answer_missing_fact")
        self.assertEqual(scoring.score_doc(json.dumps({"status": "insufficient"}), want)["why"], "status_insufficient")
        self.assertTrue(scoring.score_doc(json.dumps({"status": "insufficient"}), {"status": "insufficient"})["passed"])

    def test_the_shipped_coding_task_fails_until_fixed(self):
        self.assertFalse(scoring.run_tests(REPO)[0])
        self.assertTrue(scoring.score_patch(REPO, {"calc/pricing.py": '"""x"""\n' + FIXED})["passed"])

    def test_patch_scope_is_enforced(self):
        self.assertEqual(scoring.score_patch(REPO, {"tests/test_pricing.py": "pass\n"})["why"], "edited_tests")
        self.assertEqual(scoring.score_patch(REPO, {"../escape.py": "x"})["why"], "path_outside_repo_or_new_file")
        self.assertEqual(scoring.score_patch(REPO, {"calc/new.py": "x"})["why"], "path_outside_repo_or_new_file")
        self.assertEqual(scoring.score_patch(REPO, {"calc/pricing.py": "def apply_discount(p, c):\n    return p\n"})["why"], "tests_fail")


class Measurement(unittest.TestCase):
    def test_summary_and_spread(self):
        self.assertEqual(stats.summarize([1, 2, 3])["median"], 2)
        self.assertEqual(stats.spread_pct([9, 10, 11]), 20.0)
        self.assertIsNone(stats.spread_pct([5]))

    def test_filler_size_and_cache_busting(self):
        a, b = bench.filler(1000, "x"), bench.filler(1000, "y")
        self.assertGreater(sum(map(len, a)), 2700)
        self.assertNotEqual(a[0], b[0])
        self.assertEqual(a[1:], b[1:])

    def test_ladder_stops_at_first_unsafe_step_and_flags_wrong_size(self):
        calls = []

        def fake(model, prompt, **kw):
            calls.append(kw["num_ctx"])
            return ollama.Generation(text="OSPREY-000", prompt_tokens=100, prompt_s=1, decode_tokens=3, decode_s=1,
                                     error="" if len(calls) < 3 else "TimeoutError: slow")
        with mock.patch.object(ollama, "generate", fake), mock.patch.object(ollama, "unload_all"), \
                mock.patch.object(ollama, "loaded", return_value=[]), mock.patch("labbench.env.memory_free_pct", return_value=60), \
                mock.patch("labbench.env.swap_used_mb", return_value=0.0):
            out = bench.ladder("m:1", [4096, 8192, 16384])
        self.assertEqual(len(out["steps"]), 2)
        self.assertFalse(out["steps"][0]["size_ok"])  # 100 prompt tokens reported for a ~4K target
        self.assertTrue(out["steps"][1]["stopped_here"])

    def test_workloads_wiring_with_a_canned_model(self):
        def canned(model, prompt, **kw):
            if "Logs:" in prompt:
                return ollama.Generation(text=json.dumps({"supports_conclusion": False, "evidence_lines": []}), decode_tokens=5, decode_s=1)
            if "Question:" in prompt and "Use \"insufficient\"" in prompt:
                return ollama.Generation(text=json.dumps({"status": "insufficient"}), decode_tokens=5, decode_s=1)
            return ollama.Generation(text=json.dumps({"path": "calc/pricing.py", "content": '"""x"""\n' + FIXED}), decode_tokens=5, decode_s=1)
        with mock.patch.object(ollama, "generate", canned):
            rows = workloads.run_workloads("m:1")
        by = {w: [r["passed"] for r in rows if r["workload"] == w] for w in ("logs", "docs", "code")}
        self.assertEqual(by["code"], [True])
        self.assertEqual(sum(by["logs"]), 3)   # only the three abstention cases pass with this canned answer
        self.assertEqual(sum(by["docs"]), 2)   # only the two "insufficient" cases pass


class Retrieval(unittest.TestCase):
    def test_metrics(self):
        m = embed.metrics([["a", "b"], ["b", "a"], ["a"]], [{"a"}, {"a"}, set()])
        self.assertEqual((m["queries"], m["recall_at_1"], m["mrr"]), (2, 0.5, 0.75))

    def test_bm25_finds_the_backup_document(self):
        docs = workloads.load_docs()
        self.assertEqual(embed.bm25_rank("how many days are nightly backups kept", docs)[0], "backup-retention")

    def test_cosine(self):
        self.assertAlmostEqual(embed.cosine([1, 0], [1, 0]), 1.0)
        self.assertAlmostEqual(embed.cosine([1, 0], [0, 1]), 0.0)


class Cost(unittest.TestCase):
    A = {"seats": 5, "hardware_price": 3000, "service_life_months": 36, "power_cost_per_month": 3, "support_hours_per_month": 2,
         "support_hourly_cost": 60, "tasks_per_month": 200, "viable_share": 0.5, "local_success_rate": 0.8,
         "cloud_cost_per_task": 0.5, "review_minutes_per_failure": 10, "hourly_cost": 60}

    def test_arithmetic(self):
        r = cost.evaluate(self.A)
        self.assertAlmostEqual(r["monthly_fixed_local_cost_per_seat"], 3000 / 36 + 3 + 2 * 60 / 5, places=2)
        # per viable task: 0.8 * 0.5 gain - 0.2 * (10/60 * 60) loss = 0.4 - 2.0 = -1.6, so local can never pay for itself here
        self.assertIsNone(r["breakeven_viable_share"])
        self.assertFalse(r["breakeven_possible"])

    def test_breakeven_exists_when_failures_are_cheap(self):
        r = cost.evaluate({**self.A, "review_minutes_per_failure": 1, "cloud_cost_per_task": 5, "tasks_per_month": 400})
        self.assertTrue(r["breakeven_possible"])
        at_breakeven = cost.evaluate({**self.A, "review_minutes_per_failure": 1, "cloud_cost_per_task": 5, "tasks_per_month": 400,
                                      "viable_share": r["breakeven_viable_share"]})
        self.assertLess(abs(at_breakeven["monthly_net_per_seat"]), 1.0)  # breakeven share is rounded to 3 places

    def test_per_seat_billing_only_credits_removable_licences(self):
        a = {**self.A, "cloud_billing": "per_seat", "cloud_seat_price_per_month": 60, "removable_seat_share": 0.0, "viable_share": 0.9}
        self.assertEqual(cost.evaluate(a)["monthly_cloud_cost_avoided_per_seat"], 0)  # heavy local use, no licence cancelled
        self.assertEqual(cost.evaluate({**a, "removable_seat_share": 0.5})["monthly_cloud_cost_avoided_per_seat"], 30)

    def test_sensitivity_is_monotonic_in_success_rate(self):
        s = cost.sensitivity(self.A)
        values = [s[k] for k in sorted(s)]
        self.assertEqual(values, sorted(values))


class Network(unittest.TestCase):
    def test_classify(self):
        self.assertEqual(netcheck._classify("127.0.0.1:11434"), "loopback")
        self.assertEqual(netcheck._classify("192.168.1.5:443"), "private")
        self.assertEqual(netcheck._classify("8.8.8.8:443"), "other")


class Report(unittest.TestCase):
    def test_tables_render_from_result_files(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            Path(d, "m.throughput.json").write_text(json.dumps({"model": "m:1", "runs": [{"load_s": 1.0}], "decode_spread_pct": 5.0,
                "warm_summary": {k: {"median": 1.0} for k in ("ttft_s", "prompt_tok_s", "decode_tok_s", "wall_s")}}))
            Path(d, "m.workloads.json").write_text(json.dumps({"model": "m:1", "summary": {"logs": "1/1", "docs": "1/1", "code": "1/1"}, "median_wall_s": {"median": 2.0}}))
            Path(d, "m.ladder.json").write_text(json.dumps({"model": "m:1", "steps": [{"prompt_tokens": 8000, "recalled_fact": True, "size_ok": True, "error": "", "prompt_tok_s": 500,
                "ttft_s": 16, "server_reported_gb": 20.0, "min_free_pct": 30, "swap_growth_mb": 0, "stopped_here": True}]}))
            text = report.tables(d)
        self.assertIn("| `m:1` | 1.0 s |", text)
        self.assertIn("8,000", text)
        self.assertIn("stopped: unsafe", text)


class Data(unittest.TestCase):
    def test_every_question_topic_exists_and_logs_are_numbered_consistently(self):
        docs = workloads.load_docs()
        for q in workloads.load_questions():
            self.assertTrue(set(q["topic"]) <= set(docs), q["id"])
            self.assertTrue(set(q["expect"].get("sources", [])) <= set(docs), q["id"])
        for case in workloads.load_logs():
            self.assertTrue(all(1 <= n <= len(case["lines"]) for n in case["expect"]["evidence"]), case["id"])


class FirstRun(unittest.TestCase):
    def test_loopback_detection(self):
        for host, ok in (("127.0.0.1:11434", True), ("http://localhost:11434", True), ("10.0.0.5:11434", False), ("https://example.com", False)):
            with mock.patch.dict("os.environ", {"OLLAMA_HOST": host}):
                self.assertEqual(ollama.is_loopback(), ok, host)

    def test_remote_server_is_refused_before_anything_else_runs(self):
        with mock.patch.dict("os.environ", {"OLLAMA_HOST": "10.0.0.5:11434"}), \
             mock.patch.object(start.sys, "platform", "darwin"), mock.patch.object(start.platform, "machine", return_value="arm64"):
            self.assertIn("not this machine", start.preflight()[0])

    def test_offered_models_come_from_saved_evidence(self):
        names = [m[0] for m in start.measured_models()]
        self.assertEqual(sorted(names), ["gemma4:26b-mlx", "qwen3.6:35b-mlx", "qwen3.8:27b-mlx"])
        self.assertTrue(all(size for _, size, _ in start.measured_models()))

    def test_missing_model_is_not_pulled_without_consent(self):
        snap = {"chip": "Apple M4 Pro", "memory_gib": 48, "macos": "27", "ollama_version": "x", "power": "AC",
                "memory_free_pct": 50, "installed_models": []}
        with mock.patch.object(start, "preflight", return_value=[]), mock.patch.object(start.env, "snapshot", return_value=snap), \
             mock.patch.object(start, "_ask", return_value=False), mock.patch.object(start.subprocess, "run") as pull:
            self.assertEqual(start.run("gemma4:26b-mlx"), 1)
        pull.assert_not_called()


if __name__ == "__main__":
    unittest.main()
