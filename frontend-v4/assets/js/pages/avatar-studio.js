(function () {
  'use strict';

  var A = window.Aurelian;
  var api = A.api;
  var ui = A.ui;

  function byId(id) {
    return document.getElementById(id);
  }

  function config() {
    return {
      role: byId('avatar-role').value,
      outfit: byId('avatar-outfit').value,
      voice: byId('avatar-voice').value,
      speed: Number(byId('avatar-speed').value),
      emotion: byId('avatar-emotion').value,
      lipSync: byId('lip-sync').checked,
      emotionSync: byId('emotion-sync').checked,
      idleMotion: byId('idle-motion').checked
    };
  }

  function boot() {
    A.auth.guardRole('admin', init);
  }

  function init() {
    var saved = localStorage.getItem('aurelian_avatar_config');
    if (saved) {
      try {
        var c = JSON.parse(saved);
        byId('avatar-voice').value = c.voice || 'guide_female';
        byId('avatar-speed').value = c.speed || 1;
        byId('lip-sync').checked = c.lipSync !== false;
        byId('emotion-sync').checked = c.emotionSync !== false;
        byId('idle-motion').checked = c.idleMotion !== false;
      } catch (e) {
        // Ignore malformed local preview settings.
      }
    }

    byId('speed-output').textContent = byId('avatar-speed').value + 'x';
    byId('avatar-speed').addEventListener('input', function () {
      byId('speed-output').textContent = this.value + 'x';
    });

    byId('btn-save').addEventListener('click', function () {
      localStorage.setItem('aurelian_avatar_config', JSON.stringify(config()));
      ui.toast('数字人配置已保存', 'success');
    });

    byId('btn-test').addEventListener('click', function () {
      var c = config();
      byId('preview-status').textContent = '试听中';
      api.post('/audio/tts', {
        text: byId('preview-line').textContent,
        voice: c.voice,
        speed: c.speed
      }).then(function (r) {
        if (r.ok && r.data && r.data.audioUrl) {
          var audio = new Audio(r.data.audioUrl);
          audio.play().catch(function () {});
          ui.toast('正在试听当前音色', 'info');
        } else {
          ui.toast('已切换到本地预览模式', 'info');
        }
        setTimeout(function () {
          byId('preview-status').textContent = '待命';
        }, 1800);
      });
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
