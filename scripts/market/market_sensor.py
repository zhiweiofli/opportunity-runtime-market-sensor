#!/usr/bin/env python3
"""Deterministic Market monitoring: legacy demo and historical trial modes."""

import argparse
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import sys
from http.client import HTTPException
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


TASK_ID = "market-sensor"
VERSION = "0.3.0"
FIXTURE = Path(__file__).with_name("fixture.json")
ENDPOINT = "https://api.tushare.pro"
DAILY_DOC = "https://tushare.pro/document/1?doc_id=27"
FIELDS = ("ts_code", "trade_date", "close", "pct_chg", "vol", "amount")


class SensorError(ValueError):
    """Safe, local diagnostic; never contains a token or upstream error body."""


class TemporaryFetchError(SensorError):
    """A retryable transport failure, without upstream exception contents."""


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


def request_daily(params, timeout=30):
    token = os.environ.get("TUSHARE_TOKEN", "").strip()
    if not token:
        raise SensorError("未设置 TUSHARE_TOKEN；不回退到合成数据。")
    payload = {
        "api_name": "daily", "token": token,
        "params": params,
        "fields": ",".join(FIELDS),
    }
    request = Request(
        ENDPOINT, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            result = json.load(response)
    except HTTPError as exc:
        if exc.code in (408, 429) or 500 <= exc.code <= 599:
            raise TemporaryFetchError("Tushare 临时 HTTP 失败；请稍后复核。") from None
        raise SensorError("Tushare HTTP 失败；检查权限与请求，不记录原始错误体。") from None
    except (URLError, TimeoutError, OSError, HTTPException):
        raise TemporaryFetchError("Tushare 网络失败；检查 HTTPS 可达性与服务状态。") from None
    except ValueError:
        raise SensorError("Tushare 响应不是有效 JSON。") from None
    if (not isinstance(result, dict) or type(result.get("code")) is not int
            or result["code"] != 0):
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


def fetch_tushare(trade_date, ts_code):
    return request_daily({"trade_date": trade_date, "ts_code": ts_code})


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
    if getattr(args, "mode", "demo") == "history":
        from market_history import run_history
        return run_history(args)
    report = {
        "task_id": TASK_ID, "task_version": VERSION,
        "mode": "demo",
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
        if getattr(args, 'as_of_date', ''):
            raise SensorError('as-of-date 仅用于 history 模式。')
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


def render_markdown(report, json_filename='report.json'):
    """Human handoff with explicit JSON locations and measurement boundaries."""
    history = report.get("mode") == "history"
    lines = ["# Market Sensor 运行报告", "",
             f"- 任务版本：{report['task_version']}；状态：{report['status']}",
             f"- 生成时间：{report['generated_at']}；数据源：{report['source']}",
             f"- 演示：{str(report['demo_only']).lower()}；规则：{report['rule']['status']}",
             "- research_eligible=false；统计候选不等于错价或交易策略，未核验机制不得交真实 Research。",
             "- 合成数据不是真实行情。" if report['source'] == 'fixture' else
             "- 真实数据、单日演示规则；数据尚未经独立来源交叉核验。" if not history else
             "- 真实测量试运行；数据尚未经独立来源交叉核验。"]
    if history:
        lines += [f"- 目标日：{report['as_of_date']}（Asia/Taipei）；请求区间：{report['request_range']}",
                  f"- 配置 SHA-256：`{report.get('config_sha256')}`；完整配置：JSON `#/config`",
                  f"- 覆盖完整：{str(report['coverage_complete']).lower()}；覆盖名单：JSON `#/coverage`",
                  f"- 总命中 {report['total_matches']}，展示 {len(report['signals'])}，截断 {report['truncated_matches']}；排序：分位↓、abs(R5)↓、成交倍数↓、代码↑。",
                  "", "## 覆盖与失败", "",
                  f"代码 | 状态 | 原因 | 有效行数 | 原始数据定位（本目录 {json_filename}）",
                  "--- | --- | --- | --- | ---"]
        for i, item in enumerate(report['instruments']):
            lines.append(f"{item['ts_code']} | {item['status']} | {item['reason']} | {item['valid_rows']} | "
                         f"#/instruments/{i}；#/observations 从 {item['observations_start']} 起 {item['valid_rows']} 条")
    if report.get('error'):
        lines += ["", "## 运行错误", "", report['error'], "本轮不输出候选；不得复用上次成功快照。"]
    lines += ["", "## 候选（事实与推测分列）", ""]
    for i, signal in enumerate(report['signals']):
        lines += [f"### {signal['signal_id']}", "", signal['what_changed'],
                  f"- 量化事实：`{json.dumps(signal['magnitude'], ensure_ascii=False)}`",
                  f"- 持续性：{signal['persistence']}；{signal.get('persistence_note', '')}",
                  f"- 同向命中日期：{', '.join(signal.get('same_direction_hit_dates', [])) or '单日演示，不适用'}",
                  f"- 钱与单位：{signal['money']}",
                  f"- 待验证推测：{signal['possible_mechanism']}",
                  f"- 人工下一步：{signal['next_question']}",
                  f"- 原始数据与证据：JSON `#/signals/{i}/evidence`；质量：`#/signals/{i}/data_quality`", ""]
    if not report['signals']:
        lines.append("本轮无可展示候选；缺失、过滤或错误不构成‘没有市场异常’的结论。")
    lines += ["", "## 人工交接", "",
              "先复核 JSON 原始数据、配置、历史基准、缺失与错误；再核验信息事件、经济机制、历史重复性及表达成本。",
              "成交额不是净资金流、收入或利润。接口字段说明和行情来自同一提供者，不是独立市场证据。",
              "未补齐原稿研究条件前保持 research_eligible=false；不提供买卖、目标价或仓位指令。", ""]
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("demo", "history"), default="demo")
    parser.add_argument("--source", default="fixture")
    parser.add_argument("--trade-date", default="")
    parser.add_argument("--ts-code", default="")
    parser.add_argument("--demo-abs-pct", help="Required positive percent; demo rule only")
    parser.add_argument("--as-of-date", default="", help="History YYYYMMDD; default today in Asia/Taipei")
    parser.add_argument("--config", type=Path, default=Path(__file__).resolve().parents[2] / "config/market-v1.json")
    parser.add_argument("--history-fixture", type=Path, default=Path(__file__).with_name("history-fixture.json"))
    parser.add_argument("--output", type=Path, default=Path("outputs/market/report.json"))
    args = parser.parse_args(argv)
    outputs = (args.output, args.output.with_suffix(".md"))
    if outputs[0] == outputs[1]:
        print("ERROR: JSON 输出路径不能与 Markdown 路径相同。", file=sys.stderr)
        return 1
    try:
        # Clear snapshots before fetching; later write failures cannot leave old success.
        for path in outputs:
            path.unlink(missing_ok=True)
        report = run(args)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        outputs[1].write_text(render_markdown(report, args.output.name), encoding="utf-8")
    except OSError:
        for path in outputs:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
        print("ERROR: 无法写入报告。", file=sys.stderr)
        return 1
    print(f"{report['status']}: {len(report['signals'])} candidate(s); {args.output}")
    if report["status"] == "ERROR":
        print(report["error"], file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
