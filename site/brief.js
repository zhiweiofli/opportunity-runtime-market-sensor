(function () {
  'use strict';
  var REPO_ROOT = 'https://github.com/zhiweiofli/opportunity-runtime-market-sensor/blob/main/';
  var SAFE_PATH = /^drive-mirror\/files\/(?:[A-Za-z0-9._-]+\/)*[A-Za-z0-9._-]+$/;
  var statusEl = document.getElementById('brief-status');
  var healthEl = document.getElementById('brief-health');
  var judgeEl = document.getElementById('brief-judge');
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

  function verdictClass(verdict) {
    if (verdict === 'NOW' || verdict === 'NEXT') return 'state focus';
    if (verdict === '暂缓') return 'state defer';
    if (verdict === 'WATCH') return 'state watch';
    if (verdict === 'DROP' || verdict === 'KILL') return 'state drop';
    return 'state';
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
      healthEl.append(el('div', 'box brief-health-ok', '流水线正常 · 简报生成于 ' + (generatedAt || '未知')));
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
    var footer = '简报生成于 ' + (generatedAt || '未知') + (okCount ? ' · 其余 ' + okCount + ' 项正常' : '');
    box.append(el('p', 'small', footer));
    healthEl.append(box);
  }

  function renderJudge(judge) {
    judgeEl.replaceChildren();
    if (!judge) {
      judgeEl.append(el('p', 'box muted', '暂无已镜像的 Judge 记录。'));
      return;
    }
    var box = el('article', 'box brief-judge');
    box.append(el('h3', '', judge.title || '最新 Judge'));
    var metaParts = ['生成时间：' + (judge.generated_at || '未知')];
    if (judge.modified_at) metaParts.push('镜像更新：' + judge.modified_at);
    box.append(el('p', 'small', metaParts.join(' · ')));

    if (!judge.parse_ok) {
      box.append(el('p', 'muted', '原文结构非标准，暂无法自动解析结论与条目，请直接查看原文。'));
      appendSafeLink(box, judge.path, '查看原文 ↗');
      judgeEl.append(box);
      return;
    }

    if (judge.conclusion) {
      box.append(el('p', 'brief-conclusion', judge.conclusion));
    }

    if (Array.isArray(judge.items) && judge.items.length) {
      var grid = el('div', 'brief-items');
      judge.items.forEach(function (item) {
        var isFocus = item.verdict === 'NOW' || item.verdict === 'NEXT';
        var isMuted = item.verdict === 'DROP' || item.verdict === 'WATCH' || item.verdict === '暂缓' || item.verdict === 'KILL';
        var card = el('article', 'brief-item' + (isFocus ? ' brief-item-focus' : isMuted ? ' brief-item-muted' : ''));
        var head = el('div', 'itemhead');
        head.append(
          el('strong', '', '#' + item.rank + ' · ' + (item.title || '未命名')),
          el('span', verdictClass(item.verdict), item.verdict_note || item.verdict || '未标明')
        );
        card.append(head);

        var lines = [];
        if (Array.isArray(item.cells)) {
          item.cells.forEach(function (c) { if (c) lines.push(c); });
        }
        if (Array.isArray(item.details)) {
          item.details.forEach(function (d) { if (d) lines.push(d); });
        }
        if (lines.length) {
          var det = el('details', 'brief-item-details');
          det.append(el('summary', '', '查看详情'));
          var ul = el('ul');
          lines.forEach(function (line) { ul.append(el('li', '', line)); });
          det.append(ul);
          card.append(det);
        }
        grid.append(card);
      });
      box.append(grid);
    }

    if (Array.isArray(judge.decisions) && judge.decisions.length) {
      var decBox = el('div', 'box decision brief-decisions-box');
      decBox.append(el('h4', '', '待你决定'));
      var ul = el('ul', 'brief-decisions');
      judge.decisions.forEach(function (line) { ul.append(el('li', '', line)); });
      decBox.append(ul);
      box.append(decBox);
    }

    appendSafeLink(box, judge.path, '查看原文 ↗');
    judgeEl.append(box);
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
    researchEl.append(el('h3', 'brief-subtitle', prefix + '（' + c.total + ' 份，READY ' + c.ready + ' / KILL ' + c.kill + '）'));

    var entries = Array.isArray(list) ? list : [];
    if (!entries.length) {
      researchEl.append(el('p', 'box muted', '暂无新增 Research。'));
      return;
    }

    var primary = entries.slice(0, 8);
    var rest = entries.slice(8);

    var ul = el('ul', 'archive-list');
    primary.forEach(function (entry) { ul.append(buildResearchCard(entry)); });
    researchEl.append(ul);

    if (rest.length) {
      var more = el('details', 'brief-more box archive');
      more.append(el('summary', '', '展开其余 ' + rest.length + ' 份 Research'));
      var moreList = el('ul', 'archive-list');
      rest.forEach(function (entry) { moreList.append(buildResearchCard(entry)); });
      more.append(moreList);
      researchEl.append(more);
    }
  }

  function show(data) {
    if (!data || data.schema_version !== 'or-brief@1') {
      throw new Error('不支持的简报格式');
    }
    statusEl.textContent = '';
    statusEl.hidden = true;
    renderHealth(data.health, data.generated_at);
    renderJudge(data.judge);
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
