/**
 * Dashboard — Data Overview Screen (Dark Theme)
 * Operational dashboard backed by persisted service and feedback records.
 */
(function () {
  'use strict';
  var A = window.Aurelian, api = A.api, ui = A.ui, comp = A.components;
  var refreshTimer = null;
  var lastUpdateTime = null;
  var chartData = []; // { hour, publicCount, privateCount }

  function init() {
    A.auth.guardRole('admin', function(){
      startClock();
      fetchAllData();
      refreshTimer = setInterval(fetchAllData, A.config.DASHBOARD_REFRESH_MS);
      document.getElementById('btn-refresh').addEventListener('click', fetchAllData);
    });
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
    if (btn) {
      btn.style.transition = 'transform 0.5s ease';
      btn.style.transform = 'rotate(360deg)';
      setTimeout(function(){ btn.style.transform = 'rotate(0deg)'; }, 500);
    }

    Promise.allSettled([
      api.get('/dashboard/overview'),
      api.get('/dashboard/hot-questions'),
      api.get('/dashboard/hot-spots'),
      api.get('/dashboard/satisfaction'),
      api.get('/dashboard/system-metrics'),
      api.get('/kb/docs'),
      api.get('/dashboard/visitor-report')
    ]).then(function (results) {
      updateKPI(results[0].value, results[4].value);
      updateHotQuestions(results[1].value);
      updateRooms(results[0].value, results[2].value);
      updateSentiment(results[3].value, results[6].value);
      updateLog(results[0].value, results[4].value);
      updateSplitChart(results[0].value);
      updateTrendChart(results[0].value);
      updateFeedbackReport(results[6].value);
      updateFooter(results[5].value);
      lastUpdateTime = new Date();
    });
  }

  function updateKPI(overviewR, metricsR) {
    var overview = (overviewR && overviewR.ok) ? overviewR.data : {};
    var metrics = (metricsR && metricsR.ok) ? metricsR.data : {};

    var totalQA = (overview.questionCount || 0) + (overview.voiceQuestionCount || 0);
    var voiceCount = overview.voiceQuestionCount || 0;
    var visionCount = overview.visionRecognizeCount || 0;
    var recommendCount = overview.routeRecommendCount || 0;
    var kbHitRate = metrics.successRate ? (metrics.successRate * 100).toFixed(1) + '%' : '—';
    var pubCount = overview.questionCount || 0;

    renderKPICard('kpi-1', '今日服务次数', overview.todayServiceCount || 0, '次', '本周 ' + (overview.weekServiceCount || 0) + ' 次');
    renderKPICard('kpi-2', '文字/语音提问', pubCount + ' / ' + voiceCount, '', '文字·左 | 语音·右');
    renderKPICard('kpi-3', '图片识景次数', visionCount, '次', '今日累计');
    renderKPICard('kpi-4', '路线推荐次数', recommendCount, '次', '今日累计');

  }

  function renderKPICard(id, label, value, unit, subtitle) {
    var el = document.getElementById(id);
    if (!el) return;
    el.innerHTML =
      '<div class="text-xs text-on-surface-variant uppercase tracking-wider mb-2">' + ui.escapeHtml(label) + '</div>' +
      '<div class="tabular-nums text-[36px] font-medium text-on-background">' + ui.escapeHtml(String(value)) +
      (unit ? '<span class="text-lg text-on-surface-variant ml-1">' + ui.escapeHtml(unit) + '</span>' : '') + '</div>' +
      (subtitle ? '<div class="text-xs mt-2 text-on-surface-variant">' + ui.escapeHtml(subtitle) + '</div>' : '');
  }

  function updateTrendChart(overviewR) {
    var overview = (overviewR && overviewR.ok) ? overviewR.data : {};
    chartData = (overview.trend || []).map(function(item){
      return {hour:item.label, publicCount:item.textCount||0, privateCount:item.voiceCount||0};
    });
    var canvas = document.getElementById('trend-chart');
    if (!canvas) return;
    var ctx = canvas.getContext('2d');
    var w = canvas.parentElement.clientWidth - 48; // card padding
    var h = canvas.parentElement.clientHeight - 48;
    canvas.width = w;
    canvas.height = h;

    if (chartData.length < 2) {
      ctx.fillStyle = '#8E8E90';
      ctx.font = '12px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('暂无最近七天的问答记录', w/2, h/2);
      return;
    }

    // Draw simple line chart
    var padding = { top: 10, right: 10, bottom: 24, left: 10 };
    var plotW = w - padding.left - padding.right;
    var plotH = h - padding.top - padding.bottom;
    var maxVal = 1;
    chartData.forEach(function(d){ maxVal = Math.max(maxVal, d.publicCount, d.privateCount); });
    maxVal = Math.ceil(maxVal * 1.2) || 10;

    // Grid lines
    ctx.strokeStyle = '#E3DFD8';
    ctx.lineWidth = 1;
    for (var i = 0; i <= 4; i++) {
      var y = padding.top + (plotH * i / 4);
      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(w - padding.right, y);
      ctx.stroke();
      ctx.fillStyle = '#746F68';
      ctx.font = '10px Inter, sans-serif';
      ctx.textAlign = 'right';
      ctx.fillText(Math.round(maxVal * (4-i) / 4), padding.left - 4, y + 3);
    }

    // Public line (orange)
    drawLine(ctx, chartData, 'publicCount', '#C75E42', padding, plotW, plotH, maxVal, chartData.length);

    // Private line (gray)
    drawLine(ctx, chartData, 'privateCount', '#A8A19A', padding, plotW, plotH, maxVal, chartData.length);

    // X-axis labels
    ctx.fillStyle = '#746F68';
    ctx.font = '10px Inter, sans-serif';
    ctx.textAlign = 'center';
    chartData.forEach(function(d, i) {
      var x = padding.left + (plotW * i / Math.max(chartData.length - 1, 1));
      ctx.fillText(d.hour, x, h);
    });
  }

  function drawLine(ctx, data, key, color, pad, plotW, plotH, maxVal, len) {
    if (len < 2) return;
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.lineJoin = 'round';
    ctx.beginPath();
    data.forEach(function(d, i) {
      var x = pad.left + (plotW * i / Math.max(len - 1, 1));
      var y = pad.top + plotH - (d[key] / maxVal * plotH);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();

    // Dots
    data.forEach(function(d, i) {
      var x = pad.left + (plotW * i / Math.max(len - 1, 1));
      var y = pad.top + plotH - (d[key] / maxVal * plotH);
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(x, y, 3, 0, Math.PI * 2);
      ctx.fill();
    });
  }

  function updateHotQuestions(result) {
    var list = document.getElementById('hot-questions-list');
    if (!list) return;
    var source = result && result.ok && result.data ? (result.data.items || result.data) : [];
    if (!source || !source.length) {
      list.innerHTML = comp.emptyState('question_answer', '暂无热门问题');
      return;
    }
    var items = source.slice(0, 5);
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
    var spots = spotsR && spotsR.ok && spotsR.data ? (spotsR.data.items || spotsR.data) : [];
    if (spots.length) {
      html += '<div class="mt-3 flex flex-wrap gap-2">';
      spots.slice(0, 3).forEach(function (s) {
        html += '<span class="px-2 py-1 border border-outline-variant rounded-full text-xs text-on-surface-variant">' + ui.escapeHtml(s.spotName || s._id || '景点') + '</span>';
      });
      html += '</div>';
    }
    el.innerHTML = html;
  }

  function updateSplitChart(overviewR) {
    var canvas = document.getElementById('split-chart');
    if (!canvas) return;
    var overview = (overviewR && overviewR.ok) ? overviewR.data : {};
    var pubCount = overview.questionCount || 0;
    var privCount = overview.voiceQuestionCount || 0;
    var ctx = canvas.getContext('2d');
    var w = canvas.width, h = canvas.height;
    var cx = w/2, cy = h/2, r = Math.min(w,h)/2 - 12;

    ctx.clearRect(0, 0, w, h);

    if (pubCount === 0 && privCount === 0) {
      ctx.fillStyle = '#746F68';
      ctx.font = '11px Inter,sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('暂无数据', cx, cy);
      document.getElementById('split-legend').innerHTML = '';
      return;
    }

    var total = pubCount + privCount;
    var pubAngle = (pubCount / total) * Math.PI * 2;
    var privAngle = (privCount / total) * Math.PI * 2;

    // Public slice (orange)
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, r, -Math.PI/2, -Math.PI/2 + pubAngle);
    ctx.closePath();
    ctx.fillStyle = '#C75E42';
    ctx.fill();

    // Private slice (gray)
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, r, -Math.PI/2 + pubAngle, -Math.PI/2 + pubAngle + privAngle);
    ctx.closePath();
    ctx.fillStyle = '#A8A19A';
    ctx.fill();

    // Center hole (donut)
    ctx.beginPath();
    ctx.arc(cx, cy, r * 0.55, 0, Math.PI * 2);
    ctx.fillStyle = '#FFFDFA';
    ctx.fill();

    // Center text
    ctx.fillStyle = '#26231F';
    ctx.font = 'bold 16px Inter,sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(total, cx, cy - 4);
    ctx.font = '9px Inter,sans-serif';
    ctx.fillStyle = '#746F68';
    ctx.fillText('总次数', cx, cy + 10);

    // Legend
    var pct = total > 0 ? Math.round(pubCount/total*100) : 0;
    var legend = document.getElementById('split-legend');
    if (legend) legend.innerHTML =
      '<span style="color:#C75E42">● 文字 ' + pct + '%</span>' +
      '<span style="color:#746F68">● 语音 ' + (100-pct) + '%</span>';
  }

  function updateSentiment(result, reportR) {
    var el = document.getElementById('sentiment-content');
    if (!el) return;
    if (!result || !result.ok || !result.data) { el.innerHTML = comp.emptyState('sentiment_satisfied', '暂无数据'); return; }
    var d = result.data;
    var score = d.averageScore ? (d.averageScore * 20).toFixed(1) : '—';
    var scores=(d.trend||[]).filter(function(item){return item.averageScore!==null;});
    var trend='平稳';
    if(scores.length>1){
      var delta=scores[scores.length-1].averageScore-scores[scores.length-2].averageScore;
      if(delta>0.05)trend='上升';else if(delta<-0.05)trend='下降';
    }
    var trendColor = (trend === 'up' || trend === '上升') ? '#4C9A72' : '#746F68';
    el.innerHTML =
      '<div class="tabular-nums text-[48px] font-medium text-[#C75E42]">' + score + '%</div>' +
      '<div class="text-xs mt-2" style="color:' + trendColor + '">最近趋势：' + ui.escapeHtml(trend) + ' · ' + (d.totalResponses||0) + '份反馈</div>';

    var tags=document.querySelector('#visitor-insights .insight-tags');
    var report=(reportR&&reportR.ok)?reportR.data:{};
    if(tags){
      var emotions=report.emotionDistribution||{};
      tags.innerHTML='<span>积极 '+(emotions.positive||0)+'</span><span>一般 '+(emotions.neutral||0)+'</span><span>待改进 '+(emotions.negative||0)+'</span>';
    }
  }

  function updateFeedbackReport(result){
    var box=document.querySelector('#feedback .feedback-samples');
    if(!box)return;
    if(!result||!result.ok||!result.data){box.innerHTML='<p>游客反馈暂时无法读取。</p>';return;}
    var d=result.data;
    var topics=(d.attentionTopics||[]).slice(0,4).map(function(item){return ui.escapeHtml(item.topic)+' '+item.count+'次';});
    var suggestions=(d.serviceSuggestions||[]).map(function(item){return '<p>• '+ui.escapeHtml(item)+'</p>';}).join('');
    box.innerHTML='<p><strong>游客关注</strong></p><p>'+(topics.join(' · ')||'暂无足够数据')+'</p><p><strong>服务建议</strong></p>'+suggestions;
  }

  function updateLog(overviewR, metricsR) {
    var el = document.getElementById('log-content');
    if (!el) return;
    var metrics = (metricsR && metricsR.ok) ? metricsR.data : {};
    var overview = (overviewR && overviewR.ok) ? overviewR.data : {};
    var html = '';
    html += '<div class="flex justify-between py-1 border-b border-outline-variant"><span>在线房间</span><span class="tabular-nums text-[#4ADE80]">' + (overview.activeRooms || 0) + '</span></div>';
    html += '<div class="flex justify-between py-1"><span>今日服务</span><span class="tabular-nums">' + (overview.todayServiceCount || 0) + '</span></div>';
    html += '<div class="flex justify-between py-1"><span>🎤 语音问答</span><span class="tabular-nums">' + (overview.voiceQuestionCount || 0) + '</span></div>';
    html += '<div class="flex justify-between py-1"><span>📷 图片识景</span><span class="tabular-nums">' + (overview.visionRecognizeCount || 0) + '</span></div>';
    html += '<div class="flex justify-between py-1"><span>🗺 路线推荐</span><span class="tabular-nums">' + (overview.routeRecommendCount || 0) + '</span></div>';
    html += '<div class="flex justify-between py-1"><span>95%响应耗时</span><span class="tabular-nums">' + (metrics.p95LatencyMs ? Math.round(metrics.p95LatencyMs)+'ms' : '—') + '</span></div>';
    el.innerHTML = html;
  }

  function updateFooter(kbResult) {
    var el = document.getElementById('footer-status');
    if (!el) return;
    var docData = (kbResult && kbResult.ok && kbResult.data) ? kbResult.data : [];
    var docCount = Array.isArray(docData) ? docData.length : ((docData.docs || []).length);
    var lastUpdate = lastUpdateTime ? lastUpdateTime.toLocaleTimeString('zh-CN', { hour:'2-digit', minute:'2-digit', second:'2-digit' }) : '—';
    el.textContent = '系统运行中 · 知识库：' + docCount + '份文档 · 最后更新：' + lastUpdate;
  }

  if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', init); }
  else { init(); }
})();
