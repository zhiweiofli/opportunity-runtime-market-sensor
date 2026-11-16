(function () {
  'use strict';
  var data = null;
  var filter = document.getElementById('workflow-filter');
  var cards = document.getElementById('workflow-cards');
  var message = document.getElementById('workflow-message');
  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text !== undefined && text !== null) node.textContent = String(text);
    return node;
  }
  function date(value) { return value || '未知'; }
  function duration(seconds) {
    if (seconds === null || seconds === undefined || seconds < 0) return '未知';
    var h = Math.floor(seconds / 3600);
    return h >= 24 ? Math.floor(h / 24) + ' 天 ' + h % 24 + ' 小时' : h + ' 小时';
  }
  function amount(value) {
    if (!value || value.value === null || value.basis === 'unknown') return '未知';
    return value.value + ' ' + value.currency + ' / ' + value.unit + '（' + ({measured:'实测',estimated:'估算'}[value.basis] || '未知') + '）';
  }
  function line(parent, label, value) { parent.append(el('p', '', label + '：' + (value || '未公开'))); }
  function link(parent, url, label) {
    if (!url) return;
    try {
      var u = new URL(url);
      if (u.protocol !== 'https:' || u.hostname !== 'github.com' || u.search || u.hash || !/\/[^/]+\/[^/]+\/(pull|issues)\/\d+$/.test(u.pathname)) return;
      var a = el('a', '', label);
      a.href = u.href; a.rel = 'noopener noreferrer'; a.target = '_blank'; parent.append(a);
    } catch (_) { /* Invalid links are omitted. */ }
  }
  function history(parent, events) {
    if (!events || !events.length) return;
    var list = el('ul');
    events.forEach(function (event) {
      var item = el('li', '', date(event.at) + ' · ' + event.action + ' · ' + event.actor + ' ');
      link(item, event.url, '来源'); list.append(item);
    });
    parent.append(list);
  }
  function task(parent, item, index) {
    var box = el('div', 'workflow-card');
    box.append(el('h4', '', '实践任务 ' + (index + 1) + ' · ' + item.stage));
    var pub = item.public || {};
    line(box, '问题', pub.question_summary); line(box, '判定标准', pub.criteria_summary);
    line(box, '预算', pub.budget ? amount(pub.budget) : null);
    line(box, '领取者', item.claimant); line(box, '开始', date(item.started_at));
    line(box, '最近心跳', date(item.heartbeat_at)); line(box, '当前阶段等待', duration(item.waiting_seconds));
    if (item.latest_result) {
      line(box, '最新结果', item.latest_result.summary);
      line(box, '实际消耗', item.latest_result.actual_cost ? amount(item.latest_result.actual_cost) : null);
    }
    link(box, item.url, '查看任务或结果');
    var details = el('details'); details.append(el('summary', '', '任务状态历史')); history(details, item.history); box.append(details); parent.append(box);
  }
  function render() {
    cards.replaceChildren();
    var shown = data.opportunities.filter(function (item) { return filter.value === 'all' || item.stage === filter.value; });
    if (!shown.length) { cards.append(el('p', 'muted', '当前没有可展示的脱敏机会。')); return; }
    shown.forEach(function (item) {
      var pub = item.public || {}, box = el('article', 'workflow-card'), head = el('div', 'workflow-head');
      head.append(el('h3', '', pub.title || '未公开标题'), el('span', 'state', item.stage)); box.append(head);
      box.append(el('p', 'muted', pub.summary || '未公开摘要'));
      var grid = el('div', 'workflow-grid'), left = el('div'), right = el('div');
      line(left, '目标客户', pub.customer_summary); line(left, '经济锚点', pub.economic_anchor ? amount(pub.economic_anchor) : null);
      line(left, 'Judge 建议', item.judge_recommendation); line(left, '研究成熟度', item.research_status);
      line(right, '关键未知', pub.unknown_summary); line(right, '下一步', pub.next_step_summary);
      line(right, '进入阶段', date(item.entered_at)); line(right, '当前阶段等待', duration(item.waiting_seconds)); grid.append(left, right); box.append(grid);
      var gates = pub.gate_summary;
      if (gates) line(box, '四 Gate 摘要', 'Money：' + gates.money + '；Mechanism：' + gates.mechanism + '；Persistence：' + gates.persistence + '；Capture：' + gates.capture);
      else line(box, '四 Gate 摘要', null);
      link(box, item.url, '查看审阅或决定');
      var details = el('details'); details.append(el('summary', '', '实践任务与状态历史'));
      if (!item.tasks.length) details.append(el('p', 'muted', '暂无实践任务。'));
      item.tasks.forEach(function (t, i) { task(details, t, i); });
      history(details, item.history); box.append(details); cards.append(box);
    });
  }
  function ratio(label, value) {
    return label + '：' + (value.denominator ? (Math.round(value.numerator / value.denominator * 1000) / 10 + '%（' + value.numerator + '/' + value.denominator + '）') : '无样本（0/0）');
  }
  function show(snapshot) {
    if (snapshot.schema_version !== 'or-workflow-dashboard@1') throw new Error('不支持的快照版本');
    data = snapshot; var counts = snapshot.counts;
    var stats = document.getElementById('workflow-stats'); stats.replaceChildren();
    [['待审评审 PR', counts.open_review_prs], ['待验收结果 PR', counts.open_result_prs], ['结果待决定机会', counts.opportunities_awaiting_decision], ['未通过或待验证（含测试）', counts.unverified_prs]].forEach(function (x) {
      var item = el('div', 'stat'); item.append(el('b', '', x[1]), el('span', '', x[0])); stats.append(item);
    });
    document.getElementById('workflow-metrics').textContent = ratio('任务完成率', snapshot.completion) + ' · ' + ratio('立项转化', snapshot.conversion) + ' · 创建窗口：' + date(snapshot.window_start) + ' 至 ' + date(snapshot.observation_cutoff);
    var age = Date.now() - Date.parse(snapshot.generated_at);
    message.textContent = isFinite(age) && age >= 0 && age <= 48 * 3600000 ? '闭环快照已加载。' : '闭环快照可能过期或时间未知，请核对来源。';
    message.className = isFinite(age) && age >= 0 && age <= 48 * 3600000 ? 'muted' : 'workflow-fresh';
    document.getElementById('workflow-freshness').textContent = '快照生成：' + date(snapshot.generated_at) + ' · 最近 Judge（已镜像）：' + date(snapshot.last_judge_at) + ' · 最近领取/心跳：' + date(snapshot.last_heartbeat_at) + ' · GitHub 同步：' + date(snapshot.github_synced_at) + ' · 上次成功部署：' + date(snapshot.last_pages_deploy_at);
    Array.from(new Set(snapshot.opportunities.map(function (x) { return x.stage; }))).sort().forEach(function (stage) { var option = el('option', '', stage); option.value = stage; filter.append(option); });
    render();
  }
  filter.addEventListener('change', function () { if (data) render(); });
  fetch('./data/workflow.json', {cache:'no-store'}).then(function (response) { if (!response.ok) throw new Error('HTTP ' + response.status); return response.json(); }).then(show).catch(function (error) {
    message.textContent = '闭环快照尚未发布或暂不可用（' + error.message + '）；历史快照仍可查看。';
  });
})();
