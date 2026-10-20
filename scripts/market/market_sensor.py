#!/usr/bin/env python3
"""V1 pipeline skeleton. All anomaly rules and outputs are demo-only."""

import argparse
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import sys
from urllib.error import URLError
from urllib.request import Request, urlopen


TASK_ID = "market-sensor"
VERSION = "0.2.0"
FIXTURE = Path(__file__).with_name("fixture.json")
ENDPOINT = "https://api.tushare.pro"
DAILY_DOC = "https://tushare.pro/document/1?doc_id=27"
FIELDS = ("ts_code", "trade_date", "close", "pct_chg", "vol", "amount")


class SensorError(ValueError):
    """Safe, local diagnostic; never contains a token or upstream error body."""


def check_date(value):
    if not re.fullmatch(r"[0-9]{8}", value):
        raise SensorError("trade_date 必须为 YYYYMMDD。")
    try:
        datetime.strptime(value, "%Y%m%d")
    except ValueError:
        raise SensorError("trade_date 不是有效日期。") from None


def positive_threshold(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise SensorError("必须显式提供正数 --demo-abs-pct（百分数）。") from None
    if not math.isfinite(number) or number <= 0:
        raise SensorError("demo-abs-pct 必须是有限正数。")
    return number


def fetch_tushare(trade_date, ts_code):
    token = os.environ.get("TUSHARE_TOKEN", "").strip()
    if not token:
        raise SensorError("未设置 TUSHARE_TOKEN；不回退到合成数据。")
    payload = {
        "api_name": "daily", "token": token,
        "params": {"trade_date": trade_date, "ts_code": ts_code},
        "fields": ",".join(FIELDS),
    }
    request = Request(
        ENDPOINT, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urlopen(request, timeout=30) as response:
            result = json.load(response)
    except (URLError, TimeoutError, OSError, ValueError):
        raise SensorError("Tushare 网络/响应失败；检查 HTTPS 可达性与服务状态。") from None
    if not isinstance(result, dict) or result.get("code") != 0:
        raise SensorError("Tushare API 失败；检查账户权限/额度，不记录原始错误体。")
    data = result.get("data")
    if not isinstance(data, dict):
        raise SensorError("Tushare 缺少 data 对象。")
    fields, items = data.get("fields"), data.get("items")
    if (not isinstance(fields, list) or not all(isinstance(f, str) for f in fields)
            or len(fields) != len(set(fields)) or not set(FIELDS).issubset(fields)
            or not isinstance(items, list)):
        raise SensorError("Tushare 返回字段不符合 daily 契约。")
    if any(not isinstance(row, list) or len(row) != len(fields) for row in items):
        raise SensorError("Tushare 行长度与字段不一致。")
    return [dict(zip(fields, row)) for row in items]


def validate_rows(rows, trade_date, ts_code):
    if not isinstance(rows, list):
        raise SensorError("observations 必须是数组。")
    normalized, seen = [], set()
    for row in rows:
        if not isinstance(row, dict) or not set(FIELDS).issubset(row):
            raise SensorError("行情记录缺少必要字段。")
        code = row["ts_code"]
        if not isinstance(code, str) or not code or row["trade_date"] != trade_date:
            raise SensorError("行情标识缺失或日期不符。")
        if ts_code and code != ts_code:
            raise SensorError("返回标的与请求单一标的不符。")
        if code in seen:
            raise SensorError("单日行情出现重复标的。")
        seen.add(code)
        clean = {"ts_code": code, "trade_date": trade_date}
        for field in ("close", "pct_chg", "vol", "amount"):
            value = row[field]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise SensorError("行情存在无效或非有限数值。")
            if (field == "close" and value <= 0) or (field in ("vol", "amount") and value < 0):
                raise SensorError("行情价格/成交量/成交额范围错误。")
            clean[field] = value
        normalized.append(clean)
    return sorted(normalized, key=lambda row: row["ts_code"])


def detect(rows, threshold, source, generated_at):
    signals = []
    for row in rows:
        magnitude = abs(row["pct_chg"])
        if magnitude < threshold:
            continue
        synthetic = source == "fixture"
        source_ref = "scripts/market/fixture.json" if synthetic else "tushare:daily"
        signals.append({
            "signal_id": f"MKT-DEMO-{source}-{row['trade_date']}-{row['ts_code']}",
            "type": "Market",
            "what_changed": (
                f"{'合成样本' if synthetic else 'Tushare 日线'} {row['ts_code']} "
                f"{row['trade_date']} pct_chg={row['pct_chg']}%；"
                f"abs={magnitude}% >= 演示阈值 {threshold}%。"
            ),
            "anomaly": f"单日涨跌幅绝对值 {magnitude}% 命中演示阈值；未确立正式异常。",
            "instrument": row["ts_code"],
            "magnitude": {"abs_pct_chg": magnitude, "threshold_pct": threshold,
                          "historical_percentile": None},
            "money": f"记录成交额 {row['amount']} 千元、成交量 {row['vol']} 手；未识别可捕获钱流，非收入/利润。",
            "evidence": [
                {"source": source_ref, "observed_at": row["trade_date"],
                 "fact": row.copy()},
                {"source": "tasks/github-actions/market-sensor.md" if synthetic else DAILY_DOC,
                 "observed_at": generated_at,
                 "fact": "字段/演示说明，非独立市场证据；fixture 为合成数据。" if synthetic
                         else "daily 字段：pct_chg 为百分数、vol 为手、amount 为千元；同一提供者，非独立市场证据。"},
            ],
            "mechanism": "仅命中演示筛选条件，经济机制未知；不代表错价、利润或交易机会。",
            "possible_mechanism": "未知；单日价格跳动不足以推断经济机制。",
            "persistence": "一次性",
            "persistence_note": "仅本次单日观察，实际持续性未知。",
            "data_quality": {"synthetic": synthetic, "history_points": 1,
                             "history_sufficient": False, "liquidity_verified": False,
                             "reliability": "合成数据，非行情" if synthetic else "实连数据质量尚未独立核验"},
            "research_eligible": False,
            "next_question": "确认正式观察范围/规则，补足历史背景、经济机制、可交易性及流动性证据。",
            "task_version": f"{TASK_ID}@{VERSION}",
            "generated_at": generated_at,
            "role_spec_status": "reviewed",
            "demo_only": True,
        })
    return signals


def run(args):
    report = {
        "task_id": TASK_ID, "task_version": VERSION,
        "role_spec_status": "reviewed",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": args.source, "demo_only": True,
        "research_eligible": False,
        "research_blockers": ["演示规则非正式异常", "仅单日观察，无足够历史背景",
                              "经济机制、可交易性及流动性未验证"],
        "trade_date": args.trade_date, "ts_code": args.ts_code,
        "rule": {"id": "demo_abs_daily_pct", "status": "demo_only", "threshold_pct": None},
        "status": "ERROR", "observations": [], "signals": [],
    }
    try:
        threshold = positive_threshold(args.demo_abs_pct)
        report["rule"]["threshold_pct"] = threshold
        if args.source == "fixture":
            if args.trade_date or args.ts_code:
                raise SensorError("fixture 使用固定日期及合成标的；请留空 trade-date / ts-code。")
            fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
            trade_date, ts_code = fixture["trade_date"], ""
            check_date(trade_date)
            rows = fixture["observations"]
        elif args.source == "tushare":
            trade_date, ts_code = args.trade_date, args.ts_code
            check_date(trade_date)
            if not re.fullmatch(r"[0-9]{6}\.(SH|SZ|BJ)", ts_code):
                raise SensorError("ts-code 必须是单一 A 股标的，如 000001.SZ。")
            rows = fetch_tushare(trade_date, ts_code)
        else:
            raise SensorError("source 只允许 fixture 或 tushare。")
        rows = validate_rows(rows, trade_date, ts_code)
        signals = detect(rows, threshold, args.source, report["generated_at"])
        report.update(trade_date=trade_date, ts_code=ts_code, observations=rows, signals=signals,
                      status="NO_DATA" if not rows else "SIGNALS" if signals else "NO_MATCH")
    except SensorError as exc:
        report["error"] = str(exc)
    except Exception as exc:
        # Do not serialize upstream exception text: it may contain credentials.
        report["error"] = f"运行失败（{type(exc).__name__}）；未记录原始错误内容。"
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default="fixture")
    parser.add_argument("--trade-date", default="")
    parser.add_argument("--ts-code", default="")
    parser.add_argument("--demo-abs-pct", help="Required positive percent; demo rule only")
    parser.add_argument("--output", type=Path, default=Path("outputs/market/report.json"))
    args = parser.parse_args(argv)
    report = run(args)
    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    except OSError:
        print("ERROR: 无法写入报告。", file=sys.stderr)
        return 1
    print(f"{report['status']}: {len(report['signals'])} demo signal(s); {args.output}")
    if report["status"] == "ERROR":
        print(report["error"], file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
