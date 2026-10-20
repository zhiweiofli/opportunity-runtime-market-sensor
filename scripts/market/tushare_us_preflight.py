"""Runner-only US daily permission/coverage probe. No ETF volume-unit inference."""

import argparse
from datetime import datetime, timedelta, timezone
import json
import math
import os
from pathlib import Path
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


def probe(trade_date):
    report = {'status': 'BLOCKED', 'api_name': 'us_daily', 'ts_code': 'SPY', 'trade_date': trade_date,
              'generated_at': datetime.now(timezone.utc).isoformat(), 'coverage_verified': False,
              'volume_unit_verified': False, 'research_eligible': False}
    # The public-source process never calls this path and receives no Secret.
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        return {**report, 'reason': '只允许在Actions runner预检；未读取token。'}
    token = os.environ.get('TUSHARE_TOKEN', '').strip()
    if not token:
        return {**report, 'reason': 'runner缺少既有Secret；不回退其他接口。'}
    try:
        payload = {'api_name': 'us_daily', 'token': token,
                   'params': {'ts_code': 'SPY', 'trade_date': trade_date},
                   'fields': 'ts_code,trade_date,close,vol,amount'}
        request = Request('https://api.tushare.pro', data=json.dumps(payload).encode(),
                          headers={'Content-Type': 'application/json'}, method='POST')
        with urlopen(request, timeout=30) as response:
            result = json.load(response)
        if not isinstance(result, dict) or type(result.get('code')) is not int or result['code'] != 0:
            return {**report, 'reason': 'us_daily权限/API未通过，不记录原始错误体。'}
        data = result.get('data')
        if (not isinstance(data, dict) or not isinstance(data.get('fields'), list)
                or not isinstance(data.get('items'), list)
                or len(set(data['fields'])) != len(data['fields'])
                or not {'ts_code', 'trade_date', 'close', 'vol', 'amount'}.issubset(data['fields'])):
            return {**report, 'reason': 'us_daily返回契约不符。'}
        rows = []
        for row in data['items']:
            if not isinstance(row, list) or len(row) != len(data['fields']):
                return {**report, 'reason': 'us_daily行结构不符。'}
            record = dict(zip(data['fields'], row))
            if record['ts_code'] != 'SPY' or record['trade_date'] != trade_date:
                return {**report, 'reason': 'SPY代码/日期覆盖不符。'}
            for field in ('close', 'vol', 'amount'):
                value = record[field]
                if type(value) not in (int, float) or not math.isfinite(value) or value < 0 or (field == 'close' and value == 0):
                    return {**report, 'reason': 'us_daily数值契约不符。'}
            rows.append({key: record[key] for key in ('ts_code', 'trade_date', 'close', 'vol', 'amount')})
        if len(rows) > 1:
            return {**report, 'reason': '同代码同日重复，覆盖未通过。'}
        # Do not infer shares from a field named vol, or treat daily availability as ETF identity proof.
        return {**report, 'status': 'RESPONSE_RECEIVED_UNITS_UNVERIFIED', 'permission_response_ok': True,
                'rows': rows, 'reason': 'API可响应；ETF身份和成交量单位仍未核验，不能据此签流动性通过。'}
    except Exception as exc:
        return {**report, 'reason': f'us_daily预检受阻（{type(exc).__name__}）；未记录原始响应/异常。'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--trade-date', default='')
    parser.add_argument('--output', type=Path, default=Path('outputs/market/tushare-us-preflight.json'))
    args = parser.parse_args()
    if args.trade_date:
        datetime.strptime(args.trade_date, '%Y%m%d')
        date = args.trade_date
    else:
        previous = datetime.now(ZoneInfo('America/New_York')).date()-timedelta(days=1)
        while previous.weekday() >= 5:
            previous -= timedelta(days=1)
        date = previous.strftime('%Y%m%d')
    report = probe(date)
    report['date_selection_note'] = '显式日期或此前工作日探测；未用交易日历，不保证开市。'
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    print(report['status']+'：us_daily预检报告已保存；不用于流动性放行。')


if __name__ == '__main__':
    main()
