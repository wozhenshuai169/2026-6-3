/**
 * User Portal — Tourist Tour Interface
 */
(function () {
  'use strict';
  var A = window.Aurelian, state = A.state, api = A.api, ui = A.ui, router = A.router, comp = A.components;

  var roomId = state.get('roomId');
  var roomPollTimer = null;
  var avatarPollTimer = null;
  var members = [];
  var currentSpotId = null;

  // DOM
  var els = {};

  function init() {
    if (!A.auth.guardRole('visitor')) return;
    cacheDom();
    bindEvents();
    if (roomId) {
      startRoomMode();
    } else {
      showJoinOverlay();
    }
  }

  function cacheDom() {
    ['avatarStatusDot','avatarStatusLabel','roomJoinOverlay','roomCodeInput','roomJoinBtn','roomJoinError',
     'memberListContainer','menuToggle','menuClose','functionOverlay',
     'fnKnowledge','fnAudio','fnMap','fnReport',
     'fnResultModal','fnResultTitle','fnResultClose','fnResultBody'].forEach(function(id) {
      var camel = id.replace(/-([a-z])/g, function(m,c){ return c.toUpperCase(); });
      els[camel] = document.getElementById(id) || els[camel];
    });
  }

  function bindEvents() {
    if (els.menuToggle) els.menuToggle.addEventListener('click', function(){ els.functionOverlay.classList.remove('hidden'); });
    if (els.menuClose) els.menuClose.addEventListener('click', function(){ els.functionOverlay.classList.add('hidden'); });
    if (els.roomJoinBtn) els.roomJoinBtn.addEventListener('click', handleJoinRoom);
    if (els.roomCodeInput) els.roomCodeInput.addEventListener('keydown', function(e){ if (e.key==='Enter') handleJoinRoom(); });
    if (els.fnKnowledge) els.fnKnowledge.addEventListener('click', function(){ handleFunction('knowledge'); });
    if (els.fnAudio) els.fnAudio.addEventListener('click', function(){ handleFunction('audio'); });
    if (els.fnMap) els.fnMap.addEventListener('click', function(){ handleFunction('map'); });
    if (els.fnReport) els.fnReport.addEventListener('click', function(){ handleFunction('assistant'); });
    if (els.fnResultClose) els.fnResultClose.addEventListener('click', function(){ els.fnResultModal.classList.add('hidden'); });

    // Buttons micro-interaction
    document.querySelectorAll('button:not(#menu-toggle):not(#menu-close)').forEach(function(btn) {
      btn.addEventListener('mousedown', function(){ btn.style.transform='scale(0.98)'; });
      btn.addEventListener('mouseup', function(){ btn.style.transform='scale(1)'; });
      btn.addEventListener('mouseleave', function(){ btn.style.transform='scale(1)'; });
    });
  }

  function showJoinOverlay() {
    if (els.roomJoinOverlay) els.roomJoinOverlay.classList.remove('hidden');
  }

  function hideJoinOverlay() {
    if (els.roomJoinOverlay) els.roomJoinOverlay.classList.add('hidden');
  }

  function handleJoinRoom() {
    var code = (els.roomCodeInput.value || '').trim();
    if (!code) { showJoinError('请输入房间号'); return; }
    if (els.roomJoinBtn) { els.roomJoinBtn.disabled = true; els.roomJoinBtn.textContent = '加入中...'; }
    if (els.roomJoinError) els.roomJoinError.classList.add('hidden');

    api.post('/rooms/' + code + '/join', { token: state.get('token') }).then(function(r) {
      if (r.ok) {
        roomId = code;
        state.set('roomId', roomId);
        hideJoinOverlay();
        ui.toast('加入房间成功！', 'success');
        startRoomMode();
      } else {
        var msg = (r.error && r.error.message) || '加入失败';
        if (r.error && r.error.status === 404) msg = '房间不存在，请检查房间号';
        showJoinError(msg);
        if (els.roomJoinBtn) { els.roomJoinBtn.disabled = false; els.roomJoinBtn.textContent = '加入房间'; }
      }
    });
  }

  function showJoinError(msg) {
    if (els.roomJoinError) { els.roomJoinError.textContent = msg; els.roomJoinError.classList.remove('hidden'); }
  }

  function startRoomMode() {
    fetchRoomMembers();
    fetchAvatarState();
    roomPollTimer = setInterval(fetchRoomMembers, A.config.POLL_INTERVAL_ROOM);
    avatarPollTimer = setInterval(fetchAvatarState, A.config.POLL_INTERVAL_AVATAR);
  }

  function fetchRoomMembers() {
    if (!roomId) return;
    api.get('/rooms/' + roomId).then(function(r) {
      if (r.ok && r.data) {
        members = r.data.members || [];
        currentSpotId = r.data.currentSpot;
        renderMemberList();
      }
    });
  }

  function fetchAvatarState() {
    if (!roomId) return;
    api.get('/rooms/' + roomId + '/avatar-state').then(function(r) {
      if (r.ok && r.data) {
        var status = r.data.aiStatus || 'idle';
        var labels = { idle:'就绪', listening:'聆听中', speaking:'讲解中', thinking:'思考中', paused:'已暂停', resuming:'恢复中' };
        if (els.avatarStatusLabel) els.avatarStatusLabel.textContent = labels[status] || status;
        if (els.avatarStatusDot) {
          els.avatarStatusDot.className = (status === 'speaking' || status === 'thinking')
            ? 'size-2 bg-[#E07B3C] rounded-full ai-status-pulse'
            : 'size-2 bg-[#34C759] rounded-full';
        }
      }
    });
  }

  function renderMemberList() {
    if (!els.memberListContainer) return;
    if (members.length === 0) {
      els.memberListContainer.innerHTML = comp.emptyState('group', '暂无成员', '等待他人加入...');
      return;
    }
    var html = '';
    members.forEach(function(m) {
      var initial = (m.userName || '?').charAt(0).toUpperCase();
      var isSelf = m.userId === state.get('userId');
      html += '<div class="flex items-center gap-3 p-3 border border-brand-border rounded-xl bg-white">' +
        '<div class="size-10 rounded-full border border-brand-border bg-surface-container flex items-center justify-center text-on-surface-variant font-bold text-sm">' + ui.escapeHtml(initial) + '</div>' +
        '<div><div class="text-sm font-medium font-body-md">' + ui.escapeHtml(m.userName || '游客') + (isSelf ? ' <span class="text-on-surface-variant font-normal">(你)</span>' : '') + '</div></div>' +
        '</div>';
    });
    els.memberListContainer.innerHTML = html;
  }

  // === Function Menu Handlers ===
  function handleFunction(type) {
    els.functionOverlay.classList.add('hidden');
    if (!roomId) { ui.toast('请先加入房间', 'warning'); return; }

    if (type === 'knowledge') {
      showResultPanel('知识库', '<div class="flex items-center justify-center py-8"><div class="loading-spinner"></div></div>');
      api.get('/spots/' + (currentSpotId || 'bell_tower')).then(function(r) {
        var html = '';
        if (r.ok && r.data) {
          html += '<div class="font-medium mb-3">' + ui.escapeHtml(r.data.spotName || currentSpotId || '景点详情') + '</div>';
          if (r.data.description) html += '<p class="text-[#6F6F6F] mb-4">' + ui.escapeHtml(r.data.description) + '</p>';
          if (r.data.chunks && r.data.chunks.length) {
            r.data.chunks.forEach(function(c) {
              html += '<div class="border border-brand-border rounded-lg p-3 mb-2"><div class="font-medium text-xs text-brand-accent mb-1">' + ui.escapeHtml(c.topic || '知识点') + '</div><p class="text-xs text-[#6F6F6F]">' + ui.escapeHtml((c.content || '').substring(0, 200)) + '</p></div>';
            });
          } else {
            html += '<p class="text-xs text-[#A0A0A0]">暂无知识点数据</p>';
          }
        } else {
          html += '<p class="text-xs text-[#F87171]">加载失败</p>';
        }
        if (els.fnResultBody) els.fnResultBody.innerHTML = html;
      });
    }

    if (type === 'audio') {
      showResultPanel('音频导览', '<div class="flex items-center justify-center py-8"><div class="loading-spinner"></div></div>');
      api.post('/audio/tts', { text: '欢迎来到' + (currentSpotId || '当前景点') + '，这里是景区最具代表性的打卡点。', voice: 'guide_female', speed: 1.0, audioFormat: 'mp3' }).then(function(r) {
        var html = '<p class="text-sm mb-4">当前景点语音讲解</p>';
        if (r.ok && r.data && r.data.audioUrl) {
          html += '<audio controls autoplay class="w-full mb-4"><source src="' + A.config.API_BASE.replace('/api','') + ui.escapeHtml(r.data.audioUrl) + '" type="audio/mpeg"></audio>';
          html += '<p class="text-xs text-[#A0A0A0]">时长: ' + (r.data.duration || 0).toFixed(1) + '秒</p>';
        } else {
          html += '<p class="text-xs text-[#A0A0A0]">语音生成中，请稍后再试</p>';
        }
        if (els.fnResultBody) els.fnResultBody.innerHTML = html;
      });
    }

    if (type === 'map') {
      showResultPanel('附近景点', '<div class="flex items-center justify-center py-8"><div class="loading-spinner"></div></div>');
      var spotId = currentSpotId || 'bell_tower';
      api.get('/spots/' + spotId + '/nearby').then(function(r) {
        var html = '<p class="text-sm mb-3">附近景点列表</p>';
        if (r.ok && r.data && r.data.nearby && r.data.nearby.length) {
          r.data.nearby.forEach(function(s) {
            html += '<div class="flex items-center gap-2 border border-brand-border rounded-lg p-3 mb-2"><span class="material-symbols-outlined text-brand-accent text-[18px]">location_on</span><span class="text-sm">' + ui.escapeHtml(s.spotName || s.spotId) + '</span></div>';
          });
        } else {
          html += '<p class="text-xs text-[#A0A0A0]">附近暂无其他景点</p>';
        }
        if (els.fnResultBody) els.fnResultBody.innerHTML = html;
      });
    }

    if (type === 'assistant') {
      router.withParams('ai-assistant', { roomId: roomId });
    }
  }

  function showResultPanel(title, content) {
    if (els.fnResultTitle) els.fnResultTitle.textContent = title;
    if (els.fnResultBody) els.fnResultBody.innerHTML = content;
    if (els.fnResultModal) els.fnResultModal.classList.remove('hidden');
  }

  // Boot
  if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', init); }
  else { init(); }
})();
