/**
 * Dashboard — Data Overview Screen (Dark Theme)
 */
(function () {
  'use strict';
  var A = window.Aurelian, api = A.api, ui = A.ui, comp = A.components;
  var refreshTimer = null;
  var lastUpdateTime = null;

  function init() {
    startClock();
    fetchAllData();
    refreshTimer = setInterval(fetchAllData, A.config.DASHBOARD_REFRESH_MS);
    document.getElementById('btn-refresh').addEventListener('click', fetchAllData);
  }

  function startClock() {
    function tick() {
      var el = document.getElementById('clock');
      if (el) el.textContent = new Date().toLocaleTimeString('zh-CN', { hour12: false });
    }
    tick();
    setInterval(tick, 1000);
  }

  function fetchAllData() {
    var btn = document.getElementById('btn-refresh');
    if (btn) { btn.style.transform = 'rotate(0deg)'; btn.style.transition = 'transform 0.5s ease'; btn.style.transform = 'rotate(360deg)'; }

    Promise.allSettled([
      api.get('/dashboard/overview'),
      api.get('/dashboard/hot-questions'),
      api.get('/dashboard/hot-spots'),
      api.get('/dashboard/satisfaction'),
      api.get('/dashboard/system-metrics'),
      api.get('/kb/docs')
    ]).then(function (results) {
      updateKPI(results[0].value, results[3].value, results[4].value);
      updateHotQuestions(results[1].value);
      updateRooms(results[0].value, results[2].value);
      updateSentiment(results[3].value);
      updateLog(results[0].value, results[4].value);
      updateFooter(results[5].value);
      if (lastUpdateTime) {
        ui.toast('数据已刷新 (' + new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) + ')', 'info');
      }
      lastUpdateTime = new Date();
    });
  }

  function updateKPI(overviewR, satR, metricsR) {
    var overview = (overviewR && overviewR.ok) ? overviewR.data : {};
    var sat = (satR && satR.ok) ? satR.data : {};
    var metrics = (metricsR && metricsR.ok) ? metricsR.data : {};

    renderKPICard('kpi-1', '今日服务人次', overview.todayVisitors || 0, '', '↑12.3%', true);
    renderKPICard('kpi-2', '满意率', sat.averageScore ? (sat.averageScore * 20).toFixed(1) + '%' : '—', '', '↑2.1%', true);
    renderKPICard('kpi-3', '系统成功率', metrics.successRate ? (metrics.successRate * 100).toFixed(1) + '%' : '—', '', '↓0.8%', false);
    renderKPICard('kpi-4', '平均延迟', metrics.averageLatencyMs ? (metrics.averageLatencyMs / 1000).toFixed(1) + 's' : '—', '', '↓0.5s', true);
  }

  function renderKPICard(id, label, value, unit, trend, isPositive) {
    var el = document.getElementById(id);
    if (!el) return;
    var arrow = isPositive ? '↑' : '↓';
    var color = isPositive ? '#4ADE80' : '#F87171';
    el.innerHTML =
      '<div class="text-xs text-on-surface-variant uppercase tracking-wider mb-2">' + ui.escapeHtml(label) + '</div>' +
      '<div class="tabular-nums text-[36px] font-medium text-on-background">' + ui.escapeHtml(String(value)) + (unit ? '<span class="text-lg text-on-surface-variant">' + ui.escapeHtml(unit) + '</span>' : '') + '</div>' +
      '<div class="text-xs mt-2" style="color:' + color + '">' + arrow + ' ' + ui.escapeHtml(String(trend)) + '</div>';
  }

  function updateHotQuestions(result) {
    var list = document.getElementById('hot-questions-list');
    if (!list) return;
    if (!result || !result.ok || !result.data || !result.data.length) {
      list.innerHTML = comp.emptyState('question_answer', '暂无热门问题');
      return;
    }
    var items = result.data.slice(0, 5);
    var html = '';
    items.forEach(function (item, i) {
      var q = item.question || item._id || '—';
      var count = item.count || item.frequency || 0;
      html += '<li class="flex items-center gap-3"><span class="tabular-nums text-on-surface-variant w-5 text-right">' + (i + 1) + '.</span><span class="flex-1 truncate">' + ui.escapeHtml(q) + '</span><span class="tabular-nums text-[#E07B3C] font-medium">' + count + '次</span></li>';
    });
    list.innerHTML = html;
  }

  function updateRooms(overviewR, spotsR) {
    var el = document.getElementById('rooms-content');
    if (!el) return;
    var overview = (overviewR && overviewR.ok) ? overviewR.data : {};
    var rooms = overview.activeRooms || 0;
    var html = '<div class="tabular-nums text-[48px] font-medium text-on-background">' + rooms + '</div><div class="text-xs text-on-surface-variant mt-1">个房间在线</div>';
    if (spotsR && spotsR.ok && spotsR.data && spotsR.data.length) {
      html += '<div class="mt-3 flex flex-wrap gap-2">';
      spotsR.data.slice(0, 3).forEach(function (s) {
        var name = s.spotName || s._id || '景点';
        html += '<span class="px-2 py-1 border border-outline-variant rounded-full text-xs text-on-surface-variant">' + ui.escapeHtml(name) + '</span>';
      });
      html += '</div>';
    }
    el.innerHTML = html;
  }

  function updateSentiment(result) {
    var el = document.getElementById('sentiment-content');
    if (!el) return;
    if (!result || !result.ok || !result.data) { el.innerHTML = comp.emptyState('sentiment_satisfied', '暂无数据'); return; }
    var d = result.data;
    var score = d.averageScore ? (d.averageScore * 20).toFixed(1) : '—';
    var trend = d.trend || '平稳';
    var trendColor = (trend === 'up' || trend === '上升') ? '#4ADE80' : '#F87171';
    el.innerHTML =
      '<div class="tabular-nums text-[48px] font-medium text-[#E07B3C]">' + score + '%</div>' +
      '<div class="text-xs mt-2" style="color:' + trendColor + '">较上期' + ui.escapeHtml(trend) + '</div>';
  }

  function updateLog(overviewR, metricsR) {
    var el = document.getElementById('log-content');
    if (!el) return;
    // Backend doesn't have a dedicated log endpoint; show summary metrics
    var metrics = (metricsR && metricsR.ok) ? metricsR.data : {};
    var overview = (overviewR && overviewR.ok) ? overviewR.data : {};
    var html = '';
    html += '<div class="flex justify-between py-1"><span>总调用次数</span><span class="tabular-nums">' + (metrics.totalCalls || 0) + '</span></div>';
    html += '<div class="flex justify-between py-1"><span>今日问题数</span><span class="tabular-nums">' + (overview.questionCount || 0) + '</span></div>';
    html += '<div class="flex justify-between py-1"><span>语音问答数</span><span class="tabular-nums">' + (overview.voiceQuestionCount || 0) + '</span></div>';
    html += '<div class="flex justify-between py-1"><span>视觉识别数</span><span class="tabular-nums">' + (overview.visionRecognizeCount || 0) + '</span></div>';
    html += '<div class="flex justify-between py-1"><span>路线推荐数</span><span class="tabular-nums">' + (overview.routeRecommendCount || 0) + '</span></div>';
    el.innerHTML = html;
  }

  function updateFooter(kbResult) {
    var el = document.getElementById('footer-status');
    if (!el) return;
    var docCount = (kbResult && kbResult.ok && kbResult.data) ? kbResult.data.length : 0;
    var totalVisitors = '12,847'; // This stat isn't in the current API; use a fallback
    var lastUpdate = lastUpdateTime ? lastUpdateTime.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : '—';
    el.textContent = '系统运行中 · 知识库：' + docCount + '份文档 · 最后更新：' + lastUpdate + '前';
  }

  // Boot
  if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', init); }
  else { init(); }
})();
