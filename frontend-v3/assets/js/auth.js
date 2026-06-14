/**
 * Aurelian Guide — Auth
 * Registration, login, guard, logout.
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

  /** Guard: redirect to landing if not logged in. Returns true if ok. */
  function guard() {
    if (!st.isLoggedIn()) {
      window.location.href = '../../pages/landing/index.html';
      return false;
    }
    return true;
  }

  /** Guard: must have a specific role. Redirects to landing if role mismatch. */
  function guardRole(requiredRole) {
    if (!guard()) return false;
    var role = st.get('role');
    if (role !== requiredRole) {
      window.location.href = '../../pages/landing/index.html';
      return false;
    }
    return true;
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
    logout: logout
  };
})();
