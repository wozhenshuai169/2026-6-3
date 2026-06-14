/**
 * Landing Page — Identity Selection & Registration
 */
(function () {
  'use strict';

  var A = window.Aurelian;
  var state = A.state;
  var auth = A.auth;
  var api = A.api;
  var ui = A.ui;
  var router = A.router;

  // DOM refs
  var btnVisitor, btnLeader;
  var modal, dialog, modalTitle, modalClose, modalName, modalError, modalSubmit;
  var chosenRole = null;

  function init() {
    // If already logged in, redirect to appropriate page
    if (state.isLoggedIn()) {
      var role = state.get('role');
      if (role === 'visitor') { router.go('user-portal'); return; }
      if (role === 'tour_leader') { router.go('guide-panel'); return; }
    }

    // Cache DOM refs
    btnVisitor = document.getElementById('btn-visitor');
    btnLeader = document.getElementById('btn-leader');
    modal = document.getElementById('register-modal');
    dialog = document.getElementById('register-dialog');
    modalTitle = document.getElementById('modal-title');
    modalClose = document.getElementById('modal-close');
    modalName = document.getElementById('modal-name');
    modalError = document.getElementById('modal-error');
    modalSubmit = document.getElementById('modal-submit');

    // Bind events
    if (btnVisitor) btnVisitor.addEventListener('click', function () { openModal('visitor'); });
    if (btnLeader) btnLeader.addEventListener('click', function () { openModal('tour_leader'); });
    if (modalClose) modalClose.addEventListener('click', closeModal);
    if (modal) modal.addEventListener('click', function (e) { if (e.target === modal) closeModal(); });
    if (modalSubmit) modalSubmit.addEventListener('click', handleSubmit);
    if (modalName) modalName.addEventListener('keydown', function (e) { if (e.key === 'Enter') handleSubmit(); });
  }

  function openModal(role) {
    chosenRole = role;
    var label = role === 'visitor' ? '游客' : '团长';
    if (modalTitle) modalTitle.textContent = label + ' — 输入你的名字';
    if (modalName) { modalName.value = ''; modalName.focus(); }
    if (modalError) modalError.classList.add('hidden');
    if (modalSubmit) { modalSubmit.disabled = false; modalSubmit.textContent = '开始导览'; }
    if (modal) modal.classList.remove('hidden');
    // Trigger re-animation
    if (dialog) { dialog.classList.remove('animate-modal-in'); void dialog.offsetWidth; dialog.classList.add('animate-modal-in'); }
  }

  function closeModal() {
    if (modal) modal.classList.add('hidden');
    chosenRole = null;
  }

  function handleSubmit() {
    var name = (modalName.value || '').trim();
    // Validate
    if (name.length < 2) {
      if (modalError) { modalError.textContent = '昵称至少需要2个字'; modalError.classList.remove('hidden'); }
      return;
    }
    if (modalError) modalError.classList.add('hidden');
    // Disable button, show loading
    if (modalSubmit) { modalSubmit.disabled = true; modalSubmit.textContent = '注册中...'; }

    // Generate a simple password
    var password = 'guide_' + Date.now();

    auth.register(name, password).then(function (result) {
      if (result.ok) {
        // Store role
        state.set('role', chosenRole);
        state.save();
        ui.toast('注册成功，欢迎！', 'success');

        // Navigate
        if (chosenRole === 'visitor') {
          router.go('user-portal');
        } else {
          router.go('guide-panel');
        }
      } else {
        var msg = (result.error && result.error.message) || '注册失败，请重试';
        if (modalError) { modalError.textContent = msg; modalError.classList.remove('hidden'); }
        if (modalSubmit) { modalSubmit.disabled = false; modalSubmit.textContent = '重试'; }
      }
    });
  }

  // Boot
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
