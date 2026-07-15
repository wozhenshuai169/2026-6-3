(function () {
  'use strict';

  var A = window.Aurelian;
  var api = A.api;
  var ui = A.ui;
  var currentImageUrl = '/assets/images/digital-guide-main.webp';

  function byId(id) {
    return document.getElementById(id);
  }

  function config() {
    return {
      role: byId('avatar-role').value,
      outfit: byId('avatar-outfit').value,
      imageUrl: currentImageUrl,
      voice: byId('avatar-voice').value,
      speed: Number(byId('avatar-speed').value),
      emotion: byId('avatar-emotion').value,
      lipSync: false,
      emotionSync: byId('emotion-sync').checked,
      idleMotion: byId('idle-motion').checked
    };
  }

  function applyConfig(c) {
    if (!c) return;
    byId('avatar-role').value = c.role || 'xiaoyun';
    byId('avatar-outfit').value = c.outfit || 'modern_black';
    byId('avatar-voice').value = c.voice || 'guide_female';
    byId('avatar-speed').value = c.speed || 1;
    byId('avatar-emotion').value = c.emotion || 'friendly';
    byId('emotion-sync').checked = c.emotionSync !== false;
    byId('idle-motion').checked = c.idleMotion !== false;
    currentImageUrl = c.imageUrl || currentImageUrl;
    byId('avatar-preview-image').src = currentImageUrl;
    refreshPreview();
  }

  function refreshPreview() {
    var roleNames = { xiaoyun: '小云', yunchuan: '云川', tongtong: '童童' };
    var role = byId('avatar-role').value;
    byId('speed-output').textContent = byId('avatar-speed').value + '×';
    byId('preview-line').textContent = '你好，我是' + (roleNames[role] || '讲解员') + '。欢迎来到灵山胜境，让我陪你了解这里的故事。';
    byId('avatar-preview-image').dataset.role = role;
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
    ['avatar-role', 'avatar-outfit', 'avatar-emotion'].forEach(function (id) {
      byId(id).addEventListener('change', refreshPreview);
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
          new Audio(result.data.audioUrl).play().catch(function () {});
        } else {
          ui.toast('试听暂时不可用，请稍后重试', 'warning');
        }
        setTimeout(function () { byId('preview-status').textContent = '待命'; }, 1800);
      });
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
