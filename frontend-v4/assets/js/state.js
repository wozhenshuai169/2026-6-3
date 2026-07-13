/**
 * Aurelian Guide — State Manager
 * In-memory key/value store backed by sessionStorage.
 * Survives page navigation within the same tab session.
 */
window.Aurelian = window.Aurelian || {};

Aurelian.state = (function () {
  'use strict';

  // Keys that get persisted to sessionStorage
  var PERSIST_KEYS = ['userId', 'userName', 'token', 'role', 'expiresAt', 'roomId', 'currentSpotId', 'routeId'];
  var _store = {};

  /** Save persistable keys to sessionStorage */
  function save() {
    PERSIST_KEYS.forEach(function (k) {
      if (_store[k] !== undefined && _store[k] !== null) {
        try { sessionStorage.setItem('aurelian_' + k, _store[k]); } catch (e) { /* quota exceeded, ignore */ }
      }
    });
  }

  /** Load persisted keys from sessionStorage */
  function load() {
    PERSIST_KEYS.forEach(function (k) {
      try {
        var v = sessionStorage.getItem('aurelian_' + k);
        if (v !== null) _store[k] = v;
      } catch (e) { /* ignore */ }
    });
  }

  /** Get a value */
  function get(key) {
    return _store[key];
  }

  /** Set a value. If key is persistable, auto-saves. */
  function set(key, value) {
    _store[key] = value;
    if (PERSIST_KEYS.indexOf(key) !== -1) save();
  }

  /** Remove a key */
  function remove(key) {
    delete _store[key];
    try { sessionStorage.removeItem('aurelian_' + key); } catch (e) { /* ignore */ }
  }

  /** Clear all state (logout) */
  function clear() {
    _store = {};
    PERSIST_KEYS.forEach(function (k) {
      try { sessionStorage.removeItem('aurelian_' + k); } catch (e) { /* ignore */ }
    });
  }

  /** Clear room state that belongs to a previous identity. */
  function clearBusinessContext() {
    ['roomId', 'currentSpotId', 'routeId'].forEach(remove);
  }

  /** Whether user is logged in (has token) */
  function isLoggedIn() {
    return !!get('token');
  }

  // Restore on load
  load();

  return {
    get: get,
    set: set,
    remove: remove,
    clear: clear,
    clearBusinessContext: clearBusinessContext,
    save: save,
    load: load,
    isLoggedIn: isLoggedIn
  };
})();
