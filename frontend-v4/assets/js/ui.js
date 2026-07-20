/**
 * Aurelian Guide — UI Helpers
 * Toast notifications, loading/skeleton, error, empty states.
 */
window.Aurelian = window.Aurelian || {};

Aurelian.ui = (function () {
  'use strict';

  var TOAST_CONTAINER_ID = 'aurelian-toast-container';

  /** Ensure toast container exists */
  function toastContainer() {
    var el = document.getElementById(TOAST_CONTAINER_ID);
    if (!el) {
      el = document.createElement('div');
      el.id = TOAST_CONTAINER_ID;
      el.style.cssText = 'position:fixed;bottom:24px;left:50%;transform:translateX(-50%);z-index:9999;display:flex;flex-direction:column-reverse;gap:8px;pointer-events:none;';
      document.body.appendChild(el);
    }
    return el;
  }

  /** Show a toast notification */
  function toast(message, type) {
    type = type || 'info';
    var colors = {
      success: { bg: '#ECFDF5', border: '#10B981', text: '#059669', icon: 'check_circle' },
      error:   { bg: '#FEF2F2', border: '#EF4444', text: '#DC2626', icon: 'error' },
      warning: { bg: '#FFFBEB', border: '#F59E0B', text: '#D97706', icon: 'warning' },
      info:    { bg: '#EFF6FF', border: '#3B82F6', text: '#2563EB', icon: 'info' }
    };
    var c = colors[type] || colors.info;

    var el = document.createElement('div');
    el.style.cssText = 'display:flex;align-items:center;gap:8px;padding:12px 20px;background:' + c.bg + ';border-left:3px solid ' + c.border + ';color:' + c.text + ';border-radius:8px;font-size:14px;font-family:Inter,system-ui,sans-serif;box-shadow:0 2px 8px rgba(0,0,0,0.1);pointer-events:auto;animation:slideUp 0.3s ease-out;';
    el.innerHTML = '<span class="material-icons" style="font-size:18px;">' + c.icon + '</span><span>' + escapeHtml(message) + '</span>';

    toastContainer().appendChild(el);

    setTimeout(function () {
      el.style.opacity = '0';
      el.style.transition = 'opacity 0.3s ease';
      setTimeout(function () {
        if (el.parentNode) el.parentNode.removeChild(el);
      }, 300);
    }, Aurelian.config.TOAST_DURATION_MS);
  }

  /** Show loading state in a container */
  function showLoading(containerEl) {
    if (!containerEl) return;
    containerEl.setAttribute('data-original-html', containerEl.innerHTML);
    containerEl.innerHTML = '<div class="flex items-center justify-center py-8"><div class="flex flex-col items-center gap-3"><div class="w-8 h-8 border-2 border-[#E07B3C] border-t-transparent rounded-full animate-spin"></div><span class="text-sm text-[#6F6F6F]">加载中...</span></div></div>';
  }

  /** Restore content after loading */
  function hideLoading(containerEl) {
    if (!containerEl) return;
    var original = containerEl.getAttribute('data-original-html');
    if (original) {
      containerEl.innerHTML = original;
      containerEl.removeAttribute('data-original-html');
    }
  }

  /** Show error state in a container with retry */
  function showError(containerEl, message, retryFn) {
    if (!containerEl) return;
    containerEl.innerHTML =
      '<div class="flex flex-col items-center justify-center py-8 gap-3">' +
      '<span class="material-icons text-[40px] text-[#F87171]">error_outline</span>' +
      '<p class="text-sm text-[#6F6F6F] text-center">' + escapeHtml(message) + '</p>' +
      (retryFn ? '<button class="retry-btn px-4 py-2 border border-[#E8E8E6] rounded-lg text-sm text-[#1A1A1C] hover:border-[#E07B3C] transition-colors">重试</button>' : '') +
      '</div>';
    if (retryFn) {
      var btn = containerEl.querySelector('.retry-btn');
      if (btn) btn.addEventListener('click', retryFn);
    }
  }

  /** Show empty state */
  function showEmpty(containerEl, message, icon, actionLabel, actionFn) {
    if (!containerEl) return;
    var ic = icon || 'inbox';
    containerEl.innerHTML =
      '<div class="flex flex-col items-center justify-center py-8 gap-3">' +
      '<span class="material-icons text-[40px] text-[#A0A0A0]">' + ic + '</span>' +
      '<p class="text-sm text-[#6F6F6F] text-center">' + escapeHtml(message) + '</p>' +
      (actionLabel && actionFn ? '<button class="empty-action-btn px-4 py-2 bg-[#E07B3C] text-white rounded-lg text-sm hover:opacity-85 transition-opacity">' + escapeHtml(actionLabel) + '</button>' : '') +
      '</div>';
    if (actionFn) {
      var btn = containerEl.querySelector('.empty-action-btn');
      if (btn) btn.addEventListener('click', actionFn);
    }
  }

  /** Escape HTML entities */
  function escapeHtml(str) {
    if (!str) return '';
    str = String(str);
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  /** Debounce a function */
  function debounce(fn, ms) {
    var timer;
    return function () {
      var ctx = this, args = arguments;
      clearTimeout(timer);
      timer = setTimeout(function () { fn.apply(ctx, args); }, ms);
    };
  }

  /** Format a file size in bytes to human readable */
  function formatFileSize(bytes) {
    if (!bytes) return '0 B';
    var units = ['B', 'KB', 'MB', 'GB'];
    var i = 0;
    var size = bytes;
    while (size >= 1024 && i < units.length - 1) { size /= 1024; i++; }
    return size.toFixed(i === 0 ? 0 : 1) + ' ' + units[i];
  }

  /** Format ISO date string to locale date */
  function formatDate(isoStr) {
    if (!isoStr) return '—';
    try {
      var d = new Date(isoStr);
      return d.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' }) + ' ' +
             d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    } catch (e) {
      return isoStr;
    }
  }

  return {
    toast: toast,
    showLoading: showLoading,
    hideLoading: hideLoading,
    showError: showError,
    showEmpty: showEmpty,
    escapeHtml: escapeHtml,
    debounce: debounce,
    formatFileSize: formatFileSize,
    formatDate: formatDate
  };
})();

/** Inject toast animation keyframes once */
(function () {
  if (document.getElementById('aurelian-toast-style')) return;
  var style = document.createElement('style');
  style.id = 'aurelian-toast-style';
  style.textContent = '@keyframes slideUp { from { opacity:0; transform:translateY(12px); } to { opacity:1; transform:translateY(0); } }';
  document.head.appendChild(style);
})();
