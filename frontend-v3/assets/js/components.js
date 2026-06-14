/**
 * Aurelian Guide — Component Factories
 * Reusable DOM component generators. Returns HTML strings.
 */
window.Aurelian = window.Aurelian || {};

Aurelian.components = (function () {
  'use strict';

  var esc = Aurelian.ui.escapeHtml;

  /** Skeleton placeholder card */
  function skeletonCard(height) {
    var h = height || 120;
    return '<div class="skeleton rounded-xl" style="height:' + h + 'px;"></div>';
  }

  /** Skeleton list row */
  function skeletonRow() {
    return '<div class="flex items-center gap-3 py-3"><div class="skeleton rounded-full w-10 h-10"></div><div class="flex-1"><div class="skeleton rounded h-4 w-3/4 mb-2"></div><div class="skeleton rounded h-3 w-1/2"></div></div></div>';
  }

  /** Error state card */
  function errorCard(message, retryLabel) {
    return '<div class="flex flex-col items-center justify-center py-8 gap-3 text-center">' +
      '<span class="material-symbols-outlined text-[40px] text-[#F87171]">error_outline</span>' +
      '<p class="text-sm text-[#6F6F6F]">' + esc(message) + '</p>' +
      (retryLabel ? '<button class="retry-btn px-4 py-2 border border-[#E8E8E6] rounded-lg text-sm hover:border-[#E07B3C] transition-colors">' + esc(retryLabel) + '</button>' : '') +
      '</div>';
  }

  /** Empty state */
  function emptyState(icon, message, actionText) {
    return '<div class="flex flex-col items-center justify-center py-8 gap-3 text-center">' +
      '<span class="material-symbols-outlined text-[40px] text-[#A0A0A0]">' + (icon || 'inbox') + '</span>' +
      '<p class="text-sm text-[#6F6F6F]">' + esc(message) + '</p>' +
      (actionText ? '<span class="text-xs text-[#A0A0A0]">' + esc(actionText) + '</span>' : '') +
      '</div>';
  }

  /** KPI card for dashboard */
  function kpiCard(label, value, unit, trend, isUp, isPositive) {
    var arrow = isUp ? '↑' : '↓';
    var color = isPositive ? '#4ADE80' : '#F87171';
    return '<div class="card">' +
      '<div class="label-xs" style="color:#8E8E90;text-transform:uppercase;margin-bottom:8px;">' + esc(label) + '</div>' +
      '<div class="tabular-nums text-[36px] font-medium" style="color:#ECECED;">' + esc(String(value)) + (unit ? '<span class="text-lg" style="color:#8E8E90;">' + esc(unit) + '</span>' : '') + '</div>' +
      '<div class="text-xs mt-2" style="color:' + color + ';">' + arrow + ' ' + esc(String(trend)) + '</div>' +
      '</div>';
  }

  /** Status badge pill */
  function statusBadge(status) {
    var colors = {
      'published': { bg: '#ECFDF5', text: '#059669', label: '已发布' },
      'review':    { bg: '#FFFBEB', text: '#D97706', label: '审核中' },
      'draft':     { bg: '#F3F4F6', text: '#6B7280', label: '草稿' },
      'active':    { bg: '#ECFDF5', text: '#059669', label: '在线' },
      'idle':      { bg: '#F3F4F6', text: '#6B7280', label: '离线' }
    };
    var c = colors[status] || colors['draft'];
    return '<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium" style="background:' + c.bg + ';color:' + c.text + ';">' + c.label + '</span>';
  }

  /** Member list item */
  function memberItem(member, isSelf) {
    var initial = (member.userName || '?').charAt(0).toUpperCase();
    return '<div class="flex items-center gap-3 py-2">' +
      '<div class="w-9 h-9 rounded-full bg-[#E07B3C]/10 text-[#E07B3C] flex items-center justify-center text-sm font-medium">' + esc(initial) + '</div>' +
      '<div class="flex-1 min-w-0">' +
        '<div class="text-sm font-medium truncate">' + esc(member.userName || '游客') + (isSelf ? ' <span class="text-xs text-[#A0A0A0]">(你)</span>' : '') + '</div>' +
      '</div>' +
      '<span class="w-2 h-2 rounded-full bg-[#4ADE80]"></span>' +
      '</div>';
  }

  /** Chat message bubble */
  function chatBubble(role, text, timestamp) {
    var isUser = role === 'user';
    var timeStr = '';
    if (timestamp) {
      try { timeStr = new Date(timestamp).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }); } catch (e) {}
    }
    if (isUser) {
      return '<div class="flex justify-end mb-4"><div class="max-w-[75%]"><div class="bg-white border border-[#E8E8E4] rounded-xl rounded-br-sm px-4 py-3 text-sm text-[#1A1A1C]">' + esc(text) + '</div>' + (timeStr ? '<div class="text-right text-[10px] text-[#A0A0A0] mt-1">' + timeStr + '</div>' : '') + '</div></div>';
    } else {
      return '<div class="flex mb-4"><div class="max-w-[80%]"><div class="bg-[#F5F5F2] rounded-xl rounded-bl-sm px-4 py-3 text-sm text-[#1A1A1C] border-l-2 border-[#E07B3C]">' + esc(text) + '</div>' + (timeStr ? '<div class="text-[10px] text-[#A0A0A0] mt-1">' + timeStr + '</div>' : '') + '</div></div>';
    }
  }

  /** System message banner */
  function systemBanner(text) {
    return '<div class="flex justify-center my-4"><span class="text-xs text-[#A0A0A0] bg-[#F5F5F2] px-3 py-1 rounded-full">' + esc(text) + '</span></div>';
  }

  /** Help prompt card (for AI assistant) */
  function helpPromptCard(question, onNotify, onDismiss) {
    return '<div class="bg-[#FDF6F1] border border-[#E07B3C]/20 rounded-xl p-4 mx-4 mb-4"><p class="text-sm text-[#1A1A1C] mb-3">检测到你可能需要帮助，是否通知团长？</p><div class="flex gap-2"><button class="help-dismiss px-4 py-2 border border-[#E8E8E4] rounded-lg text-sm">暂不通知</button><button class="help-notify px-4 py-2 bg-[#E07B3C] text-white rounded-lg text-sm">通知团长</button></div></div>';
  }

  /** Typing indicator bubble */
  function typingIndicator() {
    return '<div class="flex mb-4" id="typing-indicator"><div class="bg-[#F5F5F2] rounded-xl rounded-bl-sm px-4 py-3 border-l-2 border-[#E07B3C]"><span class="text-sm text-[#A0A0A0]">AI 正在思考</span><span class="typing-dots">...</span></div></div>';
  }

  return {
    skeletonCard: skeletonCard,
    skeletonRow: skeletonRow,
    errorCard: errorCard,
    emptyState: emptyState,
    kpiCard: kpiCard,
    statusBadge: statusBadge,
    memberItem: memberItem,
    chatBubble: chatBubble,
    systemBanner: systemBanner,
    helpPromptCard: helpPromptCard,
    typingIndicator: typingIndicator
  };
})();
