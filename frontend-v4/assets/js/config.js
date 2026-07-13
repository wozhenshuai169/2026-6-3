/**
 * Aurelian Guide — Configuration
 * Global constants and settings for the frontend application.
 */
window.Aurelian = window.Aurelian || {};

Aurelian.config = {
  // Backend API base URL (served from same origin via StaticFiles mount)
  API_BASE: '/api',
  UPLOADS_BASE: '/uploads',
  ADMIN_USER_NAME: 'admin',

  // Polling intervals (milliseconds)
  POLL_INTERVAL_ROOM: 5000,       // Room status polling
  POLL_INTERVAL_AVATAR: 3000,     // Avatar state polling
  DASHBOARD_REFRESH_MS: 30000,    // Dashboard auto-refresh

  // UI timing
  TOAST_DURATION_MS: 4000,

  // Network
  REQUEST_TIMEOUT_MS: 15000,
  MAX_RETRIES: 1,
  RETRY_DELAY_MS: 1000,
};

(function () {
  'use strict';
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  function samePageHash(anchor) {
    return anchor.pathname === window.location.pathname && anchor.hash;
  }

  function isInternalPage(anchor) {
    return anchor.origin === window.location.origin && /\.html(?:$|[?#])/.test(anchor.href);
  }

  function navigateWithMotion(url) {
    document.body.classList.add('is-leaving');
    window.setTimeout(function () { window.location.href = url; }, 130);
  }

  window.Aurelian.navigateWithMotion = navigateWithMotion;

  document.addEventListener('click', function (event) {
    var anchor = event.target.closest && event.target.closest('a[href]');
    if (!anchor || event.defaultPrevented || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    if (anchor.target || anchor.hasAttribute('download') || samePageHash(anchor) || !isInternalPage(anchor)) return;
    event.preventDefault();
    navigateWithMotion(anchor.href);
  });
})();
