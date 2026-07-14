/**
 * Landing Page — Identity Selection (Visitor / Leader / Admin)
 */
(function () {
  'use strict';

  var A = window.Aurelian, state = A.state, auth = A.auth, api = A.api, ui = A.ui, router = A.router;

  var btnVisitor, btnLeader, btnAdmin;
  var modal, dialog, modalTitle, modalClose, modalName, modalVoiceGroup, modalVoice, modalError, modalSubmit;
  var adminModal, adminClose, adminPasscode, adminError, adminSubmit;
  var chosenRole = null;
  var demoAdmin = false;

  function init() {
    // Demo mode
    if (new URLSearchParams(location.search).get('demo') === '1') {
      var demoRole = new URLSearchParams(location.search).get('role') || 'tour_leader';
      if (demoRole === 'admin') demoAdmin = true;
      else {
        auth.guest(demoRole==='visitor'?'游客Demo':'团长Demo', demoRole).then(function(result){
          if (result.ok) router.go(demoRole==='visitor'?'user-portal':'guide-panel');
        });
        return;
      }
    }

    // Landing is the explicit main menu. Do not auto-route by stored role here;
    // returning users should stay on this page until they choose an entry.
    if (state.isLoggedIn()) {
      auth.me().then(function(result) {
        if (!result.ok) state.clear();
      });
    }

    // Cache DOM refs
    btnVisitor = document.getElementById('btn-visitor');
    btnLeader = document.getElementById('btn-leader');
    btnAdmin = document.getElementById('btn-admin');
    modal = document.getElementById('register-modal');
    dialog = document.getElementById('register-dialog');
    modalTitle = document.getElementById('modal-title');
    modalClose = document.getElementById('modal-close');
    modalName = document.getElementById('modal-name');
    modalVoiceGroup = document.getElementById('modal-voice-group');
    modalVoice = document.getElementById('modal-voice');
    modalError = document.getElementById('modal-error');
    modalSubmit = document.getElementById('modal-submit');
    adminModal = document.getElementById('admin-modal');
    adminClose = document.getElementById('admin-modal-close');
    adminPasscode = document.getElementById('admin-passcode');
    adminError = document.getElementById('admin-error');
    adminSubmit = document.getElementById('admin-submit');

    // Bind events
    if (btnVisitor) btnVisitor.addEventListener('click', function () { openModal('visitor'); });
    if (btnLeader) btnLeader.addEventListener('click', function () { openModal('tour_leader'); });
    if (btnAdmin) btnAdmin.addEventListener('click', openAdminModal);
    if (modalClose) modalClose.addEventListener('click', closeModal);
    if (modal) modal.addEventListener('click', function (e) { if (e.target === modal) closeModal(); });
    if (modalSubmit) modalSubmit.addEventListener('click', handleSubmit);
    if (modalName) modalName.addEventListener('keydown', function (e) { if (e.key === 'Enter') handleSubmit(); });
    // Admin modal
    if (adminClose) adminClose.addEventListener('click', closeAdminModal);
    if (adminModal) adminModal.addEventListener('click', function (e) { if (e.target === adminModal) closeAdminModal(); });
    if (adminSubmit) adminSubmit.addEventListener('click', handleAdminAuth);
    if (adminPasscode) adminPasscode.addEventListener('keydown', function (e) { if (e.key === 'Enter') handleAdminAuth(); });
    if (demoAdmin) openAdminModal();
  }

  function openModal(role) {
    chosenRole = role;
    var label = role === 'visitor' ? '游客' : '团长';
    if (modalTitle) modalTitle.textContent = label + ' — 输入你的名字';
    if (modalVoiceGroup) modalVoiceGroup.classList.toggle('hidden', role !== 'visitor');
    if (modalVoice && role === 'visitor') modalVoice.value = state.get('narrationVoice') || 'guide_female';
    if (modalName) { modalName.value = ''; modalName.focus(); }
    if (modalError) modalError.classList.add('hidden');
    if (modalSubmit) { modalSubmit.disabled = false; modalSubmit.textContent = '开始导览'; }
    if (modal) modal.classList.remove('hidden');
    if (dialog) { dialog.classList.remove('animate-modal-in'); void dialog.offsetWidth; dialog.classList.add('animate-modal-in'); }
  }

  function closeModal() {
    if (modal) modal.classList.add('hidden');
    chosenRole = null;
  }

  function handleSubmit() {
    var name = (modalName.value || '').trim();
    if (name.length < 2) {
      if (modalError) { modalError.textContent = '昵称至少需要2个字'; modalError.classList.remove('hidden'); }
      return;
    }
    if (modalError) modalError.classList.add('hidden');
    if (modalSubmit) { modalSubmit.disabled = true; modalSubmit.textContent = '注册中...'; }

    auth.guest(name, chosenRole).then(function (result) {
      if (result.ok) {
        if (chosenRole === 'visitor' && modalVoice) state.set('narrationVoice', modalVoice.value);
        ui.toast('注册成功，欢迎！', 'success');
        if (chosenRole === 'visitor') router.go('user-portal');
        else router.go('guide-panel');
      } else {
        var msg = (result.error && result.error.message) || '注册失败，请重试';
        if (modalError) { modalError.textContent = msg; modalError.classList.remove('hidden'); }
        if (modalSubmit) { modalSubmit.disabled = false; modalSubmit.textContent = '重试'; }
      }
    });
  }

  // === Admin auth ===
  function openAdminModal() {
    if (adminPasscode) { adminPasscode.value = ''; adminPasscode.focus(); }
    if (adminError) adminError.classList.add('hidden');
    if (adminModal) adminModal.classList.remove('hidden');
  }

  function closeAdminModal() {
    if (adminModal) adminModal.classList.add('hidden');
  }

  function handleAdminAuth() {
    var code = (adminPasscode.value || '').trim();
    auth.login(A.config.ADMIN_USER_NAME, code).then(function(result){
      if (!result.ok) { if (adminError) adminError.classList.remove('hidden'); return; }
      if (state.get('role') !== 'admin') {
        if (adminError) {
          adminError.textContent = '当前账号不是管理员';
          adminError.classList.remove('hidden');
        }
        state.clear();
        return;
      }
      if (adminError) adminError.classList.add('hidden');
      ui.toast('验证通过，欢迎管理员！', 'success');
      router.go('knowledge-base');
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
