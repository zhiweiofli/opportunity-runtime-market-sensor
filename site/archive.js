(function () {
  'use strict';
  var panel = document.getElementById('archive');
  var type = document.getElementById('archive-type');
  var search = document.getElementById('archive-search');
  var status = document.getElementById('archive-status');
  var list = document.getElementById('archive-list');
  var entries = null;
  var loading = false;
  var root = 'https://github.com/zhiweiofli/opportunity-runtime-market-sensor/blob/main/';

  function render() {
    var query = search.value.trim().toLowerCase();
    var filtered = entries.filter(function (entry) {
      return (type.value === 'all' || entry.kind === type.value) && (entry.title + ' ' + entry.summary + ' ' + (entry.status || '')).toLowerCase().includes(query);
    });
    status.textContent = '显示 ' + filtered.length + ' / ' + entries.length + ' 份资料，按最近更新排序。';
    list.replaceChildren();
    filtered.forEach(function (entry) {
      var item = document.createElement('li');
      var meta = document.createElement('span');
      meta.className = 'small';
      meta.textContent = (entry.kind === 'research' ? 'Research' : 'Judge') + ' · ' + (entry.modified ? entry.modified.slice(0, 10) : '时间未知') + (entry.status ? ' · 原文状态：' + entry.status : '');
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
        entries = manifest.entries.filter(function (entry) {
          return entry && typeof entry.path === 'string' && /^or-archive\/(research|judge)\/[^/]+\.md$/.test(entry.path) && typeof entry.title === 'string' && typeof entry.summary === 'string' && ['research', 'judge'].includes(entry.kind);
        }).sort(function (a, b) { return (b.modified || '').localeCompare(a.modified || ''); });
        render();
      }).catch(function () {
        status.textContent = '资料清单暂不可用，请使用下方 GitHub 目录入口；关闭后重新打开可重试。';
      }).finally(function () { loading = false; });
  });
  type.addEventListener('change', function () { if (entries) render(); });
  search.addEventListener('input', function () { if (entries) render(); });
})();
