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

  var DIRECTION_KEY = 'aurelian:navigation-direction';
  var root = document.documentElement;
  var isNavigating = false;
  var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var supportsNativeTransition = Boolean(document.startViewTransition && 'onpageswap' in window);
  var incomingDirection = readDirection();

  root.dataset.navigationDirection = incomingDirection;
  if (!supportsNativeTransition) root.classList.add('page-motion-fallback');

  function readDirection() {
    try {
      return window.sessionStorage.getItem(DIRECTION_KEY) || 'forward';
    } catch (error) {
      return 'forward';
    }
  }

  function rememberDirection(direction) {
    root.dataset.navigationDirection = direction;
    try {
      window.sessionStorage.setItem(DIRECTION_KEY, direction);
    } catch (error) {
      // Navigation still works when storage is unavailable.
    }
  }

  function samePageHash(anchor) {
    return anchor.pathname === window.location.pathname && anchor.hash;
  }

  function isInternalPage(anchor) {
    return anchor.origin === window.location.origin && /\.html(?:$|[?#])/.test(anchor.href);
  }

  function finishNavigation(url, mode) {
    if (mode === 'replace') window.location.replace(url);
    else window.location.assign(url);
  }

  function navigateWithMotion(url, options) {
    options = options || {};
    if (isNavigating) return;
    isNavigating = true;

    var direction = options.direction || (options.replace ? 'replace' : 'forward');
    rememberDirection(direction);

    if (reduceMotion || supportsNativeTransition || !document.body) {
      finishNavigation(url, options.replace ? 'replace' : 'push');
      return;
    }

    document.body.classList.add('is-page-leaving');
    window.setTimeout(function () {
      finishNavigation(url, options.replace ? 'replace' : 'push');
    }, 180);
  }

  function navigateBack(fallbackUrl) {
    if (isNavigating) return;
    if (window.history.length <= 1 && fallbackUrl) {
      navigateWithMotion(fallbackUrl, { replace: true });
      return;
    }

    isNavigating = true;
    rememberDirection('back');

    if (reduceMotion || supportsNativeTransition || !document.body) {
      window.history.back();
      return;
    }

    document.body.classList.add('is-page-leaving');
    window.setTimeout(function () { window.history.back(); }, 180);
  }

  window.Aurelian.navigateWithMotion = navigateWithMotion;
  window.Aurelian.navigateBack = navigateBack;

  document.addEventListener('click', function (event) {
    var button = event.target.closest && event.target.closest('button[onclick]');
    if (!button || event.defaultPrevented) return;

    var inlineAction = button.getAttribute('onclick') || '';
    if (/\bhistory\.back\s*\(\s*\)/.test(inlineAction)) {
      event.preventDefault();
      event.stopImmediatePropagation();
      navigateBack('../../pages/landing/index.html');
      return;
    }

    var hrefMatch = inlineAction.match(/\b(?:window\.)?location\.href\s*=\s*(['"])(.*?)\1/);
    if (hrefMatch) {
      event.preventDefault();
      event.stopImmediatePropagation();
      navigateWithMotion(hrefMatch[2]);
    }
  }, true);

  document.addEventListener('click', function (event) {
    var anchor = event.target.closest && event.target.closest('a[href]');
    if (!anchor || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    if (anchor.target || anchor.hasAttribute('download') || anchor.hasAttribute('data-no-transition') || samePageHash(anchor) || !isInternalPage(anchor)) return;
    event.preventDefault();
    navigateWithMotion(anchor.href);
  });

  window.addEventListener('pageshow', function () {
    isNavigating = false;
    if (!document.body) return;
    document.body.classList.remove('is-page-leaving');

    if (!supportsNativeTransition && !reduceMotion && incomingDirection) {
      document.body.classList.add('is-page-entering');
      window.setTimeout(function () {
        document.body.classList.remove('is-page-entering');
      }, 340);
    }

    window.setTimeout(function () {
      try { window.sessionStorage.removeItem(DIRECTION_KEY); } catch (error) {}
    }, 400);
  });
})();
