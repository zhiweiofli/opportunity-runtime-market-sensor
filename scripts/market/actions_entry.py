"""Select explicit event semantics without interpolating inputs into shell code."""

import os
import sys

import market_sensor


def arguments(event, inputs):
    if event == 'schedule':
        return ['--mode', 'history', '--source', 'tushare']
    if event != 'workflow_dispatch':
        raise market_sensor.SensorError('只接受 schedule 或 workflow_dispatch 事件。')
    mode = inputs.get('INPUT_MODE', 'demo')
    source = inputs.get('INPUT_SOURCE', 'fixture')
    args = ['--mode', mode, '--source', source]
    if mode == 'history':
        args += ['--as-of-date', inputs.get('INPUT_AS_OF_DATE', '')]
    else:
        args += ['--trade-date', inputs.get('INPUT_TRADE_DATE', ''),
                 '--ts-code', inputs.get('INPUT_TS_CODE', ''),
                 '--demo-abs-pct', inputs.get('INPUT_DEMO_ABS_PCT', '5')]
    return args


if __name__ == '__main__':
    sys.exit(market_sensor.main(arguments(os.environ.get('GITHUB_EVENT_NAME'), os.environ)))
