"""US Domestic equity fund-flow reversal -> a falsifiable Researcher R1 packet."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
from http.client import HTTPException
import json
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from us_sources import Blocked, amount, canonical, parse_ici, parse_spy


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / 'config/market-v1.json'
FIXTURE = ROOT / 'scripts/market/fixtures/us-flow/manifest.json'
NY = ZoneInfo('America/New_York')
VERSION = '0.3.0'
MECHANISM = ('共同基金净申赎与ETF净发行的持续方向变化可能改变基金体系对美国股票的边际配置需求，'
             '进而形成可重复的底层需求与定价压力；这是待R1核验的机制，不是已证实的价格因果或错价。')
COUNTER = ['现金缓冲或实物申赎可能削弱即时底层买卖，其他持有人也可能吸收配置变化。',
           '载体迁移、季节性、类别重分或估计修订可能解释反转，市场可能已预先反映。',
           'SPY仅为美国股票类别观测载体，不精确复制ICI类别；表达成本、容量和工具匹配仍未知。']
QUESTION = ('R1核验Money/Mechanism：这次申赎/发行反转能否形成可重复的底层需求压力，'
            '还是载体迁移、现金管理、季节性或修订？市场是否已反映，哪些证据能KILL机制？')


def now():
    return datetime.now(timezone.utc)


def timestamp(value):
    if not isinstance(value, str):
        raise Blocked('快照取得时间必须是带时区ISO时间。')
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if result.tzinfo is None:
            raise ValueError
        return result.astimezone(timezone.utc)
    except ValueError:
        raise Blocked('快照取得时间必须是带时区ISO时间。') from None


def as_of(value):
    if not value:
        return now()
    if re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', value):
        try:
            return (datetime.fromisoformat(value) + timedelta(days=1)).replace(tzinfo=NY).astimezone(timezone.utc)
        except ValueError:
            raise ValueError('as-of日期无效。') from None
    try:
        return timestamp(value)
    except Blocked:
        raise ValueError('as-of必须为ISO日期或带时区时间。') from None


def availability(published_date):
    return (datetime.fromisoformat(published_date) + timedelta(days=1)).replace(tzinfo=NY).astimezone(timezone.utc)


def as_of_day(at):
    # A midnight cutoff represents the day just completed.
    return (at.astimezone(NY)-timedelta(microseconds=1)).date()


def load_config(path):
    raw = Path(path).read_bytes()
    config = json.loads(raw)
    expected = json.loads(CONFIG.read_text())
    if not isinstance(config, dict) or set(config) != set(expected):
        raise ValueError('US流向配置字段不符。')
    for key in ('task_version', 'rule_id', 'ici_url', 'instrument_url', 'category', 'unit', 'instrument_ticker'):
        if config[key] != expected[key]:
            raise ValueError('US流向配置身份/来源/单位不符。')
    for key in set(config)-{'task_version', 'rule_id', 'ici_url', 'instrument_url', 'category', 'unit', 'instrument_ticker'}:
        value = config[key]
        if type(value) not in (int, float) or not Decimal(str(value)).is_finite() or value <= 0:
            raise ValueError('US流向配置阈值必须有限且为正。')
    if config['min_week_gap_days'] > config['max_week_gap_days']:
        raise ValueError('周间隔配置不符。')
    return config, hashlib.sha256(raw).hexdigest()


def fetch_public(url):
    """No secrets or Tushare headers enter this public-source request path."""
    try:
        with urlopen(Request(url, headers={'User-Agent': 'MarketSensor/0.3.0'}), timeout=30) as response:
            raw = response.read(4*1024*1024+1)
            final = response.geturl()
            if urlsplit(final).scheme != 'https' or urlsplit(final).hostname != urlsplit(url).hostname:
                raise Blocked('公开源重定向到非原HTTPS主机；未接受为数据。')
            if len(raw) > 4*1024*1024:
                raise Blocked('公开响应过大，未接受为完整来源。')
            if 'html' not in response.headers.get('Content-Type', '').lower():
                raise Blocked('公开响应不是支持的原始HTML；不从截图/PDF猜数值。')
            return raw, now().isoformat()
    except HTTPError as exc:
        raise Blocked(f'公开来源HTTP {exc.code}；不绕过限制或回退其他数据。') from None
    except (URLError, OSError, HTTPException) as exc:
        raise Blocked(f'公开来源传输受阻/响应不完整（{type(exc).__name__}）；未取得有效快照。') from None


def source_url_valid(url, canonical_url):
    # V1 deliberately accepts the two original HTML endpoints, not arbitrary mirrors.
    return isinstance(url, str) and url.rstrip('/') == canonical_url.rstrip('/')


def acquire_source(name, config, args, manifest, synthetic):
    url = config['ici_url' if name == 'ici' else 'instrument_url']
    if args.input_mode == 'live_http':
        raw, retrieved = fetch_public(url)
        entry = {'source_url': url, 'retrieved_at': retrieved, 'sha256': hashlib.sha256(raw).hexdigest()}
    else:
        entry = manifest.get('sources', {}).get(name)
        if not isinstance(entry, dict) or not source_url_valid(entry.get('source_url'), url):
            raise Blocked('快照缺少原始来源URL或不是本规则原始来源。')
        timestamp(entry.get('retrieved_at'))
        if not isinstance(entry.get('file'), str) or not isinstance(entry.get('sha256'), str):
            raise Blocked('快照缺少文件名/原始字节哈希。')
        try:
            path = Path(args.snapshot_manifest).parent / entry['file']
            raw = path.read_bytes()
        except OSError:
            raise Blocked('原始快照文件无法读取。') from None
        if len(raw) > 4*1024*1024 or hashlib.sha256(raw).hexdigest() != entry['sha256']:
            raise Blocked('快照过大或原始字节哈希不符。')
    if not synthetic and (b'SYNTHETIC FIXTURE' in raw or b'data-synthetic="true"' in raw):
        raise Blocked('合成材料不能通过改模式/声明升级为真实来源。')
    digest = hashlib.sha256(raw).hexdigest()
    directory = args.output.parent / 'sources'
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f'{name}-{digest}.html'
    path.write_bytes(raw)
    return raw, {'name': name, 'source_url': url, 'retrieved_at': entry['retrieved_at'],
                 'sha256': digest, 'raw_file': 'sources/'+path.name, 'synthetic': synthetic}


def check_time(data, source, at, config, is_flow):
    retrieved = timestamp(source['retrieved_at'])
    if retrieved > at:
        raise Blocked('快照晚于as_of取得；当前修订值不能回填为历史PIT数据。')
    if not source['synthetic'] and retrieved > now():
        raise Blocked('快照取得时间在未来，不能作为已取得来源。')
    today = as_of_day(at)
    if is_flow:
        published = datetime.fromisoformat(data['published_date']).date()
        usable = availability(data['published_date'])
        data['available_after'] = usable.isoformat()
        if at < usable:
            raise Blocked('发布日期只有date精度；纽约该日结束前不可使用。')
        if (today-published).days > config['max_age_days']:
            raise Blocked('发布日至as_of超过新鲜度限制。')
        latest = datetime.fromisoformat(data['selected_rows'][-1]['period_end']).date()
        if not 0 <= (published-latest).days <= config['max_publication_lag_days']:
            raise Blocked('最新报告周晚于发布日或距发布日过旧。')
        dates = [datetime.fromisoformat(r['period_end']).date() for r in data['selected_rows']]
        if any(not config['min_week_gap_days'] <= (b-a).days <= config['max_week_gap_days'] for a, b in zip(dates, dates[1:])):
            raise Blocked('四周缺周/间隔异常；不插值或补零。')
    else:
        date = datetime.fromisoformat(data['price_date']).date()
        if data['price_date'] != data['volume_date'] or not 0 <= (today-date).days <= config['max_age_days']:
            raise Blocked('工具价格/成交股数不同日、在未来或已过期。')
        if Decimal(data['notional_proxy_usd']) < Decimal(str(config['min_notional_usd'])):
            raise Blocked('美元成交额代理低于1亿美元粗筛；保留观察，不放行。')


def reversal(rows, config):
    values = [Decimal(r['value_usd_million']) for r in rows]
    before, after = sum(values[:2]), sum(values[2:])
    threshold = Decimal(str(config['min_period_net_usd_million']))
    direction = None
    if all(v > 0 for v in values[:2]) and all(v < 0 for v in values[2:]):
        direction = 'outflow_reversal'
    elif all(v < 0 for v in values[:2]) and all(v > 0 for v in values[2:]):
        direction = 'inflow_reversal'
    hit = direction is not None and abs(before) >= threshold and abs(after) >= threshold
    return {'rule_hit': hit, 'direction': direction,
            'before_net_usd_million': canonical(before), 'after_net_usd_million': canonical(after),
            'change_usd_million': canonical(after-before), 'unit': 'USD million', 'rows': rows,
            'reason': '四个独立周的方向与物质性通过。' if hit else '未同时满足前后各两周同向反转及两个区间物质性；零值不计方向。'}


def signal_for(report, flow, instrument):
    evaluation = report['rule_evaluation']
    fingerprint_data = {'rows': flow['selected_rows'], 'published_date': flow['published_date'],
                        'category': flow['category'], 'unit': flow['unit'], 'config': report['config'], 'task_version': VERSION}
    fingerprint = hashlib.sha256(json.dumps(fingerprint_data, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
    sources = report['sources']
    eligible = not report['demo_only']
    return {
        'signal_id': f"MKT-{report['rule']['id']}-{flow['selected_rows'][-1]['period_end']}-{evaluation['direction']}",
        'observation_id': fingerprint, 'data_fingerprint': fingerprint,
        'type': 'Market', 'signal_class': 'Flow Shift', 'instrument': 'SPY（类别观测载体，非交易选择）',
        'what_changed': f"Domestic equity前两周净额{evaluation['before_net_usd_million']}、后两周净额{evaluation['after_net_usd_million']}，单位USD million，方向{evaluation['direction']}。",
        'anomaly': 'ICI共同基金净新现金流与ETF净发行合并估计发生连续两周方向反转。',
        'magnitude': evaluation,
        'money': '行业基金体系估计申赎/净发行配置，非全市场资金流、股票成交额、收入或利润。',
        'mechanism': MECHANISM, 'possible_mechanism': MECHANISM,
        'persistence': '持续', 'persistence_note': '仅四个不重叠报告周中前后各两周同向；数据估计且可能修订，不推断永久持续。',
        'counter_evidence_and_unknowns': COUNTER,
        'next_question': QUESTION,
        'evidence': [{**s, 'observed_at': flow['published_date'] if s['name'] == 'ici' else instrument['price_date'],
                      'fact': flow if s['name'] == 'ici' else instrument} for s in sources],
        'source_dependency_note': 'ICI数值与ICI方法说明是同一提供者；发行人只支持工具身份/流动性，不独立验证基金流或价格因果。',
        'data_quality': {'synthetic': report['demo_only'], 'history_points': 4, 'history_sufficient': True,
                         'liquidity_verified': True, 'liquidity_scope': '仅单日美元成交额代理粗筛，不代表滑点/容量/成本已验收。',
                         'published_date': flow['published_date'], 'published_precision': 'date',
                         'vintage_sha256': sources[0]['sha256'], 'long_history_percentile': None,
                         'reliability': '合成业务夹具，非行情' if report['demo_only'] else '原始发布估计；修订与来源可追溯，价格因果待R1核验。'},
        'generated_at': report['generated_at'], 'task_version': 'market-sensor@'+VERSION,
        'role_spec_status': 'reviewed', 'demo_only': report['demo_only'], 'research_eligible': eligible,
        'input_mode': report['input_mode'], 'config_sha256': report['config_sha256'],
    }


def deduplicate(signal, previous, at):
    if (not isinstance(previous, dict) or previous.get('mode') != 'flow'
            or not isinstance(previous.get('signals'), list)):
        return signal, {'status': 'unverified_no_previous_report', 'scope': 'previous_report_only'}
    for old in previous.get('signals', []):
        if not isinstance(old, dict):
            continue
        if old.get('signal_id') != signal['signal_id']:
            continue
        if (old.get('observation_id') == signal['observation_id'] and old.get('task_version') == signal['task_version']
                and old.get('demo_only') == signal['demo_only'] and old.get('research_eligible') == signal['research_eligible']):
            try:
                if (timestamp(old.get('generated_at')) > now() or not isinstance(old.get('evidence'), list)
                        or any(not isinstance(e, dict) or timestamp(e.get('retrieved_at')) > at for e in old['evidence'])):
                    raise Blocked('前次Signal来自未来。')
            except Blocked:
                return signal, {'status': 'unverified_invalid_previous_time', 'scope': 'previous_report_only'}
            return old, {'status': 'same_observation_reused', 'scope': 'previous_report_only', 'is_new_evidence': False}
        if old.get('demo_only') != signal['demo_only']:
            return signal, {'status': 'unverified_source_class_changed', 'scope': 'previous_report_only'}
        signal['revision_of'] = old.get('observation_id')
        return signal, {'status': 'revised_observation', 'scope': 'previous_report_only'}
    return signal, {'status': 'no_match_in_previous_report', 'scope': 'previous_report_only'}


def run_flow(args):
    report = {'task_id': 'market-sensor', 'task_version': VERSION, 'role_spec_status': 'reviewed', 'mode': 'flow',
              'generated_at': now().isoformat(), 'as_of': None, 'input_mode': args.input_mode, 'source': args.input_mode,
              'demo_only': args.input_mode == 'synthetic_fixture', 'research_eligible': False,
              'rule': {'id': 'us_domestic_fund_flow_reversal_v1', 'status': 'trial'},
              'config': None, 'config_sha256': None, 'status': 'ERROR', 'signals': [], 'observations': [],
              'sources': [], 'coverage': {}, 'coverage_complete': False, 'blockers': [],
              'dedup': {'status': 'not_applicable', 'scope': 'previous_report_only'},
              'tushare_us_preflight': {'status': 'NOT_RUN', 'reason': '仅Actions runner可使用既有Secret，权限/ETF覆盖/量单位未核验。'}}
    try:
        if args.demo_abs_pct is not None or args.trade_date or args.ts_code or args.as_of_date:
            raise ValueError('flow不接受legacy demo/history的参数；使用--as-of。')
        config, digest = load_config(args.config)
        report.update(config=config, config_sha256=digest)
        requested_at = as_of(args.as_of) if args.as_of else None
        if getattr(args, 'us_preflight_report', None):
            try:
                probe = json.loads(Path(args.us_preflight_report).read_text())
                if not isinstance(probe, dict) or probe.get('api_name') != 'us_daily':
                    raise ValueError
                report['tushare_us_preflight'] = probe
            except (OSError, ValueError):
                report['tushare_us_preflight'] = {'status': 'BLOCKED', 'reason': 'runner预检报告不可读；不据此验证工具单位。'}
        manifest = {}
        if args.input_mode != 'live_http':
            try:
                manifest = json.loads(Path(args.snapshot_manifest).read_text())
            except (OSError, ValueError):
                raise Blocked('快照manifest无法读取/不是有效JSON。') from None
            if (not isinstance(manifest, dict) or manifest.get('schema_version') != 1
                    or type(manifest.get('synthetic')) is not bool or not isinstance(manifest.get('sources'), dict)):
                raise Blocked('快照manifest缺少版本/synthetic/来源元数据。')
            if args.input_mode == 'synthetic_fixture' and not manifest['synthetic']:
                raise Blocked('synthetic_fixture必须明确标synthetic=true。')
            report['demo_only'] = manifest['synthetic']
        parsed = {}
        for name, parser in [('ici', parse_ici), ('instrument', parse_spy)]:
            report['coverage'][name] = {'status': 'BLOCKED'}
            try:
                raw, source = acquire_source(name, config, args, manifest, report['demo_only'])
                report['sources'].append(source)
                parsed[name] = parser(raw)
                report['observations'].append({'source': name, 'data': parsed[name]})
                report['coverage'][name] = {'status': 'PARSED_PENDING_TIME_CHECK'}
            except Blocked as exc:
                report['coverage'][name]['reason'] = str(exc)
                report['blockers'].append(f'{name}: {exc}')
        at = requested_at or now()
        report['as_of'] = at.isoformat()
        report['generated_at'] = now().isoformat()
        # Always replace the manifest, even when blocked, so it cannot describe an old run.
        archive = {'schema_version': 1, 'synthetic': report['demo_only'], 'sources': {
            s['name']: {'file': s['raw_file'], 'source_url': s['source_url'],
                        'retrieved_at': s['retrieved_at'], 'sha256': s['sha256']} for s in report['sources']}}
        args.output.parent.mkdir(parents=True, exist_ok=True)
        (args.output.parent/'source-manifest.json').write_text(json.dumps(archive, ensure_ascii=False, indent=2)+'\n')
        for name, data in parsed.items():
            source = next(s for s in report['sources'] if s['name'] == name)
            try:
                check_time(data, source, at, config, name == 'ici')
                report['coverage'][name] = {'status': 'VALID'}
            except Blocked as exc:
                report['coverage'][name] = {'status': 'BLOCKED', 'reason': str(exc)}
                report['blockers'].append(f'{name}: {exc}')
        if 'ici' in parsed and report['coverage']['ici']['status'] == 'VALID':
            report['rule_evaluation'] = reversal(parsed['ici']['selected_rows'], config)
        report['coverage_complete'] = all(s['status'] == 'VALID' for s in report['coverage'].values())
        report['rule']['status'] = 'demo_only' if report['demo_only'] else 'trial'
        if report['blockers']:
            report['status'] = 'BLOCKED'
        elif report['rule_evaluation']['rule_hit']:
            report['status'] = 'SIGNALS'
            signal = signal_for(report, parsed['ici'], parsed['instrument'])
            signal, report['dedup'] = deduplicate(signal, getattr(args, 'previous_report_data', None), at)
            report['signals'] = [signal]
            report['research_eligible'] = signal['research_eligible']
        else:
            report['status'] = 'NO_SIGNAL'
        report['research_blockers'] = report['blockers'] or (['synthetic_fixture不能作为真实研究输入。'] if report['demo_only'] else [])
    except Blocked as exc:
        report.update(status='BLOCKED', blockers=[str(exc)], research_blockers=[str(exc)])
    except Exception as exc:
        report.update(status='ERROR', error=f'US监测参数/处理失败（{type(exc).__name__}）；未记录原始异常内容。')
    return report


def facts_table(rows):
    return '\n'.join(['报告周末 | Domestic equity估计（USD million）', '--- | ---',
                      *[f"{r['period_end']} | {r['value_usd_million']}" for r in rows]])


def render_packet(report):
    lines = ['# Market → Researcher R1 证据包', '', f"运行状态：{report['status']}；任务：market-sensor@{VERSION}",
             f"输入：{report['input_mode']}；demo_only={str(report['demo_only']).lower()}；research_eligible={str(report['research_eligible']).lower()}", '']
    if not report['signals']:
        lines += ['本轮无合格交接Signal。BLOCKED不是无异常；不要把观察材料当作已过门槛的Signal。',
                  *report.get('blockers', []), '']
        for observation in report['observations']:
            if observation['source'] == 'ici':
                lines += [facts_table(observation['data']['selected_rows']), '']
        return '\n'.join(lines)+'\n'
    signal = report['signals'][0]
    lines += ['**SYNTHETIC：仅业务路径演示，不交真实Research。**' if signal['demo_only'] else '**可交R1核验；不是Hypothesis、交易或策略有效性结论。**', '',
              f"Signal ID：{signal['signal_id']}", f"Observation ID：{signal['observation_id']}",
              f"Generated At：{signal['generated_at']}", f"Task Version：{signal['task_version']}",
              f"配置SHA-256：{signal['config_sha256']}", f"重复核对：{report['dedup']['status']}（仅与提供的前次报告比较；无全局新证据承诺）", '',
              '## 原始四周事实与钱', '', facts_table(signal['magnitude']['rows']), '', signal['what_changed'], signal['money'],
              '这是共同基金净新现金流与ETF净发行合并的行业周估计；不是股票成交额、全市场净流量或月度实际值。',
              signal['persistence_note'], '', '## 潜在机制（待R1验证）', '', signal['possible_mechanism'], '',
              '## 反证与关键未知', '', *['- '+c for c in signal['counter_evidence_and_unknowns']], '',
              '## 工具与来源事实', '']
    for evidence in signal['evidence']:
        lines += [f"- 原始URL：{evidence['source_url']}", f"- 取得时间：{evidence['retrieved_at']}；原始SHA-256：{evidence['sha256']}"]
        fact = evidence['fact']
        if evidence['name'] == 'ici':
            lines += [f"- 发布日：{fact['published_date']}，精度date；最早保守可用时间：{fact['available_after']}；类别{fact['category']}，单位{fact['unit']}。"]
        else:
            lines += [f"- {fact['ticker']} / {fact['exchange']} / {fact['currency']}；同日{fact['price_date']}价格USD {fact['price_usd']} × Exchange Volume {fact['exchange_volume_shares']} shares = USD {fact['notional_proxy_usd']}。", fact['role'], fact['volume_scope']]
    lines += ['', signal['source_dependency_note'], '', '## R1下一问题与停止', '', signal['next_question'],
              'R1只需核验Money/Mechanism并可KILL或ESCALATE；合法KILL保留理由，不要求用户先完成机制研究。',
              '若进入后续研究，再核查持续性、可捕获性与表达成本；本包不授权交易或投入资本。', '']
    return '\n'.join(lines)


def render_report(report):
    lines = ['# 美股基金配置监测', '', f"状态：{report['status']}；as_of：{report['as_of']}；运行时间：{report['generated_at']}",
             f"输入：{report['input_mode']}；配置SHA-256：{report['config_sha256']}",
             f"demo_only={str(report['demo_only']).lower()}；research_eligible={str(report['research_eligible']).lower()}", '',
             '## 来源覆盖与阻塞', '', '来源 | 状态 | 原因', '--- | --- | ---',
             *[f"{name} | {value['status']} | {value.get('reason', '')}" for name, value in report['coverage'].items()], '',
             *report.get('blockers', []), report.get('error', ''), '',
             '## 观察与业务判定', '']
    for observation in report['observations']:
        if observation['source'] == 'ici':
            lines += [facts_table(observation['data']['selected_rows']), '']
    if report.get('rule_evaluation'):
        lines.append(report['rule_evaluation']['reason'])
    lines += ['', '## 来源与人工交接', '',
              *[f"- {s['name']}：{s['source_url']}；取得{s['retrieved_at']}；SHA-256 {s['sha256']}；原文{s['raw_file']}" for s in report['sources']],
              '', '完整四周事实、机制、反证和R1问题见同目录researcher-packet.md；合格真实包可人工保存到Drive Signals/Market，不先补机制研究。',
              'BLOCKED/合成包不得当真实Signal；NO_SIGNAL仅表示有效完整评估未触发本规则。',
              'SPY仅证明相关工具与粗流动性，不代表交易选择。无买卖建议、价格因果或盈利承诺。', '']
    return '\n'.join(lines)
