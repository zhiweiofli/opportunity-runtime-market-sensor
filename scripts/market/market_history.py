"""Historical daily monitoring. Decimal arithmetic, no calendar/API dependencies beyond daily."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import re
from statistics import median
import time
from zoneinfo import ZoneInfo

import market_sensor as sensor


CONFIG = Path(__file__).resolve().parents[2] / "config/market-v1.json"
COMPLETE = {"MATCH", "NO_MATCH", "LOW_LIQUIDITY"}
INTEGER_KEYS = (
    "lookback_calendar_days", "return_window", "baseline_observations", "min_history",
    "amount_lookback", "persistence_observations", "min_same_direction_hits",
    "persistence_max_calendar_days", "liquidity_lookback", "recent_observations",
    "recent_max_calendar_days", "max_signals",
)
NUMBER_KEYS = ("abs_return_min", "percentile_min", "amount_ratio_min", "min_avg_amount_cny",
               "request_interval_seconds", "request_timeout_seconds")


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def taipei_today():
    return datetime.now(ZoneInfo("Asia/Taipei")).strftime("%Y%m%d")


def day(value):
    sensor.check_date(value)
    return datetime.strptime(value, "%Y%m%d").date()


def load_config(path):
    raw = Path(path).read_bytes()
    config = json.loads(raw)
    required = {*INTEGER_KEYS, *NUMBER_KEYS, "task_version", "rule_id", "universe", "retry_delays_seconds"}
    if not isinstance(config, dict) or set(config) != required:
        raise sensor.SensorError("历史配置字段不符合版本化契约。")
    if config['task_version'] != sensor.VERSION or config['rule_id'] != 'price_volume_stress_v1':
        raise sensor.SensorError("历史配置版本或规则 ID 不符。")
    universe = config['universe']
    if (not isinstance(universe, list) or not universe
            or any(not isinstance(c, str) or not re.fullmatch(r'[0-9]{6}\.(SH|SZ|BJ)', c) for c in universe)
            or len(set(universe)) > 20):
        raise sensor.SensorError("历史名单必须为1至20个去重 A 股代码。")
    for key in INTEGER_KEYS:
        if type(config[key]) is not int or config[key] <= 0:
            raise sensor.SensorError("历史配置的样本数/窗口必须为正整数。")
    for key in NUMBER_KEYS:
        n = config[key]
        if type(n) not in (int, float) or not math.isfinite(n) or n <= 0:
            raise sensor.SensorError("历史配置阈值必须为有限正数。")
    if (config['percentile_min'] > 1 or config['max_signals'] > 5
            or config['min_same_direction_hits'] > config['persistence_observations']
            or config['min_same_direction_hits'] < 2
            or config['min_history'] < max(
                config['baseline_observations'] + config['return_window'] + config['persistence_observations'] - 1,
                config['amount_lookback'] + config['persistence_observations'],
                config['liquidity_lookback'] + 1, config['recent_observations'])
            or config['request_interval_seconds'] < 2 or config['request_timeout_seconds'] > 30
            or config['retry_delays_seconds'] != [2, 5]):
        raise sensor.SensorError("历史配置窗口或请求限制不符合试运行边界。")
    return config, hashlib.sha256(raw).hexdigest()


class DailyClient:
    """Serial pacing also applies between retries and after failed requests."""

    def __init__(self, config):
        self.config = config
        self.last_request = None

    def fetch(self, start_date, end_date, ts_code):
        delays = self.config['retry_delays_seconds']
        for attempt in range(len(delays) + 1):
            if self.last_request is not None:
                remaining = self.config['request_interval_seconds'] - (time.monotonic() - self.last_request)
                if remaining > 0:
                    time.sleep(remaining)
            self.last_request = time.monotonic()
            try:
                return sensor.request_daily(
                    {'start_date': start_date, 'end_date': end_date, 'ts_code': ts_code},
                    timeout=self.config['request_timeout_seconds'])
            except sensor.TemporaryFetchError:
                if attempt == len(delays):
                    raise
                time.sleep(delays[attempt])


def validate_history(rows, start_date, as_of_date, ts_code):
    if not isinstance(rows, list):
        raise sensor.SensorError("observations 必须是数组。")
    normalized, seen = [], set()
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get('trade_date'), str):
            raise sensor.SensorError("历史记录缺少有效日期。")
        date = row['trade_date']
        day(date)
        if not start_date <= date <= as_of_date:
            raise sensor.SensorError("历史记录越过请求区间或目标日。")
        if date in seen:
            raise sensor.SensorError("同代码同日出现重复历史记录。")
        seen.add(date)
        clean = sensor.validate_rows([row], date, ts_code)[0]
        if clean['pct_chg'] <= -100:
            raise sensor.SensorError("历史 pct_chg 必须大于 -100%。")
        normalized.append(clean)
    return sorted(normalized, key=lambda row: row['trade_date'])


def decimal(value):
    return Decimal(str(value))


def number(value):
    result = float(value)
    if not math.isfinite(result):
        raise sensor.SensorError("历史计算超出有限数值范围。")
    return result


def evaluate_day(rows, index, config):
    window, samples = config['return_window'], config['baseline_observations']

    def r5(end):
        result = Decimal(1)
        for row in rows[end-window+1:end+1]:
            result *= 1 + decimal(row['pct_chg']) / 100
        return result - 1

    current = r5(index)
    baseline = [abs(r5(i)) for i in range(index-samples, index)]
    count = sum(value <= abs(current) for value in baseline)
    percentile = Decimal(count) / samples
    denom = median(decimal(row['amount']) for row in rows[index-config['amount_lookback']:index])
    ratio = decimal(rows[index]['amount']) / denom if denom > 0 else None
    abs_return_passed = abs(current) >= decimal(config['abs_return_min'])
    percentile_passed = percentile >= decimal(config['percentile_min'])
    amount_passed = ratio is not None and ratio >= decimal(config['amount_ratio_min'])
    price_hit = abs_return_passed and percentile_passed
    return {
        'trade_date': rows[index]['trade_date'], 'r5': number(current),
        'historical_percentile': number(percentile), 'historical_le_count': count,
        'historical_samples': samples,
        'baseline_range': [rows[index-samples]['trade_date'], rows[index-1]['trade_date']],
        'amount_median_cny': number(denom * 1000),
        'amount_ratio': number(ratio) if ratio is not None else None,
        'direction': 1 if current > 0 else -1 if current < 0 else 0,
        'price_hit': price_hit,
        'abs_return_passed': abs_return_passed, 'percentile_passed': percentile_passed,
        'amount_passed': amount_passed, 'hit': price_hit and amount_passed,
    }


def evaluate(rows, as_of_date, config):
    result = {'status': 'NO_DATA', 'reason': '目标日无记录；未确认休市/停牌/入库状态。'}
    if not rows or rows[-1]['trade_date'] != as_of_date:
        return result
    if len(rows) < config['min_history']:
        return {**result, 'status': 'INSUFFICIENT_HISTORY', 'reason': '有效历史不足最少记录数。'}
    persistence = config['persistence_observations']
    if ((day(as_of_date) - day(rows[-persistence]['trade_date'])).days > config['persistence_max_calendar_days']
            or (day(as_of_date) - day(rows[-config['recent_observations']]['trade_date'])).days > config['recent_max_calendar_days']):
        return {**result, 'status': 'STALE_HISTORY', 'reason': '最近观察跨度超过新鲜度限制。'}
    avg = sum(decimal(r['amount']) for r in rows[-config['liquidity_lookback']-1:-1]) * 1000 / config['liquidity_lookback']
    result['avg_amount_20_cny'] = number(avg)
    result['liquidity_passed'] = avg >= decimal(config['min_avg_amount_cny']) and rows[-1]['amount'] > 0
    if not result['liquidity_passed']:
        return {**result, 'status': 'LOW_LIQUIDITY', 'reason': '此前均成交额或目标日成交额未通过流动性过滤。'}
    evaluations = [evaluate_day(rows, i, config) for i in range(len(rows)-persistence, len(rows))]
    result['evaluations'] = evaluations
    if any(e['amount_ratio'] is None for e in evaluations):
        return {**result, 'status': 'INSUFFICIENT_HISTORY', 'reason': '此前成交额中位数为零，成交基准不可计算。'}
    current = evaluations[-1]
    hits = [e['trade_date'] for e in evaluations if e['hit'] and e['direction'] == current['direction']]
    result['same_direction_hit_dates'] = hits
    if not current['hit']:
        failed = [label for key, label in [('abs_return_passed', '收益绝对值'),
                  ('percentile_passed', '历史分位'), ('amount_passed', '成交倍数')] if not current[key]]
        reason = '目标日未达到条件：' + '、'.join(failed) + '。'
    elif len(hits) < config['min_same_direction_hits']:
        reason = '目标日命中，但最近观察中同向命中不足。'
    else:
        return {**result, 'status': 'MATCH', 'reason': '同向量价统计条件及质量过滤通过；经济机制未核验。'}
    return {**result, 'status': 'NO_MATCH', 'reason': reason}


def make_signal(item, report):
    metric = item['evaluations'][-1]
    synthetic = report['demo_only']
    code = item['ts_code']
    mechanism = '交易活跃度与重新定价同时增强，可能与信息重估/短期流动性压力有关；仅为待验证推测。'
    magnitude = {**metric, 'avg_amount_20_cny': item['avg_amount_20_cny']}
    return {
        'signal_id': f"MKT-{report['rule']['id']}-{report['as_of_date']}-{code}",
        'type': 'Market', 'instrument': code,
        'what_changed': f"{code} 在 {report['as_of_date']} 的 {report['config']['return_window']} 日复合收益 {metric['r5']:.6%}、历史分位 {metric['historical_percentile']:.6%}、成交额倍数 {metric['amount_ratio']:.6g}。",
        'anomaly': '历史量价统计条件命中；不等于错价或可交易机会。',
        'magnitude': magnitude,
        'money': f"此前{report['config']['liquidity_lookback']}有效日均成交额 {item['avg_amount_20_cny']} 元；amount 原单位千元，非净流入/收入/利润。",
        'evidence': [
            {'source': 'history-fixture.json（合成）' if synthetic else 'tushare:daily',
             'observed_at': report['as_of_date'],
             'fact': {'ts_code': code, 'observations_start': item['observations_start'],
                      'observations_count': item['valid_rows'], 'json_path': '#/observations',
                      'request_range': report['request_range'], 'fetched_at': item['fetched_at']}},
            {'source': sensor.DAILY_DOC, 'observed_at': report['generated_at'],
             'fact': '字段说明与行情同属一个提供者，非独立市场证据；pct_chg 为百分数，amount 为千元。'}],
        'mechanism': mechanism, 'possible_mechanism': mechanism,
        'persistence': '持续', 'persistence_note': '仅本规则最近观察同向命中；不推断经济持续性。',
        'same_direction_hit_dates': item['same_direction_hit_dates'],
        'evaluations': item['evaluations'],
        'data_quality': {'synthetic': synthetic, 'history_points': item['valid_rows'],
                         'history_sufficient': True, 'history_range': item['actual_range'],
                         'liquidity_verified': False, 'liquidity_filter_passed': True,
                         'freshness_passed': True, 'reliability': '合成数据，非行情' if synthetic else '单一提供者，未经独立交叉核验；未验证容量/滑点。'},
        'next_question': '人工核验相应日期的信息事件、经济机制、历史重复性和表达成本；补足原稿研究条件后才交 Researcher。',
        'task_version': f'{sensor.TASK_ID}@{sensor.VERSION}', 'role_spec_status': 'reviewed',
        'generated_at': report['generated_at'], 'demo_only': synthetic, 'research_eligible': False,
    }


def run_history(args):
    report = {
        'task_id': sensor.TASK_ID, 'task_version': sensor.VERSION, 'role_spec_status': 'reviewed',
        'mode': 'history', 'generated_at': utc_now(), 'source': args.source,
        'demo_only': args.source != 'tushare', 'research_eligible': False,
        'research_blockers': ['统计量价候选，非已验证错价/策略', '机制、独立数据可靠性、表达成本待人工核验'],
        'as_of_date': args.as_of_date or taipei_today(), 'trade_date': '', 'ts_code': '',
        'rule': {'id': 'price_volume_stress_v1', 'status': 'trial' if args.source == 'tushare' else 'demo_only'},
        'config': None, 'config_sha256': None, 'request_range': None,
        'status': 'ERROR', 'observations': [], 'signals': [], 'instruments': [],
        'coverage_complete': False, 'coverage': {}, 'total_matches': 0, 'truncated_matches': 0,
    }
    try:
        config, digest = load_config(args.config)
        codes = sorted(set(config['universe']))
        report.update(config=config, config_sha256=digest, expected_instruments=codes)
        if args.trade_date or args.ts_code or args.demo_abs_pct is not None:
            raise sensor.SensorError('history 不接受 demo 的 trade-date / ts-code / demo-abs-pct。')
        if args.source not in ('fixture', 'tushare'):
            raise sensor.SensorError('source 只允许 fixture 或 tushare。')
        target = report['as_of_date']
        target_day = day(target)
        if target_day > day(taipei_today()):
            raise sensor.SensorError('as-of-date 不允许未来日期。')
        start = (target_day - timedelta(days=config['lookback_calendar_days'])).strftime('%Y%m%d')
        report.update(trade_date=target, request_range={'start_date': start, 'end_date': target})
        fixture = None
        if args.source == 'fixture':
            fixture = json.loads(Path(args.history_fixture).read_text(encoding='utf-8'))
            if not isinstance(fixture, dict) or not isinstance(fixture.get('observations'), list):
                raise sensor.SensorError('历史 fixture 缺少 observations 数组。')
            if any(not isinstance(r, dict) or r.get('ts_code') not in codes for r in fixture['observations']):
                raise sensor.SensorError('历史 fixture 存在未知代码或无效行。')
        client = DailyClient(config)
        for code in codes:
            item = {'ts_code': code, 'status': 'ERROR', 'reason': '', 'fetched_at': utc_now(),
                    'request_range': report['request_range'], 'actual_range': None,
                    'valid_rows': 0, 'observations_start': len(report['observations'])}
            report['instruments'].append(item)
            try:
                rows = ([r for r in fixture['observations'] if r['ts_code'] == code] if fixture is not None
                        else client.fetch(start, target, code))
                item['fetched_at'] = utc_now()
                rows = validate_history(rows, start, target, code)
                item.update(valid_rows=len(rows), actual_range=[rows[0]['trade_date'], rows[-1]['trade_date']] if rows else None)
                report['observations'].extend(rows)
                item.update(evaluate(rows, target, config))
            except sensor.SensorError as exc:
                item.update(status='ERROR', reason=str(exc))
            except Exception as exc:
                item.update(status='ERROR', reason=f'历史处理失败（{type(exc).__name__}）；未记录原始内容。')
        items = report['instruments']
        report['coverage'] = {
            'expected': codes,
            'evaluated': [i['ts_code'] for i in items if i['status'] in COMPLETE],
            'matched': [i['ts_code'] for i in items if i['status'] == 'MATCH'],
            'filtered': [i['ts_code'] for i in items if i['status'] in {'NO_MATCH', 'LOW_LIQUIDITY', 'STALE_HISTORY', 'INSUFFICIENT_HISTORY'}],
            'missing': [i['ts_code'] for i in items if i['status'] == 'NO_DATA'],
            'failed': [i['ts_code'] for i in items if i['status'] == 'ERROR'],
        }
        report['coverage_complete'] = all(i['status'] in COMPLETE for i in items)
        matches = [make_signal(i, report) for i in items if i['status'] == 'MATCH']
        matches.sort(key=lambda s: (-s['magnitude']['historical_percentile'], -abs(s['magnitude']['r5']),
                                    -s['magnitude']['amount_ratio'], s['instrument']))
        report['total_matches'] = len(matches)
        report['truncated_matches'] = max(0, len(matches) - config['max_signals'])
        if report['coverage']['failed']:
            report['error'] = '部分标的发生取数/数据契约错误，整轮候选已抑制；逐标的原因见 instruments。'
        else:
            report['signals'] = matches[:config['max_signals']]
            report['status'] = ('SIGNALS' if matches else 'NO_MATCH' if report['coverage']['evaluated']
                                else 'NO_DATA' if all(i['status'] == 'NO_DATA' for i in items) else 'INSUFFICIENT_DATA')
    except sensor.SensorError as exc:
        report['error'] = str(exc)
    except Exception as exc:
        report['error'] = f'历史运行失败（{type(exc).__name__}）；未记录原始内容。'
    if report['status'] == 'ERROR':
        report['signals'] = []
    return report
