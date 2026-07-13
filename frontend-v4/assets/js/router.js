/**
 * Aurelian Guide — Router
 * Page navigation helpers. All paths relative to frontend-v4 root.
 */
window.Aurelian = window.Aurelian || {};

Aurelian.router = (function () {
  'use strict';

  /** Map page names to paths (relative to frontend-v4 index) */
  var PAGE_PATHS = {
    'home':            'index.html',
    'landing':         'pages/landing/index.html',
    'guide-panel':     'pages/guide-panel/index.html',
    'dashboard':       'pages/dashboard/index.html',
    'user-portal':     'pages/user-portal/index.html',
    'knowledge-base':  'pages/knowledge-base/index.html',
    'ai-assistant':    'pages/ai-assistant/index.html',
    'vision':          'pages/vision/index.html',
    'recommend':       'pages/recommend/index.html',
    'avatar-studio':   'pages/avatar-studio/index.html'
  };

  /** Get the base path (frontend-v4 root) from current location */
  function getBase() {
    var path = window.location.pathname;
    // Remove any page-specific segments to get to frontend-v3 root
    if (path.indexOf('/pages/') !== -1) {
      return '../../';
    }
    if (path.indexOf('/assets/') !== -1) {
      return '../../';
    }
    return '';
  }

  /** Navigate to a named page */
  function go(page) {
    var base = getBase();
    var target = PAGE_PATHS[page];
    if (!target) {
      console.error('Unknown page:', page);
      return;
    }
    var url = base + target;
    if (Aurelian.navigateWithMotion) Aurelian.navigateWithMotion(url);
    else window.location.href = url;
  }

  /** Navigate back */
  function goBack() {
    window.history.back();
  }

  /** Store params and navigate to page */
  function withParams(page, params) {
    if (params) {
      Object.keys(params).forEach(function (k) {
        Aurelian.state.set(k, params[k]);
      });
    }
    go(page);
  }

  /** Get current page name from path */
  function getPage() {
    var path = window.location.pathname;
    if (path.indexOf('/landing/') !== -1) return 'landing';
    if (path.indexOf('/guide-panel/') !== -1) return 'guide-panel';
    if (path.indexOf('/dashboard/') !== -1) return 'dashboard';
    if (path.indexOf('/user-portal/') !== -1) return 'user-portal';
    if (path.indexOf('/knowledge-base/') !== -1) return 'knowledge-base';
    if (path.indexOf('/ai-assistant/') !== -1) return 'ai-assistant';
    if (path.indexOf('/vision/') !== -1) return 'vision';
    if (path.indexOf('/recommend/') !== -1) return 'recommend';
    return 'home';
  }

  return {
    go: go,
    goBack: goBack,
    withParams: withParams,
    getPage: getPage,
    PAGE_PATHS: PAGE_PATHS
  };
})();
