/**
 * Aurelian Guide — Auth
 * Registration, login, guard, logout.
 * Guards show inline overlay instead of hard redirect.
 */
window.Aurelian = window.Aurelian || {};

Aurelian.auth = (function () {
  'use strict';

  var api = Aurelian.api;
  var st = Aurelian.state;

  /** Register a new user */
  function register(userName, password) {
    return api.post('/auth/register', {
      userName: userName,
      password: password
    }).then(function (result) {
      if (result.ok && result.data) {
        st.set('userId', result.data.userId);
        st.set('userName', result.data.userName);
        st.set('token', result.data.token);
        st.save();
      }
      return result;
    });
  }

  /** Check if logged in. Returns true if ok. */
  function isLoggedIn() {
    return st.isLoggedIn();
  }

  /** Guard: if not logged in, show overlay instead of redirect. Returns true if ok. */
  function guard(onPass) {
    if (!st.isLoggedIn()) {
      showAuthOverlay(onPass);
      return false;
    }
    if (onPass) onPass();
    return true;
  }

  /** Guard with role check */
  function guardRole(requiredRole, onPass) {
    if (!st.isLoggedIn()) {
      showAuthOverlay(onPass);
      return false;
    }
    var role = st.get('role');
    if (role !== requiredRole) {
      showAuthOverlay(onPass, requiredRole);
      return false;
    }
    if (onPass) onPass();
    return true;
  }

  /** Show inline auth overlay with demo option */
  function showAuthOverlay(onPass, requiredRole) {
    // Remove existing overlay
    var existing = document.getElementById('auth-overlay');
    if (existing) existing.remove();

    var overlay = document.createElement('div');
    overlay.id = 'auth-overlay';
    overlay.style.cssText = 'position:fixed;inset:0;z-index:9999;display:flex;align-items:center;justify-content:center;background:rgba(26,26,28,0.3);backdrop-filter:blur(6px);';

    var roleLabel = requiredRole === 'tour_leader' ? '团长' : (requiredRole === 'visitor' ? '游客' : '');
    var hint = roleLabel ? '此页面需要以「' + roleLabel + '」身份访问' : '请先选择身份开始体验';

    overlay.innerHTML =
      '<div style="background:#fff;border:1px solid #E8E8E6;border-radius:16px;padding:32px;max-width:360px;width:90%;text-align:center;box-shadow:0 4px 24px rgba(0,0,0,0.08)">' +
        '<span class="material-symbols-outlined" style="font-size:48px;color:#E07B3C;margin-bottom:12px;display:block">person_alert</span>' +
        '<h3 style="font-family:\'Noto Serif SC\',serif;font-size:18px;font-weight:500;color:#1A1A1C;margin:0 0 8px">需要登录</h3>' +
        '<p style="font-size:13px;color:#6F6F6F;margin:0 0 20px;line-height:1.5">' + hint + '</p>' +
        '<div style="display:flex;flex-direction:column;gap:8px">' +
          (requiredRole === 'tour_leader' || !requiredRole
            ? '<button id="auth-demo-leader" style="width:100%;padding:12px;background:#E07B3C;color:#fff;border:none;border-radius:10px;font-size:14px;font-weight:500;cursor:pointer">🎯 以团长身份体验</button>'
            : '') +
          (requiredRole === 'visitor' || !requiredRole
            ? '<button id="auth-demo-visitor" style="width:100%;padding:12px;background:#E07B3C;color:#fff;border:none;border-radius:10px;font-size:14px;font-weight:500;cursor:pointer">👤 以游客身份体验</button>'
            : '') +
          '<a href="../../pages/landing/index.html" style="display:block;padding:10px;color:#6F6F6F;font-size:12px;text-decoration:none">前往注册页面 →</a>' +
        '</div>' +
      '</div>';

    document.body.appendChild(overlay);

    // Bind demo buttons
    var btnL = document.getElementById('auth-demo-leader');
    var btnV = document.getElementById('auth-demo-visitor');

    function setupDemo(role) {
      st.set('token', 'demo-' + Date.now());
      st.set('userId', 'demo-' + role);
      st.set('userName', role === 'visitor' ? '游客Demo' : '团长Demo');
      st.set('role', role);
      st.save();
      overlay.remove();
      if (onPass) onPass();
      else window.location.reload();
    }

    if (btnL) btnL.addEventListener('click', function(){ setupDemo('tour_leader'); });
    if (btnV) btnV.addEventListener('click', function(){ setupDemo('visitor'); });
  }

  /** Logout */
  function logout() {
    st.clear();
    window.location.href = '../../pages/landing/index.html';
  }

  return {
    register: register,
    guard: guard,
    guardRole: guardRole,
    logout: logout,
    isLoggedIn: isLoggedIn
  };
})();
