(function () {
  'use strict';

  var A = window.Aurelian;
  var api = A.api;
  var ui = A.ui;
  var AVATARS = {
    xiaoyun: { imageUrl: '/assets/images/digital-avatar-a.png', speakingImageUrl: '/assets/images/digital-avatar-a-open.png', alt: '男性形象 A' },
    yunchuan: { imageUrl: '/assets/images/digital-avatar-b.png', alt: '形象 B' }
  };
  var currentImageUrl = AVATARS.xiaoyun.imageUrl;
  var lipSyncController = null;

  function byId(id) {
    return document.getElementById(id);
  }

  function config() {
    var role = selectedRole();
    return {
      role: role,
      outfit: byId('avatar-outfit').value,
      imageUrl: currentImageUrl,
      voice: byId('avatar-voice').value,
      speed: Number(byId('avatar-speed').value),
      emotion: byId('avatar-emotion').value,
      lipSync: byId('lip-sync').checked,
      emotionSync: byId('emotion-sync').checked,
      idleMotion: byId('idle-motion').checked
    };
  }

  function selectedRole() {
    var checked = document.querySelector('input[name="avatar-role"]:checked');
    return checked && AVATARS[checked.value] ? checked.value : 'xiaoyun';
  }

  function selectRole(role, useDefaultImage) {
    var nextRole = AVATARS[role] ? role : 'xiaoyun';
    var radio = document.querySelector('input[name="avatar-role"][value="' + nextRole + '"]');
    if (radio) radio.checked = true;
    if (useDefaultImage !== false) currentImageUrl = AVATARS[nextRole].imageUrl;
    byId('avatar-preview-frame').setAttribute('data-avatar-role', nextRole);
    byId('avatar-preview-image').src = currentImageUrl;
    if (currentImageUrl === AVATARS[nextRole].imageUrl && AVATARS[nextRole].speakingImageUrl) {
      byId('avatar-preview-image').setAttribute('data-speaking-src', AVATARS[nextRole].speakingImageUrl);
    } else {
      byId('avatar-preview-image').removeAttribute('data-speaking-src');
    }
    byId('avatar-preview-image').alt = AVATARS[nextRole].alt + '讲解形象预览';
  }

  function applyConfig(c) {
    if (!c) return;
    var role = AVATARS[c.role] ? c.role : 'xiaoyun';
    byId('avatar-outfit').value = c.outfit || 'modern_black';
    byId('avatar-voice').value = c.voice || 'guide_female';
    byId('avatar-speed').value = c.speed || 1;
    byId('avatar-emotion').value = c.emotion || 'friendly';
    byId('lip-sync').checked = c.lipSync !== false;
    byId('emotion-sync').checked = c.emotionSync !== false;
    byId('idle-motion').checked = c.idleMotion !== false;
    currentImageUrl = c.imageUrl && c.imageUrl.indexOf('/uploads/avatar/') === 0 ? c.imageUrl : AVATARS[role].imageUrl;
    selectRole(role, false);
    if (lipSyncController) lipSyncController.setEnabled(byId('lip-sync').checked);
    refreshPreview();
  }

  function refreshPreview() {
    byId('speed-output').textContent = byId('avatar-speed').value + '×';
    byId('preview-line').textContent = '你好，我是智能导游。欢迎来到灵山胜境，让我陪你了解这里的故事。';
    byId('avatar-preview-image').dataset.role = selectedRole();
    byId('avatar-preview-image').dataset.outfit = byId('avatar-outfit').value;
  }

  function uploadImage(file) {
    if (!file) return;
    var data = new FormData();
    data.append('file', file);
    byId('preview-status').textContent = '上传中';
    api.upload('/avatar-settings/image', data).then(function (result) {
      if (result.ok) {
        applyConfig(result.data);
        ui.toast('讲解形象图片已更新', 'success');
      } else {
        ui.toast((result.error && result.error.message) || '图片上传失败', 'error');
      }
      byId('preview-status').textContent = '待命';
      byId('avatar-image-file').value = '';
    });
  }

  function boot() {
    A.auth.guardRole('admin', init);
  }

  function init() {
    var previewAudio = byId('avatar-preview-audio');
    lipSyncController = A.lipSync.attach(previewAudio, byId('avatar-preview-mouth'));
    document.querySelectorAll('input[name="avatar-role"]').forEach(function (radio) {
      radio.addEventListener('change', function () {
        selectRole(radio.value, true);
        refreshPreview();
      });
    });
    ['avatar-outfit', 'avatar-emotion'].forEach(function (id) {
      byId(id).addEventListener('change', refreshPreview);
    });
    byId('lip-sync').addEventListener('change', function () {
      if (lipSyncController) lipSyncController.setEnabled(this.checked);
    });
    byId('avatar-speed').addEventListener('input', refreshPreview);
    byId('avatar-image-file').addEventListener('change', function () {
      uploadImage(this.files && this.files[0]);
    });

    api.get('/avatar-settings').then(function (result) {
      if (result.ok) applyConfig(result.data);
      else ui.toast('讲解形象设置暂时无法读取', 'warning');
    });

    byId('btn-save').addEventListener('click', function () {
      api.put('/avatar-settings', config()).then(function (result) {
        if (result.ok) {
          applyConfig(result.data);
          ui.toast('讲解形象设置已保存', 'success');
        } else {
          ui.toast((result.error && result.error.message) || '设置保存失败', 'error');
        }
      });
    });

    byId('btn-test').addEventListener('click', function () {
      var c = config();
      byId('preview-status').textContent = '试听中';
      api.post('/audio/tts', {
        text: byId('preview-line').textContent,
        voice: c.voice,
        speed: c.speed
      }).then(function (result) {
        if (result.ok && result.data && result.data.audioUrl) {
          previewAudio.src = result.data.audioUrl;
          previewAudio.play().catch(function () { ui.toast('试听音频已准备好，请再次点击试听', 'warning'); });
        } else {
          ui.toast('试听暂时不可用，请稍后重试', 'warning');
        }
      });
    });
    previewAudio.addEventListener('play', function () { byId('preview-status').textContent = '讲解中'; });
    previewAudio.addEventListener('pause', function () { byId('preview-status').textContent = '待命'; });
    previewAudio.addEventListener('ended', function () { byId('preview-status').textContent = '待命'; });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
