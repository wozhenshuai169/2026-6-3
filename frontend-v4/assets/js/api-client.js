/**
 * Aurelian Guide — API Client
 * Fetch wrapper with auto token injection, retry, and error mapping.
 * All methods return { ok: boolean, data?: any, error?: { status, message, code } }
 */
window.Aurelian = window.Aurelian || {};

Aurelian.api = (function () {
  'use strict';

  var cfg = Aurelian.config;
  var state = Aurelian.state;

  /** Build full URL from endpoint path */
  function url(endpoint) {
    return cfg.API_BASE + endpoint;
  }

  /** Generic fetch with timeout, retry, and error mapping */
  function request(method, endpoint, body, isFormData) {
    var attempts = 0;
    var maxAttempts = cfg.MAX_RETRIES + 1;

    function tryOnce() {
      return new Promise(function (resolve) {
        var controller = new AbortController();
        var timer = setTimeout(function () { controller.abort(); }, cfg.REQUEST_TIMEOUT_MS);

        var opts = {
          method: method,
          signal: controller.signal,
          headers: {}
        };
        if (state.isLoggedIn()) {
          opts.headers.Authorization = 'Bearer ' + state.get('token');
        }

        if (body) {
          if (isFormData) {
            opts.body = body;
            // Let browser set Content-Type for FormData (with boundary)
          } else {
            opts.body = JSON.stringify(body);
            opts.headers['Content-Type'] = 'application/json';
          }
        }

        fetch(url(endpoint), opts)
          .then(function (res) {
            clearTimeout(timer);
            // 401 — clear auth and redirect
            if (res.status === 401) {
              Aurelian.state.clear();
              if (Aurelian.router) {
                Aurelian.router.go('landing');
              } else if (Aurelian.navigateWithMotion) {
                Aurelian.navigateWithMotion('../../pages/landing/index.html', { replace: true });
              } else {
                window.location.href = '../../pages/landing/index.html';
              }
              resolve({ ok: false, error: { status: 401, message: '登录已过期，请重新登录', code: 'UNAUTHORIZED' } });
              return;
            }
            // Try to parse JSON
            return res.json().then(function (data) {
              if (res.ok) {
                resolve({ ok: true, data: data });
              } else {
                resolve({
                  ok: false,
                  error: {
                    status: res.status,
                    message: res.status === 403 ? '无权限访问该资源' : ((data && data.detail) || data || '请求失败'),
                    code: (data && data.errorCode) || ('HTTP_' + res.status)
                  }
                });
              }
            }).catch(function () {
              // Response not JSON
              if (res.ok) {
                resolve({ ok: true, data: null });
              } else {
                resolve({ ok: false, error: { status: res.status, message: res.status === 403 ? '无权限访问该资源' : ('请求失败 (' + res.status + ')'), code: 'HTTP_' + res.status } });
              }
            });
          })
          .catch(function (err) {
            clearTimeout(timer);
            if (err.name === 'AbortError') {
              resolve({ ok: false, error: { status: 0, message: '请求超时，请检查网络连接', code: 'TIMEOUT' } });
            } else {
              resolve({ ok: false, error: { status: 0, message: '暂时无法连接服务，请稍后再试', code: 'NETWORK_ERROR' } });
            }
          });
      });
    }

    function retry() {
      return tryOnce().then(function (result) {
        if (!result.ok && result.error && result.error.status >= 500 && attempts < maxAttempts - 1) {
          attempts++;
          return new Promise(function (r) { setTimeout(r, cfg.RETRY_DELAY_MS); }).then(retry);
        }
        return result;
      });
    }

    return retry();
  }

  /** GET request */
  function get(endpoint) {
    return request('GET', endpoint, null, false);
  }

  /** POST request with JSON body */
  function post(endpoint, body) {
    return request('POST', endpoint, body || {}, false);
  }

  function patch(endpoint, body) {
    return request('PATCH', endpoint, body || {}, false);
  }

  function put(endpoint, body) {
    return request('PUT', endpoint, body || {}, false);
  }

  function remove(endpoint) {
    return request('DELETE', endpoint, null, false);
  }

  /** POST request with FormData (file upload) */
  function upload(endpoint, formData) {
    return request('POST', endpoint, formData, true);
  }

  return {
    get: get,
    post: post,
    put: put,
    patch: patch,
    delete: remove,
    upload: upload,
    url: url
  };
})();
