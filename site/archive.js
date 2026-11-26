(function () {
  'use strict';
  var panel = document.getElementById('archive');
  var type = document.getElementById('archive-type');
  var verdict = document.getElementById('archive-verdict');
  var tag = document.getElementById('archive-tag');
  var search = document.getElementById('archive-search');
  var showNoSignal = document.getElementById('archive-show-nosignal');
  var status = document.getElementById('archive-status');
  var list = document.getElementById('archive-list');
  var entries = null;
  var loading = false;
  var lastChanged = null;
  var root = 'https://github.com/zhiweiofli/opportunity-runtime-market-sensor/blob/main/';
  var L = window.OR_LABELS || { label: function (t, c) { return c || '未标明'; }, maps: { kind: {} } };
  var kinds = {research:'研究', judge:'评审', signals:'信号', receipt:'研究批次回执', archive:'归档', other:'其他'};
  function srcText(tags) { return tags.map(function (t) { return L.label('source', t); }).join('、'); }
  var noSignalRe = /\bno[- ]signal\b/i;

  function render() {
    var query = search.value.trim().toLowerCase();
    var includeNoSignal = Boolean(showNoSignal && showNoSignal.checked);
    var filtered = entries.filter(function (entry) {
      var tags = entry.tags || [];
      return (includeNoSignal || !noSignalRe.test(entry.title)) &&
        (type.value === 'all' || entry.kind === type.value) &&
        (verdict.value === 'all' || (entry.status || 'unknown') === verdict.value) &&
        (tag.value === 'all' || (tag.value === 'unknown' ? !tags.length : tags.includes(tag.value))) &&
        (entry.title + ' ' + entry.summary + ' ' + (entry.status || '') + ' ' + tags.join(' ')).toLowerCase().includes(query);
    });
    status.textContent = '显示 ' + filtered.length + ' / ' + entries.length + ' 份资料，按最近更新排序' + (includeNoSignal ? '。' : '（已隐藏无信号记录）。') + (lastChanged ? ' 镜像最近变更：' + lastChanged : '');
    list.replaceChildren();
    filtered.forEach(function (entry) {
      var item = document.createElement('li');
      var meta = document.createElement('span');
      meta.className = 'small';
      meta.textContent = kinds[entry.kind] + ' · ' + (entry.modified ? entry.modified.slice(0, 10) : '时间未知') + (entry.status ? ' · 研究结论：' + L.label('status', entry.status) : '') + (entry.tags && entry.tags.length ? ' · 来源：' + srcText(entry.tags) : '') + (entry.source_status === 'not_seen' ? ' · 源端暂不可见' : '');
      var heading = document.createElement('h3');
      heading.textContent = entry.title;
      var summary = document.createElement('p');
      summary.textContent = entry.summary || '暂无可提取的摘要，请查看原文。';
      var link = document.createElement('a');
      link.href = root + entry.path.split('/').map(encodeURIComponent).join('/');
      link.target = '_blank'; link.rel = 'noopener noreferrer';
      link.textContent = '查看原文 ↗';
      item.append(meta, heading, summary, link); list.append(item);
    });
  }

  panel.addEventListener('toggle', function () {
    if (!panel.open || entries || loading) return;
    loading = true; status.textContent = '正在读取 GitHub 资料清单…';
    fetch('./data/archive.json', {cache:'no-store'})
      .then(function (response) { if (!response.ok) throw new Error('HTTP ' + response.status); return response.json(); })
      .then(function (manifest) {
        if (!Array.isArray(manifest.entries)) throw new Error('清单格式无效');
        lastChanged = manifest.mirror_last_changed_at || null;
        entries = manifest.entries.filter(function (entry) {
          if (!entry || typeof entry.path !== 'string' || entry.path.split('/').includes('..')) return false;
          var safePath = /^or-archive\/(research|judge)\/[^/]+\.md$/.test(entry.path) || /^drive-mirror\/files\/(?:[A-Za-z0-9._-]+\/)*[A-Za-z0-9._-]+$/.test(entry.path);
          return safePath && typeof entry.title === 'string' && typeof entry.summary === 'string' && Object.prototype.hasOwnProperty.call(kinds, entry.kind);
        }).sort(function (a, b) { return (b.modified || '').localeCompare(a.modified || ''); });
        Array.from(new Set(entries.map(function (entry) { return entry.status; }).filter(Boolean))).sort().forEach(function (value) { var o = document.createElement('option'); o.value = value; o.textContent = L.label('status', value) + '（' + value + '）'; verdict.append(o); });
        Array.from(new Set(entries.flatMap(function (entry) { return entry.tags || []; }))).sort().forEach(function (value) { var o = document.createElement('option'); o.value = value; o.textContent = L.label('source', value) + '（' + value + '）'; tag.append(o); });
        render();
      }).catch(function () {
        status.textContent = '资料清单暂不可用，请使用下方 GitHub 目录入口；关闭后重新打开可重试。';
      }).finally(function () { loading = false; });
  });
  type.addEventListener('change', function () { if (entries) render(); });
  verdict.addEventListener('change', function () { if (entries) render(); });
  tag.addEventListener('change', function () { if (entries) render(); });
  if (showNoSignal) showNoSignal.addEventListener('change', function () { if (entries) render(); });
  search.addEventListener('input', function () { if (entries) render(); });
})();
