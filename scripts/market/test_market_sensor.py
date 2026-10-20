"""Offline pipeline and API contract tests. No token or network required."""

import argparse
from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import URLError

import market_sensor as sensor


def args(**changes):
    values = dict(source="fixture", trade_date="", ts_code="", demo_abs_pct="5")
    values.update(changes)
    return argparse.Namespace(**values)


class MarketSensorTests(unittest.TestCase):
    def test_fixture_inclusive_boundary_and_protocol(self):
        report = sensor.run(args())
        self.assertEqual(report["status"], "SIGNALS")
        self.assertEqual(len(report["signals"]), 2)  # +6 and -5; excludes +1
        for signal in report["signals"]:
            self.assertEqual(signal["type"], "Market")
            self.assertEqual(signal["task_version"], "market-sensor@0.2.0")
            self.assertEqual(signal["role_spec_status"], "reviewed")
            self.assertTrue(signal["demo_only"])
            self.assertEqual(len(signal["evidence"]), 2)
            self.assertTrue({"signal_id", "what_changed", "money", "mechanism", "persistence",
                             "next_question", "generated_at"}.issubset(signal))
            self.assertTrue({"anomaly", "instrument", "magnitude", "possible_mechanism", "data_quality"}.issubset(signal))
            self.assertEqual(signal["persistence"], "一次性")
            self.assertFalse(signal["research_eligible"])
            self.assertFalse(signal["data_quality"]["history_sufficient"])
            self.assertTrue(signal["data_quality"]["synthetic"])
        self.assertTrue(report["demo_only"])
        self.assertFalse(report["research_eligible"])
        self.assertTrue(report["research_blockers"])
        self.assertEqual(report["rule"]["status"], "demo_only")

    def test_no_match_is_not_no_data(self):
        self.assertEqual(sensor.run(args(demo_abs_pct="99"))["status"], "NO_MATCH")
        with patch.object(sensor, "fetch_tushare", return_value=[]):
            report = sensor.run(args(source="tushare", trade_date="20261016", ts_code="000001.SZ"))
        self.assertEqual(report["status"], "NO_DATA")
        self.assertEqual(report["signals"], [])

    def test_bad_parameters_fail_before_fetch(self):
        cases = [dict(demo_abs_pct=value) for value in (None, "0", "-1", "nan", "inf", "x")]
        cases += [dict(source="other"), dict(trade_date="20261016"),
                  dict(source="tushare", trade_date="20260230", ts_code="000001.SZ"),
                  dict(source="tushare", trade_date="20261016", ts_code="000001.SZ,000002.SZ")]
        with patch.object(sensor, "fetch_tushare") as fetch:
            for case in cases:
                with self.subTest(case=case):
                    self.assertEqual(sensor.run(args(**case))["status"], "ERROR")
            fetch.assert_not_called()

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_token_never_falls_back_or_connects(self):
        with patch.object(sensor, "urlopen") as connect:
            report = sensor.run(args(source="tushare", trade_date="20261016", ts_code="000001.SZ"))
        connect.assert_not_called()
        self.assertEqual(report["status"], "ERROR")
        self.assertEqual(report["signals"], [])

    @patch.dict(os.environ, {"TUSHARE_TOKEN": "FAKE_TEST_TOKEN"})
    def test_tushare_request_contract_and_normalization(self):
        # Field order deliberately differs from request; mock is not live validation.
        response = {"code": 0, "data": {
            "fields": ["pct_chg", "ts_code", "trade_date", "close", "vol", "amount"],
            "items": [[-5.0, "000001.SZ", "20261016", 10.0, 100, 100]],
        }}
        with patch.object(sensor, "urlopen", return_value=io.StringIO(json.dumps(response))) as connect:
            report = sensor.run(args(source="tushare", trade_date="20261016", ts_code="000001.SZ"))
        request = connect.call_args[0][0]
        self.assertEqual(request.full_url, "https://api.tushare.pro")
        self.assertEqual(connect.call_args[1]["timeout"], 30)
        payload = json.loads(request.data)
        self.assertEqual(payload["api_name"], "daily")
        self.assertEqual(payload["params"], {"trade_date": "20261016", "ts_code": "000001.SZ"})
        self.assertEqual(payload["token"], "FAKE_TEST_TOKEN")
        self.assertEqual(payload["fields"], ",".join(sensor.FIELDS))
        self.assertEqual(report["status"], "SIGNALS")
        self.assertEqual(report["observations"][0]["pct_chg"], -5)
        self.assertFalse(report["research_eligible"])
        self.assertFalse(report["signals"][0]["data_quality"]["synthetic"])
        self.assertFalse(report["signals"][0]["data_quality"]["liquidity_verified"])
        self.assertNotIn("FAKE_TEST_TOKEN", json.dumps(report))

    @patch.dict(os.environ, {"TUSHARE_TOKEN": "FAKE_TEST_TOKEN"})
    def test_upstream_errors_are_sanitized(self):
        for response in ({"code": -1, "msg": "FAKE_TEST_TOKEN"},
                         {"code": 0, "data": {"fields": [], "items": []}},
                         {"code": 0, "data": {"fields": list(sensor.FIELDS), "items": [[1]]}}):
            with self.subTest(response=response):
                with patch.object(sensor, "urlopen", return_value=io.StringIO(json.dumps(response))):
                    report = sensor.run(args(source="tushare", trade_date="20261016", ts_code="000001.SZ"))
                self.assertEqual(report["status"], "ERROR")
                self.assertNotIn("FAKE_TEST_TOKEN", json.dumps(report))
        with patch.object(sensor, "urlopen", side_effect=URLError("FAKE_TEST_TOKEN")):
            report = sensor.run(args(source="tushare", trade_date="20261016", ts_code="000001.SZ"))
        self.assertEqual(report["status"], "ERROR")
        self.assertNotIn("FAKE_TEST_TOKEN", json.dumps(report))

    def test_invalid_rows_fail_instead_of_becoming_no_match(self):
        row = dict(ts_code="000001.SZ", trade_date="20261016", close=10, pct_chg=6, vol=100, amount=100)
        cases = [[{**row, key: value}] for key, value in (
            ("pct_chg", float("nan")), ("pct_chg", None), ("pct_chg", "6"),
            ("close", 0), ("vol", -1), ("amount", True),
            ("trade_date", "20261015"), ("ts_code", "000002.SZ"))]
        cases += [[row, row], [{"ts_code": "000001.SZ"}]]
        for rows in cases:
            with self.subTest(rows=rows):
                with patch.object(sensor, "fetch_tushare", return_value=rows):
                    report = sensor.run(args(source="tushare", trade_date="20261016", ts_code="000001.SZ"))
                self.assertEqual(report["status"], "ERROR")
                self.assertEqual(report["signals"], [])

    def test_cli_overwrites_stale_report_on_runtime_error(self):
        with tempfile.TemporaryDirectory() as directory, redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            output = Path(directory) / "report.json"
            self.assertEqual(sensor.main(["--demo-abs-pct", "5", "--output", str(output)]), 0)
            self.assertEqual(json.loads(output.read_text())["status"], "SIGNALS")
            self.assertEqual(sensor.main(["--demo-abs-pct", "nan", "--output", str(output)]), 1)
            report = json.loads(output.read_text())
            self.assertEqual(report["status"], "ERROR")
            self.assertEqual(report["signals"], [])


if __name__ == "__main__":
    unittest.main()
