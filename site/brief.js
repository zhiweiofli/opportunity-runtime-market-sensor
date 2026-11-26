(function () {
  'use strict';
  var REPO_ROOT = 'https://github.com/zhiweiofli/opportunity-runtime-market-sensor/blob/main/';
  var SAFE_PATH = /^drive-mirror\/files\/(?:[A-Za-z0-9._-]+\/)*[A-Za-z0-9._-]+$/;
  var statusEl = document.getElementById('brief-status');
  var healthEl = document.getElementById('brief-health');
  var judgeEl = document.getElementById('brief-judge');
  var trendsEl = document.getElementById('brief-trends');
  var gapsEl = document.getElementById('brief-gaps');
  var researchEl = document.getElementById('brief-research');

  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text !== undefined && text !== null) node.textContent = String(text);
    return node;
  }

  function safeHref(path) {
    if (typeof path !== 'string' || path.split('/').includes('..') || !SAFE_PATH.test(path)) return null;
    return REPO_ROOT + path.split('/').map(encodeURIComponent).join('/');
  }

  function appendSafeLink(parent, path, label) {
    var href = safeHref(path);
    if (!href) return false;
    var a = el('a', '', label);
    a.href = href;
    a.target = '_blank';
    a.rel = 'noopener noreferrer';
    parent.append(a);
    return true;
  }

  function statusClass(status) {
    if (status === 'HYPOTHESIS_READY') return 'state focus';
    if (status === 'KILL') return 'state drop';
    if (status === 'WATCH') return 'state watch';
    return 'state';
  }

  function renderHealth(health, generatedAt) {
    healthEl.replaceChildren();
    var items = Array.isArray(health) ? health : [];
    if (!items.length) return;
    var allOk = items.every(function (item) { return item && item.status === 'ok'; });
    if (allOk) {
      healthEl.append(el('div', 'box brief-health-ok', '流水线正常 · 简报生成于 ' + localTime(generatedAt)));
      return;
    }
    var box = el('div', 'box brief-health');
    var okCount = 0;
    items.forEach(function (item) {
      if (!item) return;
      if (item.status === 'ok') {
        okCount += 1;
        return;
      }
      var cls = item.status === 'warn' ? 'brief-health-warn' : 'brief-health-unknown muted';
      box.append(el('p', cls, (item.label || item.id) + '：' + (item.detail || '状态未知')));
    });
    var footer = '简报生成于 ' + localTime(generatedAt) + (okCount ? ' · 其余 ' + okCount + ' 项正常' : '');
    box.append(el('p', 'small', footer));
    healthEl.append(box);
  }

  var DECIDE_URL = 'https://github.com/zhiweiofli/opportunity-runtime-market-sensor/pulls?q=is%3Apr+is%3Aopen+Judge+in%3Atitle';
  var SVG_NS = 'http://www.w3.org/2000/svg';

  function verdictTone(verdict) {
    if (verdict === 'NOW') return 'v-now';
    if (verdict === 'NEXT') return 'v-next';
    if (verdict === 'WATCH') return 'v-watch';
    if (verdict === 'DROP' || verdict === 'KILL') return 'v-drop';
    if (verdict === '暂缓') return 'v-defer';
    return 'v-none';
  }

  function firstLine(item) {
    var pool = [].concat(Array.isArray(item.cells) ? item.cells : [], Array.isArray(item.details) ? item.details : []);
    for (var i = 0; i < pool.length; i += 1) { if (pool[i]) return pool[i]; }
    return '';
  }

  function externalLink(parent, href, label, cls) {
    var a = el('a', cls || '', label);
    a.href = href;
    a.target = '_blank';
    a.rel = 'noopener noreferrer';
    parent.append(a);
  }

  function renderJudge(judge) {
    judgeEl.replaceChildren();
    if (!judge) {
      judgeEl.append(el('p', 'box muted', '暂无已镜像的 Judge 记录。'));
      return;
    }
    var box = el('article', 'box brief-judge brief-focus');
    box.append(el('h3', '', '重点关注'));
    var metaParts = [judge.title || '最新 Judge', '生成时间：' + localTime(judge.generated_at)];
    if (judge.modified_at) metaParts.push('镜像更新：' + localTime(judge.modified_at));
    box.append(el('p', 'small', metaParts.join(' · ')));

    if (!judge.parse_ok) {
      box.append(el('p', 'muted', '原文结构非标准，暂无法自动解析结论与条目，请直接查看原文。'));
      appendSafeLink(box, judge.path, '查看 Judge 原文 ↗');
      judgeEl.append(box);
      return;
    }

    var items = Array.isArray(judge.items) ? judge.items : [];
    var nowItems = items.filter(function (i) { return i.verdict === 'NOW'; });
    var nextItems = items.filter(function (i) { return i.verdict === 'NEXT'; });
    var restItems = items.filter(function (i) { return i.verdict !== 'NOW' && i.verdict !== 'NEXT'; });

    if (nowItems.length) {
      nowItems.forEach(function (item) {
        var card = el('div', 'brief-now');
        var head = el('div', 'itemhead');
        head.append(el('span', 'vtag v-now', 'NOW'), el('span', 'small', '#' + item.rank));
        card.append(head, el('p', 'brief-now-title', item.title || '未命名'));
        if (item.verdict_note && item.verdict_note !== item.verdict) card.append(el('p', 'brief-now-note', item.verdict_note));
        var line = firstLine(item);
        if (line) card.append(el('p', 'small', line));
        box.append(card);
      });
    } else {
      box.append(el('p', 'muted', '本期没有 NOW 条目。'));
    }

    if (nextItems.length) {
      box.append(el('h4', 'brief-minor-title', 'NEXT（' + nextItems.length + '）'));
      var nextList = el('ul', 'brief-next');
      nextItems.forEach(function (item) {
        var li = el('li');
        li.append(el('span', 'vtag v-next', '#' + item.rank), el('span', '', ' ' + (item.title || '未命名')));
        nextList.append(li);
      });
      box.append(nextList);
    }

    if (restItems.length) {
      var countOf = function (v) { return restItems.filter(function (i) { return i.verdict === v; }).length; };
      var label = '另有 WATCH ' + countOf('WATCH') + ' · DROP ' + countOf('DROP');
      var others = restItems.length - countOf('WATCH') - countOf('DROP');
      if (others) label += ' · 其他 ' + others;
      var more = el('details', 'brief-rest');
      more.append(el('summary', '', label));
      var restList = el('ul', 'brief-next');
      restItems.forEach(function (item) {
        var li = el('li');
        li.append(el('span', 'vtag ' + verdictTone(item.verdict), item.verdict || '未标明'), el('span', '', ' #' + item.rank + ' ' + (item.title || '未命名')));
        restList.append(li);
      });
      more.append(restList);
      box.append(more);
    }

    if (judge.conclusion) {
      var concl = el('details', 'brief-rest');
      concl.append(el('summary', '', 'Judge 结论'), el('p', 'brief-conclusion', judge.conclusion));
      box.append(concl);
    }

    if (Array.isArray(judge.decisions) && judge.decisions.length) {
      var decBox = el('div', 'box decision brief-decisions-box');
      decBox.append(el('h4', '', '待你决定'));
      var ul = el('ul', 'brief-decisions');
      judge.decisions.forEach(function (line) { ul.append(el('li', '', line)); });
      decBox.append(ul);
      box.append(decBox);
    }

    var actions = el('div', 'brief-actions');
    externalLink(actions, DECIDE_URL, '去 GitHub 决策 ↗', 'brief-btn');
    appendSafeLink(actions, judge.path, '查看 Judge 原文 ↗');
    box.append(actions);
    judgeEl.append(box);
  }

  function svg(tag, attrs, text) {
    var node = document.createElementNS(SVG_NS, tag);
    Object.keys(attrs || {}).forEach(function (k) { node.setAttribute(k, String(attrs[k])); });
    if (text !== undefined && text !== null) node.textContent = String(text);
    return node;
  }

  function renderWeeklyChart(parent, weeks) {
    if (!weeks.length) {
      parent.append(el('p', 'muted', '暂无周度数据。'));
      return;
    }
    var colW = 44;
    var padL = 28;
    var padT = 18;
    var plotH = 140;
    var width = padL + weeks.length * colW + 8;
    var height = padT + plotH + 44;
    var max = 1;
    var totals = { ready: 0, kill: 0, other: 0, judges: 0 };
    weeks.forEach(function (w) {
      var t = w.research_ready + w.research_kill + w.research_other;
      if (t > max) max = t;
      totals.ready += w.research_ready;
      totals.kill += w.research_kill;
      totals.other += w.research_other;
      totals.judges += w.judge_runs;
    });
    var aria = weeks.length + ' 周 Research 堆叠柱状图：READY ' + totals.ready + '、KILL ' + totals.kill + '、其他 ' + totals.other + '；共 ' + totals.judges + ' 次 Judge 运行。';
    var root = svg('svg', { viewBox: '0 0 ' + width + ' ' + height, role: 'img', 'aria-label': aria, class: 'trend-svg', preserveAspectRatio: 'xMinYMin meet' });
    root.append(svg('title', {}, aria));
    var baseY = padT + plotH;
    root.append(svg('line', { x1: padL, y1: baseY, x2: width - 4, y2: baseY, class: 'axis' }));
    root.append(svg('text', { x: padL - 6, y: padT + 4, class: 'tick', 'text-anchor': 'end' }, max));
    root.append(svg('text', { x: padL - 6, y: baseY, class: 'tick', 'text-anchor': 'end' }, 0));
    weeks.forEach(function (w, idx) {
      var x = padL + idx * colW + 8;
      var bw = colW - 16;
      var y = baseY;
      var g = svg('g', {});
      var total = w.research_ready + w.research_kill + w.research_other;
      var src = w.by_source || {};
      var srcText = Object.keys(src).filter(function (k) { return src[k]; }).map(function (k) { return k + ' ' + src[k]; }).join('，') || '无';
      g.append(svg('title', {}, w.week_start + ' 起一周：Research ' + total + '（READY ' + w.research_ready + ' / KILL ' + w.research_kill + ' / 其他 ' + w.research_other + '）；来源 ' + srcText + '；信号 ' + w.signals_total + '（no-signal ' + w.signals_no_signal + '）；Judge ' + w.judge_runs + ' 次'));
      [['research_ready', 'bar-ready'], ['research_kill', 'bar-kill'], ['research_other', 'bar-other']].forEach(function (pair) {
        var v = w[pair[0]] || 0;
        if (!v) return;
        var h = v / max * plotH;
        y -= h;
        g.append(svg('rect', { x: x, y: y, width: bw, height: h, class: pair[1] }));
      });
      g.append(svg('text', { x: x + bw / 2, y: y - 4, class: 'val', 'text-anchor': 'middle' }, total));
      g.append(svg('text', { x: x + bw / 2, y: baseY + 14, class: 'tick', 'text-anchor': 'middle' }, w.week_start.slice(5)));
      if (w.judge_runs) {
        var cx = x + bw / 2;
        var ty = baseY + 22;
        g.append(svg('path', { d: 'M' + cx + ' ' + ty + 'l-5 9h10z', class: 'judge-mark' }));
      }
      root.append(g);
    });
    parent.append(root);
    var legend = el('p', 'small trend-legend');
    legend.append(el('span', 'dot dot-ready'), el('span', '', 'READY '), el('span', 'dot dot-kill'), el('span', '', 'KILL '), el('span', 'dot dot-other'), el('span', '', '其他 '), el('span', 'judge-tri', '▲'), el('span', '', 'Judge 运行周'));
    parent.append(legend);
  }

  function renderSourceTable(parent, rows) {
    if (!rows.length) return;
    var table = el('table', 'brief-table');
    var head = el('tr');
    ['来源', '总数', 'READY', 'KILL', '可能重复 KILL', 'READY 占比'].forEach(function (h) { head.append(el('th', '', h)); });
    var thead = el('thead');
    thead.append(head);
    var tbody = el('tbody');
    rows.forEach(function (r) {
      var tr = el('tr');
      tr.append(el('td', '', r.source), el('td', '', r.total), el('td', '', r.ready), el('td', '', r.kill), el('td', '', r.possible_repeat));
      var pct = r.total ? Math.round(r.ready / r.total * 100) : 0;
      var cell = el('td');
      var track = el('span', 'ratio');
      var fill = el('span', 'ratio-fill');
      fill.style.width = pct + '%';
      track.append(fill);
      cell.append(track, el('span', 'small', ' ' + pct + '%'));
      tr.append(cell);
      tbody.append(tr);
    });
    table.append(thead, tbody);
    var wrap = el('div', 'table-wrap');
    wrap.append(table);
    parent.append(wrap);
  }

  function renderJudgeTrack(parent, history) {
    if (!history.length) return;
    var list = el('ul', 'judge-track');
    history.slice().reverse().forEach(function (h) {
      var li = el('li');
      li.append(el('span', 'track-date', h.date || '—'));
      var tags = el('span', 'track-tags');
      if (!h.parse_ok) {
        tags.append(el('span', 'muted small', '格式不可解析 '));
        appendSafeLink(tags, h.path, '原文 ↗');
      } else if (!Array.isArray(h.items) || !h.items.length) {
        tags.append(el('span', 'muted small', '无决策看板条目 '));
        appendSafeLink(tags, h.path, '原文 ↗');
      } else {
        h.items.forEach(function (item) {
          var full = item.title || '未命名';
          var short = full.length > 16 ? full.slice(0, 16) + '…' : full;
          var tag = el('span', 'vtag ' + verdictTone(item.verdict), (item.verdict || '?') + ' ' + short);
          tag.title = '#' + item.rank + ' ' + (item.verdict || '未标明') + '：' + full;
          tags.append(tag);
        });
      }
      li.append(tags);
      list.append(li);
    });
    parent.append(list);
  }

  function renderTrends(data) {
    trendsEl.replaceChildren();
    var weeks = data.trends && Array.isArray(data.trends.weeks) ? data.trends.weeks : [];
    var history = Array.isArray(data.judge_history) ? data.judge_history : [];
    var sources = Array.isArray(data.source_yield) ? data.source_yield : [];
    if (!weeks.length && !history.length && !sources.length) return;
    var box = el('section', 'box brief-trends');
    box.append(el('h3', '', '机会趋势'));
    box.append(el('h4', 'brief-minor-title', '每周 Research'));
    renderWeeklyChart(box, weeks);
    if (sources.length) {
      box.append(el('h4', 'brief-minor-title', '来源产出'));
      renderSourceTable(box, sources);
    }
    if (history.length) {
      box.append(el('h4', 'brief-minor-title', 'Judge 判定轨迹'));
      renderJudgeTrack(box, history);
    }
    trendsEl.append(box);
  }

  function renderGaps(gaps) {
    gapsEl.replaceChildren();
    var list = Array.isArray(gaps) ? gaps : [];
    if (!list.length) return;
    var det = el('details', 'box archive brief-more');
    det.append(el('summary', '', 'Judge 未覆盖的 Research（' + list.length + ' 份）'));
    var ul = el('ul', 'gap-list');
    list.forEach(function (g) {
      var li = el('li');
      li.append(el('span', statusClass(g.status), g.status || '未标明'));
      var tags = Array.isArray(g.tags) && g.tags.length ? g.tags.join('、') : '未标明';
      li.append(el('span', 'small', ' ' + tags + ' · ' + (g.modified ? g.modified.slice(0, 10) : '时间未知') + ' '));
      li.append(el('span', '', (g.title || '未命名') + ' '));
      appendSafeLink(li, g.path, '原文 ↗');
      ul.append(li);
    });
    det.append(ul);
    gapsEl.append(det);
  }

  function buildResearchCard(entry) {
    var li = el('li');
    var metaRow = el('div', 'brief-meta-row');
    metaRow.append(el('span', statusClass(entry.status), entry.status || '未标明'));
    if (Array.isArray(entry.possible_repeat_of) && entry.possible_repeat_of.length) {
      metaRow.append(el('span', 'state repeat', '可能重复历史 KILL'));
    }
    var tags = Array.isArray(entry.tags) && entry.tags.length ? entry.tags.join('、') : '未标明';
    var dateStr = entry.modified ? entry.modified.slice(0, 10) : '时间未知';
    metaRow.append(el('span', 'small', tags + ' · ' + dateStr));
    li.append(metaRow);

    li.append(el('h4', '', entry.title || '未命名 Research'));
    li.append(el('p', '', entry.summary || '暂无可提取的摘要，请查看原文。'));

    if (Array.isArray(entry.possible_repeat_of) && entry.possible_repeat_of.length) {
      var repBox = el('div', 'brief-repeats small');
      repBox.append(el('span', '', '可能重复历史 KILL：'));
      entry.possible_repeat_of.forEach(function (hit, idx) {
        if (idx > 0) repBox.append(el('span', '', '；'));
        var why = hit.rule === 'source_signal_id' ? '同源信号' : (Array.isArray(hit.matched) && hit.matched.length ? '共同词：' + hit.matched.join('、') : '');
        var label = (hit.title || '历史条目') + (hit.modified ? ' (' + hit.modified.slice(0, 10) + ')' : '') + (why ? ' · ' + why : '');
        if (!appendSafeLink(repBox, hit.path, label)) {
          repBox.append(el('span', '', label));
        }
      });
      li.append(repBox);
    }

    appendSafeLink(li, entry.path, '查看原文 ↗');
    return li;
  }

  function renderResearch(list, counts, hasJudge) {
    researchEl.replaceChildren();
    var c = counts || { total: 0, ready: 0, kill: 0, unknown: 0 };
    var prefix = hasJudge ? '上次 Judge 之后的新 Research' : '全部已镜像 Research（暂无 Judge 基线）';
    var det = el('details', 'box archive brief-more');
    det.append(el('summary', '', prefix + '：' + c.total + ' 份（READY ' + c.ready + ' / KILL ' + c.kill + '）'));
    var entries = Array.isArray(list) ? list : [];
    if (!entries.length) {
      det.append(el('p', 'muted', '暂无新增 Research。'));
    } else {
      var ul = el('ul', 'archive-list');
      entries.forEach(function (entry) { ul.append(buildResearchCard(entry)); });
      det.append(ul);
    }
    researchEl.append(det);
  }

  function localTime(value) {
    if (!value) return '未知';
    var d = new Date(value);
    if (!isFinite(d.getTime())) return String(value);
    try {
      return d.toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai', hour12: false, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) + '（UTC+8）';
    } catch (_) { return d.toISOString(); }
  }

  function show(data) {
    if (!data || data.schema_version !== 'or-brief@1') {
      throw new Error('不支持的简报格式');
    }
    statusEl.textContent = '';
    statusEl.hidden = true;
    var meta = document.getElementById('meta');
    if (meta) {
      var lastJudge = data.judge && data.judge.modified_at;
      meta.textContent = '简报生成：' + localTime(data.generated_at) + ' | 最近 Judge：' + localTime(lastJudge);
    }
    renderHealth(data.health, data.generated_at);
    renderJudge(data.judge);
    renderTrends(data);
    renderGaps(data.coverage_gaps);
    renderResearch(data.new_research, data.counts, Boolean(data.judge));
  }

  fetch('./data/brief.json', { cache: 'no-store' })
    .then(function (response) {
      if (!response.ok) throw new Error('HTTP ' + response.status);
      return response.json();
    })
    .then(show)
    .catch(function (error) {
      statusEl.hidden = false;
      statusEl.textContent = '本期简报暂不可用（' + error.message + '），其他区块仍可查看。';
    });
})();
