"""Select explicit event semantics without interpolating inputs into shell code."""

import os
from pathlib import Path
import shutil
import sys

import market_sensor


def arguments(event, inputs):
    if event == 'schedule':
        args = ['--mode', 'flow', '--input-mode', 'live_http']
        if inputs.get('INPUT_US_PREFLIGHT_REPORT'):
            args += ['--us-preflight-report', inputs['INPUT_US_PREFLIGHT_REPORT']]
        return args
    if event != 'workflow_dispatch':
        raise market_sensor.SensorError('只接受 schedule 或 workflow_dispatch 事件。')
    mode = inputs.get('INPUT_MODE', 'flow')
    source = inputs.get('INPUT_SOURCE', 'fixture')
    args = ['--mode', mode, '--source', source]
    if mode == 'flow':
        args += ['--input-mode', inputs.get('INPUT_INPUT_MODE', 'live_http'),
                 '--as-of', inputs.get('INPUT_AS_OF', '')]
        manifest = inputs.get('INPUT_SNAPSHOT_MANIFEST', '')
        if inputs.get('INPUT_SNAPSHOT_RUN_ID'):
            manifest = 'inputs/snapshot/source-manifest.json'
        if manifest:
            args += ['--snapshot-manifest', manifest]
        if inputs.get('INPUT_PREVIOUS_RUN_ID'):
            args += ['--previous-report', 'inputs/previous/report.json']
        if inputs.get('INPUT_INPUT_MODE', 'live_http') == 'live_http' and inputs.get('INPUT_US_PREFLIGHT_REPORT'):
            args += ['--us-preflight-report', inputs['INPUT_US_PREFLIGHT_REPORT']]
    elif mode == 'history':
        args += ['--as-of-date', inputs.get('INPUT_AS_OF_DATE', '')]
    else:
        args += ['--trade-date', inputs.get('INPUT_TRADE_DATE', ''),
                 '--ts-code', inputs.get('INPUT_TS_CODE', ''),
                 '--demo-abs-pct', inputs.get('INPUT_DEMO_ABS_PCT', '5')]
    return args


if __name__ == '__main__':
    # Preserve content-addressed previous originals for a reused Signal's references.
    previous_sources = Path('inputs/previous/sources')
    if previous_sources.is_dir():
        target = Path('outputs/market/sources')
        target.mkdir(parents=True, exist_ok=True)
        for source in previous_sources.glob('*.html'):
            shutil.copyfile(source, target/source.name)
    sys.exit(market_sensor.main(arguments(os.environ.get('GITHUB_EVENT_NAME'), os.environ)))
