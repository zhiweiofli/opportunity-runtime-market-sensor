(function () {
  'use strict';
  // 页面显示用的中文语义标签。数据文件与原文仍保留英文代码，悬停可见原代码。
  var maps = {
    status: {
      HYPOTHESIS_READY: '假设就绪',
      KILL: '已否决',
      BLOCKED: '待实证',
      WATCH: '观察中'
    },
    verdict: {
      NOW: '本周推进',
      NEXT: '排队候选',
      WATCH: '观察',
      DROP: '放弃',
      KILL: '已否决',
      '暂缓': '暂缓'
    },
    source: {
      Business: '利润池变化',
      Friction: '付费摩擦',
      IBF: '存量困局',
      UW: '人工不划算'
    },
    kind: {
      signals: '信号',
      research: '研究',
      receipt: '研究批次回执',
      judge: '评审',
      archive: '归档',
      other: '其他'
    }
  };
  function label(type, code) {
    if (code === null || code === undefined || code === '') return '未标明';
    var m = maps[type] || {};
    return Object.prototype.hasOwnProperty.call(m, code) ? m[code] : String(code);
  }
  window.OR_LABELS = { maps: maps, label: label };
})();
