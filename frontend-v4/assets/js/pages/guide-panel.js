/**
 * Guide Panel — Tour Leader Control Console
 */
(function () {
  'use strict';
  var A = window.Aurelian, state = A.state, api = A.api, ui = A.ui, router = A.router, comp = A.components;
  var SCENIC_AREA_ID = 'lingshan_shengjing';

  // State
  var roomId = null;
  var roomPollTimer = null;
  var avatarPollTimer = null;
  var routes = [];
  var selectedRouteId = null;
  var selectedSpotId = null;
  var currentSpotId = null;
  var isPaused = false;
  var roomEnded = false;
  var members = [];
  var roomRequestPending = false;
  var avatarRequestPending = false;
  var narrationRequestPending = false;
  var guideLipSync = null;
  var roomSocket = null;
  var roomSocketRetry = null;
  var mobilePanelReturnFocus = null;
  var chapterRenderKey = null;

  // DOM
  var els = {};

  function init() {
    A.auth.guardRole('tour_leader', function(){
      cacheDom(); bindEvents(); loadAvatarSettings(); loadRoutes();
    });
    window.addEventListener('pagehide', stopPolling);
    document.addEventListener('visibilitychange', function () {
      if (document.hidden) stopPolling();
      else if (roomId) startPolling();
    });
  }

  function cacheDom() {
    var ids = ['roomIdDisplay','routeNameDisplay','memberCount','memberStatusDot','currentSpotDisplay',
      'scenicAreaDisplay','progressDisplay','pendingRequestsRow','pendingRequestsText',
      'btnStart','btnSkip','btnCollect','btnPause','btnCopyRoom','btnShare','btnViewRequests',
      'btnViewRequests2','btnBack','requestsBadge','spotSelectorBtn','spotSelectorLabel','spotDropdown',
      'btnNotifications','notificationBadge','btnMore','moreActionsMenu',
      'btnMobilePanel','leaderMobileSheet','leaderMobileBackdrop','leaderMobileClose','leaderMobileContent',
      'memberList','memberListTitle','tabAll','tabRequests',
      'routeModal','routeList','routeCancel','routeConfirm','guideNarrationPlayer',
      'guideAudioControls','guideAudioToggle','guideAudioCurrent','guideAudioSeek','guideAudioDuration',
      'narrationVoice','guideAvatarImage','guideAvatarFrame','guideAvatarMouth','guideStage',
      'leaderSyncStatus','leaderSyncLabel','leaderSyncTime','leaderAudienceSummary','chapterTrack'];
    ids.forEach(function(id) {
      var camel = id.replace(/-([a-z])/g, function(m,c){ return c.toUpperCase(); });
      var kebab = id.replace(/([A-Z])/g, '-$1').toLowerCase();
      els[camel] = document.getElementById(id) || document.getElementById(kebab);
    });
    setSyncState('idle', '等待创建同行小队');
  }

  function bindEvents() {
    if (els.btnStart) els.btnStart.addEventListener('click', handleStart);
    if (els.btnSkip) els.btnSkip.addEventListener('click', handleSkip);
    if (els.btnCollect) els.btnCollect.addEventListener('click', handleCollect);
    if (els.btnPause) els.btnPause.addEventListener('click', handlePause);
    if (els.btnCopyRoom) els.btnCopyRoom.addEventListener('click', handleCopyRoom);
    if (els.btnShare) els.btnShare.addEventListener('click', handleShare);
    if (els.btnNotifications) els.btnNotifications.addEventListener('click', showNotificationCenter);
    if (els.btnMore) els.btnMore.addEventListener('click', toggleMoreActions);
    if (els.moreActionsMenu) els.moreActionsMenu.querySelectorAll('[data-more-action]').forEach(function(btn) {
      btn.addEventListener('click', function(){ handleMoreAction(btn.getAttribute('data-more-action')); });
    });
    if (els.btnBack) els.btnBack.addEventListener('click', function(){ router.go('landing'); });
    if (els.btnMobilePanel) els.btnMobilePanel.addEventListener('click', openMobilePanel);
    if (els.leaderMobileClose) els.leaderMobileClose.addEventListener('click', closeMobilePanel);
    if (els.leaderMobileBackdrop) els.leaderMobileBackdrop.addEventListener('click', closeMobilePanel);
    if (els.leaderMobileSheet) els.leaderMobileSheet.querySelectorAll('[data-leader-panel]').forEach(function(btn) {
      btn.addEventListener('click', function(){ renderMobilePanel(btn.getAttribute('data-leader-panel')); });
    });
    document.addEventListener('keydown', function(event) {
      if (event.key === 'Escape' && els.leaderMobileSheet && !els.leaderMobileSheet.classList.contains('hidden')) closeMobilePanel();
    });
    if (els.spotSelectorBtn) els.spotSelectorBtn.addEventListener('click', toggleSpotDropdown);
    if (els.routeCancel) els.routeCancel.addEventListener('click', closeRouteModal);
    if (els.routeConfirm) els.routeConfirm.addEventListener('click', confirmCreateRoom);
    if (els.tabAll) els.tabAll.addEventListener('click', function(){ renderMemberList('all'); });
    if (els.tabRequests) els.tabRequests.addEventListener('click', function(){ renderMemberList('requests'); });
    if (els.btnViewRequests) els.btnViewRequests.addEventListener('click', showRequestsModal);
    if (els.btnViewRequests2) els.btnViewRequests2.addEventListener('click', showRequestsModal);
    if (els.narrationVoice) {
      var savedVoice = state.get('narrationVoice');
      if (savedVoice && els.narrationVoice.querySelector('option[value="' + savedVoice + '"]')) {
        els.narrationVoice.value = savedVoice;
      }
      els.narrationVoice.addEventListener('change', function(){
        state.set('narrationVoice', els.narrationVoice.value);
        ui.toast('讲解音色已切换，下次讲解时生效', 'success');
      });
    }
    bindAudioControls();
    // Close dropdown on outside click
    document.addEventListener('click', function(e) {
      if (els.spotDropdown && els.spotSelectorBtn && !els.spotSelectorBtn.contains(e.target) && !els.spotDropdown.contains(e.target)) {
        els.spotDropdown.classList.add('hidden');
      }
      if (els.moreActionsMenu && els.btnMore && !els.btnMore.contains(e.target) && !els.moreActionsMenu.contains(e.target)) {
        closeMoreActions();
      }
    });
  }

  // === Route Loading ===
  function loadRoutes() {
    api.get('/map/scenic-areas/' + SCENIC_AREA_ID + '/routes').then(function(r) {
      if (r.ok && r.data && r.data.routes) {
        routes = r.data.routes;
        if (routes.length > 0) selectedRouteId = routes[0].routeId;
        renderSpotDropdown();
        updateRoomDisplay();
      }
    });
  }

  function renderSpotDropdown() {
    if (!els.spotDropdown) return;
    // Build spot list from selected route's spots
    var route = getSelectedRoute();
    if (!route || !route.spotIds) { els.spotDropdown.innerHTML = '<div class="p-3 text-sm text-[#A0A0A0]">暂无景点数据</div>'; return; }
    var spotNames = {};
    (route.spots || []).forEach(function(spot){ spotNames[spot.spotId] = spot.name; });
    var html = '';
    route.spotIds.forEach(function(sid) {
      html += '<button class="spot-option w-full text-left px-4 py-2.5 text-sm hover:bg-[#FAFAF7] transition-colors border-b border-[#F0F0ED] last:border-b-0" data-spot-id="' + ui.escapeHtml(sid) + '">' + ui.escapeHtml(spotNames[sid] || sid) + '</button>';
    });
    els.spotDropdown.innerHTML = html;
    els.spotDropdown.querySelectorAll('.spot-option').forEach(function(btn) {
      btn.addEventListener('click', function() {
        selectedSpotId = btn.getAttribute('data-spot-id');
        if (els.spotSelectorLabel) els.spotSelectorLabel.textContent = spotNames[selectedSpotId] || selectedSpotId;
        els.spotDropdown.classList.add('hidden');
        // Update current spot if room exists
        if (roomId) updateCurrentSpot(selectedSpotId);
      });
    });
  }

  function getSelectedRoute() {
    return routes.find(function(r){ return r.routeId === selectedRouteId; });
  }

  // === Room Management ===
  function showRouteModal() {
    if (!els.routeList || !els.routeModal) return;
    var html = '';
    routes.forEach(function(r, i) {
      var checked = i === 0 ? 'border-[#E07B3C] bg-[#FDF6F1]' : 'border-[#E8E8E4]';
      html += '<button class="route-option text-left p-4 border rounded-xl transition-colors ' + checked + '" data-route-id="' + ui.escapeHtml(r.routeId) + '">' +
        '<div class="font-medium text-sm">' + ui.escapeHtml(r.routeName) + '</div>' +
        '<div class="text-xs text-[#A0A0A0] mt-1">约' + r.estimatedTime + '分钟 · ' + ui.escapeHtml(r.difficulty || 'medium') + '</div></button>';
    });
    els.routeList.innerHTML = html;
    els.routeModal.classList.remove('hidden');
    if (routes.length && els.routeConfirm) els.routeConfirm.disabled = false;

    els.routeList.querySelectorAll('.route-option').forEach(function(btn) {
      btn.addEventListener('click', function() {
        els.routeList.querySelectorAll('.route-option').forEach(function(b){ b.className = b.className.replace('border-[#E07B3C] bg-[#FDF6F1]','border-[#E8E8E4]'); });
        btn.className = btn.className.replace('border-[#E8E8E4]','border-[#E07B3C] bg-[#FDF6F1]');
        selectedRouteId = btn.getAttribute('data-route-id');
        if (els.routeConfirm) els.routeConfirm.disabled = false;
      });
    });
  }

  function closeRouteModal() {
    if (els.routeModal) els.routeModal.classList.add('hidden');
  }

  function confirmCreateRoom() {
    if (!selectedRouteId) return;
    if (els.routeConfirm) { els.routeConfirm.disabled = true; els.routeConfirm.innerHTML = '<span class="loading-spinner"></span>创建中...'; }
      api.post('/rooms', {
        roomName: state.get('userName') + '的导览团',
      scenicAreaId: SCENIC_AREA_ID,
      routeId: selectedRouteId
    }).then(function(r) {
      if (r.ok && r.data) {
        roomId = r.data.roomId;
        roomEnded = false;
        state.set('roomId', roomId);
        state.set('routeId', selectedRouteId);
        closeRouteModal();
        ui.toast('房间创建成功！', 'success');
        updateRoomDisplay();
        startPolling();
        renderSpotDropdown();
      } else {
        ui.toast('创建失败: ' + (r.error && r.error.message || '未知错误'), 'error');
        if (els.routeConfirm) { els.routeConfirm.disabled = false; els.routeConfirm.textContent = '确认并创建房间'; }
      }
    });
  }

  function handleStart() {
    if (!roomId) {
      if (routes.length === 0) { ui.toast('路线加载中，请稍候', 'warning'); return; }
      showRouteModal();
      return;
    }
    // Room exists — resume or start
    if (isPaused) {
      isPaused = false;
      if (els.btnPause) els.btnPause.innerHTML = '<span class="material-icons">pause</span> 暂停讲解';
      api.patch('/rooms/' + roomId + '/status', { status: 'active' }).then(function(r) {
        if (r.ok && els.guideNarrationPlayer) {
          els.guideNarrationPlayer.play().catch(function(){
            ui.toast('请点击底部播放器继续播放', 'warning');
          });
        }
      });
      ui.toast('讲解已继续', 'info');
    } else {
      var route = getSelectedRoute();
      var startSpot = selectedSpotId || currentSpotId || (route && route.spotIds && route.spotIds[0]);
      if (!startSpot) { ui.toast('请先选择路线景点', 'warning'); return; }
      beginNarration(startSpot);
    }
  }

  function loadAvatarSettings() {
    api.get('/avatar-settings').then(function(result) {
      if (!result.ok || !result.data) return;
      var imageUrl = result.data.imageUrl || '';
      var hasSpeakingFrame = /digital-avatar-a\.png(?:\?|$)/.test(imageUrl);
      var isHeadOnly = /digital-guide-foreground\.png(?:\?|$)/.test(imageUrl);
      if (els.guideAvatarImage && imageUrl) {
        els.guideAvatarImage.src = imageUrl;
        if (hasSpeakingFrame) els.guideAvatarImage.setAttribute('data-speaking-src', '/assets/images/digital-avatar-a-open.png');
        else els.guideAvatarImage.removeAttribute('data-speaking-src');
      }
      if (els.guideAvatarFrame) els.guideAvatarFrame.setAttribute('data-avatar-role', isHeadOnly ? 'head-only' : (result.data.role || 'xiaoyun'));
      if (guideLipSync) guideLipSync.setEnabled(result.data.lipSync !== false);
      if (!state.get('narrationVoice') && els.narrationVoice) {
        els.narrationVoice.value = result.data.voice || 'guide_female';
      }
    });
  }

  function beginNarration(spotId) {
    if (!roomId || narrationRequestPending) return Promise.resolve(false);
    narrationRequestPending = true;
    if (els.btnStart) {
      els.btnStart.disabled = true;
      els.btnStart.innerHTML = '<span class="loading-spinner"></span> 正在准备讲解...';
    }
    var voice = els.narrationVoice ? els.narrationVoice.value : 'guide_female';
    state.set('narrationVoice', voice);
    return api.post('/rooms/' + roomId + '/narration/start', { spotId: spotId, voice: voice }).then(function(r) {
      if (!r.ok || !r.data) {
        ui.toast('讲解暂时无法准备，请稍后再试', 'error');
        return false;
      }
      selectedSpotId = r.data.spotId;
      currentSpotId = r.data.spotId;
      state.set('currentSpotId', currentSpotId);
      if (els.spotSelectorLabel) els.spotSelectorLabel.textContent = currentSpotId;
      var subtitle = document.querySelector('.guide-stage .subtitle');
      if (subtitle) subtitle.textContent = r.data.text || '';
      updateRoomDisplay();
      playGuideNarration(r.data.audioUrl);
      ui.toast('讲解已准备好并开始播放', 'success');
      return true;
    }).catch(function() {
      ui.toast('讲解服务连接失败，请稍后再试', 'error');
      return false;
    }).finally(function() {
      narrationRequestPending = false;
      if (els.btnStart) {
        els.btnStart.disabled = false;
        els.btnStart.innerHTML = '<span class="material-icons">play_arrow</span> 重新讲解';
      }
    });
  }

  function playGuideNarration(audioUrl) {
    if (!audioUrl || !els.guideNarrationPlayer) return;
    var fullUrl = audioUrl.startsWith('/') ? audioUrl : A.config.API_BASE.replace('/api','') + '/' + audioUrl;
    els.guideNarrationPlayer.src = fullUrl;
    if (els.guideAudioControls) els.guideAudioControls.classList.remove('hidden');
    updateAudioProgress();
    els.guideNarrationPlayer.play().catch(function() {
      ui.toast('讲解音频已准备好，请点击底部播放器开始播放', 'warning');
    });
  }

  function bindAudioControls() {
    if (!els.guideNarrationPlayer) return;
    guideLipSync = A.lipSync.attach(els.guideNarrationPlayer, els.guideAvatarMouth);
    if (els.guideAudioToggle) els.guideAudioToggle.addEventListener('click', handleAudioToggle);
    if (els.guideAudioSeek) els.guideAudioSeek.addEventListener('input', handleAudioSeek);
    els.guideNarrationPlayer.addEventListener('loadedmetadata', updateAudioProgress);
    els.guideNarrationPlayer.addEventListener('durationchange', updateAudioProgress);
    els.guideNarrationPlayer.addEventListener('timeupdate', updateAudioProgress);
    els.guideNarrationPlayer.addEventListener('play', function(){ updateAudioToggle(false); });
    els.guideNarrationPlayer.addEventListener('pause', function(){ updateAudioToggle(true); });
    els.guideNarrationPlayer.addEventListener('ended', function(){
      updateAudioProgress();
      updateAudioToggle(true);
    });
  }

  function handleAudioToggle() {
    if (!els.guideNarrationPlayer || !els.guideNarrationPlayer.src) {
      ui.toast('请先开始讲解', 'warning');
      return;
    }
    if (els.guideNarrationPlayer.ended) els.guideNarrationPlayer.currentTime = 0;
    // 以播放器的真实状态为准，再复用团长端的暂停/继续逻辑。
    isPaused = els.guideNarrationPlayer.paused;
    handlePause();
  }

  function handleAudioSeek(event) {
    if (!els.guideNarrationPlayer) return;
    var duration = els.guideNarrationPlayer.duration;
    var nextTime = Number(event.target.value);
    if (!Number.isFinite(duration) || duration <= 0 || !Number.isFinite(nextTime)) return;
    els.guideNarrationPlayer.currentTime = Math.max(0, Math.min(nextTime, duration));
    updateAudioProgress();
  }

  function updateAudioProgress() {
    if (!els.guideNarrationPlayer) return;
    var duration = Number.isFinite(els.guideNarrationPlayer.duration) ? els.guideNarrationPlayer.duration : 0;
    var current = Number.isFinite(els.guideNarrationPlayer.currentTime) ? els.guideNarrationPlayer.currentTime : 0;
    if (els.guideAudioSeek) {
      els.guideAudioSeek.max = duration || 0;
      els.guideAudioSeek.value = Math.min(current, duration || 0);
      var percent = duration > 0 ? Math.min(100, (current / duration) * 100) : 0;
      els.guideAudioSeek.style.setProperty('--seek-progress', percent + '%');
    }
    if (els.guideAudioCurrent) els.guideAudioCurrent.textContent = formatAudioTime(current);
    if (els.guideAudioDuration) els.guideAudioDuration.textContent = formatAudioTime(duration);
  }

  function updateAudioToggle(paused) {
    if (!els.guideAudioToggle) return;
    var label = paused ? '播放讲解' : '暂停讲解';
    els.guideAudioToggle.setAttribute('aria-label', label);
    els.guideAudioToggle.setAttribute('title', label);
    els.guideAudioToggle.innerHTML = '<span class="material-icons">' + (paused ? 'play_arrow' : 'pause') + '</span>';
  }

  function formatAudioTime(seconds) {
    if (!Number.isFinite(seconds) || seconds < 0) seconds = 0;
    var total = Math.floor(seconds);
    var minutes = Math.floor(total / 60);
    var remainder = total % 60;
    return minutes + ':' + String(remainder).padStart(2, '0');
  }

  function handleSkip() {
    if (!roomId) { ui.toast('请先创建房间', 'warning'); return; }
    // Find next spot in route
    var route = getSelectedRoute();
    if (!route) return;
    var idx = route.spotIds.indexOf(currentSpotId);
    var nextSpot = idx >= 0 && idx < route.spotIds.length - 1 ? route.spotIds[idx + 1] : route.spotIds[0];
    beginNarration(nextSpot);
  }

  function handleCollect() {
    if (!roomId) { ui.toast('请先创建房间', 'warning'); return; }
    api.post('/rooms/' + roomId + '/messages', {
      content: '【集合提醒】请各位游客注意，即将在当前位置集合，跟随团长继续游览。',
      type: 'broadcast'
    }).then(function(r) {
      if (r.ok) ui.toast('集合提醒已发布给所有游客', 'success');
      else ui.toast('集合提醒发布失败', 'error');
    });
  }

  function handlePause() {
    if (!roomId) { ui.toast('请先创建房间', 'warning'); return; }
    isPaused = !isPaused;
    if (els.btnPause) {
      els.btnPause.innerHTML = isPaused
        ? '<span class="material-icons">play_arrow</span> 继续讲解'
        : '<span class="material-icons">pause</span> 暂停讲解';
    }
    if (els.guideNarrationPlayer) {
      if (isPaused) els.guideNarrationPlayer.pause();
      else els.guideNarrationPlayer.play().catch(function(){
        ui.toast('请点击底部播放器继续播放', 'warning');
      });
    }
    api.patch('/rooms/' + roomId + '/status', { status: isPaused ? 'paused' : 'active' }).then(function(){});
    ui.toast(isPaused ? '讲解已暂停' : '讲解已继续播放', 'info');
  }

  function updateCurrentSpot(spotId) {
    if (!roomId) return Promise.resolve(false);
    return api.post('/rooms/' + roomId + '/current-spot', { spotId: spotId }).then(function(r) {
      if (r.ok) {
        selectedSpotId = spotId;
        currentSpotId = spotId;
        state.set('currentSpotId', spotId);
        if (els.spotSelectorLabel) els.spotSelectorLabel.textContent = spotId;
        updateRoomDisplay();
        ui.toast('已切换到: ' + spotId, 'success');
        return true;
      }
      ui.toast((r.error && r.error.message) || '景点更新失败', 'error');
      return false;
    });
  }

  function handleCopyRoom() {
    if (!roomId) return;
    copyText(roomId).then(function() {
      ui.toast('房间号已复制', 'success');
    }).catch(function() {
      ui.toast('浏览器限制自动复制，请手动复制：' + roomId, 'warning');
      try { window.prompt('请手动复制房间号', roomId); } catch (e) {}
    });
  }

  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text);
    }
    return new Promise(function(resolve, reject) {
      var textarea = document.createElement('textarea');
      textarea.value = text;
      textarea.setAttribute('readonly', '');
      textarea.style.position = 'fixed';
      textarea.style.left = '-9999px';
      textarea.style.top = '0';
      textarea.style.opacity = '0';
      document.body.appendChild(textarea);
      textarea.focus();
      textarea.select();
      textarea.setSelectionRange(0, textarea.value.length);
      try {
        var ok = document.execCommand('copy');
        ok ? resolve() : reject(new Error('execCommand copy failed'));
      } catch (e) {
        reject(e);
      } finally {
        document.body.removeChild(textarea);
      }
    });
  }

  function handleShare() {
    if (!roomId) { ui.toast('请先创建房间', 'warning'); return; }
    var text = '加入我的智慧导览房间: ' + roomId;
    if (navigator.share) {
      navigator.share({ title: 'Aurelian Guide', text: text }).catch(function(){});
    } else {
      ui.toast('房间号: ' + roomId + ' (已复制)', 'info');
      copyText(roomId).catch(function(){});
    }
  }

  function toggleMoreActions(e) {
    if (e) e.stopPropagation();
    if (!els.moreActionsMenu) return;
    var willOpen = els.moreActionsMenu.classList.contains('hidden');
    els.moreActionsMenu.classList.toggle('hidden');
    if (els.btnMore) els.btnMore.setAttribute('aria-expanded', willOpen ? 'true' : 'false');
  }

  function closeMoreActions() {
    if (els.moreActionsMenu) els.moreActionsMenu.classList.add('hidden');
    if (els.btnMore) els.btnMore.setAttribute('aria-expanded', 'false');
  }

  function handleMoreAction(action) {
    closeMoreActions();
    if (action === 'copy') {
      if (!roomId) ui.toast('请先创建房间', 'warning');
      else handleCopyRoom();
      return;
    }
    if (action === 'refresh') {
      if (!roomId) { ui.toast('当前还没有导览房间', 'warning'); return; }
      fetchRoomStatus();
      fetchAvatarState();
      ui.toast('房间状态已刷新', 'success');
      return;
    }
    if (action === 'end') handleEndTour();
  }

  function handleEndTour() {
    if (!roomId) { ui.toast('当前还没有导览房间', 'warning'); return; }
    if (!window.confirm('确认结束本次导览吗？结束后该房间不能重新开启。')) return;
    api.patch('/rooms/' + roomId + '/status', { status: 'ended' }).then(function(r) {
      if (!r.ok) {
        ui.toast((r.error && r.error.message) || '结束导览失败', 'error');
        return;
      }
      completeTourDisplay();
      ui.toast('本次导览已结束', 'success');
    });
  }

  function showNotificationCenter() {
    var pending = members.filter(function(m){ return m.hasRequest; });
    var details = '<div style="display:grid;gap:10px">' +
      '<div style="padding:12px;border:1px solid #E8E8E6;border-radius:10px"><div style="font-size:12px;color:#746f68">房间状态</div><div style="font-size:14px;margin-top:4px">' + (roomId ? (isPaused ? '讲解已暂停' : '导览进行中') : '尚未创建房间') + '</div></div>' +
      '<div style="padding:12px;border:1px solid #E8E8E6;border-radius:10px"><div style="font-size:12px;color:#746f68">在线情况</div><div style="font-size:14px;margin-top:4px">' + members.length + ' 人在线 · ' + pending.length + ' 条私人请求</div></div>';
    if (pending.length) {
      pending.forEach(function(m){ details += '<div style="padding:12px;background:#FFF6F2;border-radius:10px;color:#C75E42">' + ui.escapeHtml(m.userName || '游客') + ' 有一条待处理请求</div>'; });
    } else {
      details += '<div style="padding:16px;text-align:center;color:#746f68">暂无新的私人请求</div>';
    }
    details += '</div>';
    showTopbarModal('通知中心', details);
  }

  function showTopbarModal(title, content) {
    var old = document.getElementById('topbar-action-overlay');
    if (old) old.remove();
    var ov = document.createElement('div');
    ov.id = 'topbar-action-overlay';
    ov.style.cssText = 'position:fixed;inset:0;z-index:999;display:flex;align-items:center;justify-content:center;background:rgba(26,26,28,0.2);backdrop-filter:blur(6px)';
    ov.innerHTML = '<div style="background:#fff;border:1px solid #E8E8E6;border-radius:16px;padding:24px;max-width:420px;width:90%;max-height:70vh;overflow-y:auto"><div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:18px"><h3 style="margin:0;font-size:17px">' + ui.escapeHtml(title) + '</h3><button id="topbar-action-close" style="padding:6px 10px;cursor:pointer;border:1px solid #E8E8E6;border-radius:8px;background:#fff">关闭</button></div>' + content + '</div>';
    document.body.appendChild(ov);
    document.getElementById('topbar-action-close').addEventListener('click', function(){ ov.remove(); });
    ov.addEventListener('click', function(e){ if (e.target === ov) ov.remove(); });
  }

  function toggleSpotDropdown() {
    if (!els.spotDropdown) return;
    els.spotDropdown.classList.toggle('hidden');
  }

  function showRequestsModal(){
    var pending = members.filter(function(m){ return m.hasRequest; });
    var content = '';
    if (pending.length === 0) {
      content = '<div class="text-center py-8 text-sm text-on-surface-variant">暂无待处理私人请求</div>';
    } else {
      pending.forEach(function(m){
        content += '<div class="border border-outline rounded-lg p-3 mb-2 flex items-start gap-3"><div class="w-8 h-8 rounded-full bg-error/10 text-error flex items-center justify-center text-xs font-bold">'+(m.userName||'?').charAt(0).toUpperCase()+'</div><div><div class="text-sm font-medium">'+ui.escapeHtml(m.userName||'游客')+'</div><div class="text-xs text-on-surface-variant mt-1">私人请求详情 · 待查看</div></div></div>';
      });
    }
    ui.toast(pending.length+' 条私人请求 · 点击查看详情','info');
    // Inject a simple overlay
    var ov = document.createElement('div');
    ov.id='requests-overlay';
    ov.style.cssText='position:fixed;inset:0;z-index:999;display:flex;align-items:center;justify-content:center;background:rgba(26,26,28,0.2);backdrop-filter:blur(6px)';
    ov.innerHTML='<div style="background:#fff;border:1px solid #E8E8E6;border-radius:16px;padding:24px;max-width:400px;width:90%;max-height:70vh;overflow-y:auto"><div class="flex items-center justify-between mb-4"><h3 style="font-family:\'Source Han Serif\',serif;font-size:16px;font-weight:500">私人请求 ('+pending.length+')</h3><button id="requests-close" style="padding:4px 8px;cursor:pointer;border:1px solid #E8E8E6;border-radius:8px;background:#fff;font-size:12px">关闭</button></div>'+content+'</div>';
    document.body.appendChild(ov);
    document.getElementById('requests-close').addEventListener('click',function(){ov.remove();});
    ov.addEventListener('click',function(e){if(e.target===ov)ov.remove();});
  }

  function setSyncState(status, label) {
    if (!els.leaderSyncStatus) return;
    els.leaderSyncStatus.setAttribute('data-state', status);
    if (els.leaderSyncLabel) els.leaderSyncLabel.textContent = label;
    if (els.leaderSyncTime) els.leaderSyncTime.textContent = status === 'live' ? '刚刚' : '';
  }

  function connectRoomSocket() {
    if (!roomId || roomSocket) return;
    setSyncState('syncing', '正在连接游客端');
    api.post('/auth/ws-ticket', { roomId: roomId }).then(function(r) {
      if (!r.ok || !r.data || !r.data.ticket || !roomId) {
        setSyncState('error', '实时同步暂不可用');
        return;
      }
      var protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
      var socket = new WebSocket(protocol + '//' + location.host + '/ws/rooms/' + encodeURIComponent(roomId) + '?ticket=' + encodeURIComponent(r.data.ticket));
      roomSocket = socket;
      socket.onopen = function() {
        if (roomSocket === socket) setSyncState('live', '已与游客端同步');
      };
      socket.onmessage = function(event) {
        if (roomSocket !== socket) return;
        try { handleRoomSocketEvent(JSON.parse(event.data)); } catch (e) { /* Ignore malformed live events. */ }
      };
      socket.onerror = function() {
        if (roomSocket === socket) setSyncState('error', '实时同步暂不可用');
      };
      socket.onclose = function() {
        if (roomSocket !== socket) return;
        roomSocket = null;
        if (!roomId || document.hidden) return;
        setSyncState('syncing', '正在恢复实时同步');
        clearTimeout(roomSocketRetry);
        roomSocketRetry = setTimeout(connectRoomSocket, 3000);
      };
    }).catch(function() {
      setSyncState('error', '实时同步暂不可用');
    });
  }

  function disconnectRoomSocket() {
    clearTimeout(roomSocketRetry);
    roomSocketRetry = null;
    var socket = roomSocket;
    roomSocket = null;
    if (socket) socket.close();
  }

  function handleRoomSocketEvent(event) {
    var type = event && event.type;
    if (type === 'room.connected') {
      setSyncState('live', '已与游客端同步');
      fetchRoomStatus();
      return;
    }
    if (type === 'room.spot' && event.data) {
      currentSpotId = event.data.spotId || event.data.currentSpot || currentSpotId;
      isPaused = event.data.status === 'paused';
      updateRoomDisplay();
      setSyncState('live', '景点已同步给游客');
      return;
    }
    if (type === 'room.members' || type === 'room.status') {
      if (type === 'room.status' && event.data && event.data.status === 'ended') {
        completeTourDisplay();
        return;
      }
      fetchRoomStatus();
      setSyncState('live', '游客小队已更新');
      return;
    }
    if (type === 'room.narration') {
      fetchAvatarState();
      setSyncState('live', '讲解状态已同步');
      return;
    }
    if (type === 'room.message' || type === 'conversation.updated' || type === 'direct.message') {
      setSyncState('live', '同行互动已更新');
    }
  }

  function completeTourDisplay() {
    roomEnded = true;
    if (els.guideNarrationPlayer) els.guideNarrationPlayer.pause();
    [els.btnStart, els.btnPause, els.btnSkip].forEach(function(btn) { if (btn) btn.disabled = true; });
    setSyncState('idle', '本次导览已结束');
    stopPolling();
  }

  // === Polling (fallback for live synchronization) ===
  function startPolling() {
    if (roomEnded) return;
    if (roomPollTimer) clearInterval(roomPollTimer);
    if (avatarPollTimer) clearInterval(avatarPollTimer);
    connectRoomSocket();
    fetchRoomStatus();
    fetchAvatarState();
    roomPollTimer = setInterval(fetchRoomStatus, A.config.POLL_INTERVAL_ROOM);
    avatarPollTimer = setInterval(fetchAvatarState, A.config.POLL_INTERVAL_AVATAR);
  }

  function stopPolling() {
    if (roomPollTimer) clearInterval(roomPollTimer);
    if (avatarPollTimer) clearInterval(avatarPollTimer);
    roomPollTimer = null;
    avatarPollTimer = null;
    disconnectRoomSocket();
  }

  function fetchRoomStatus() {
    if (!roomId || roomRequestPending) return;
    roomRequestPending = true;
    api.get('/rooms/' + roomId).then(function(r) {
      if (r.ok && r.data) {
        members = r.data.members || [];
        currentSpotId = r.data.currentSpot || currentSpotId;
        isPaused = r.data.status === 'paused';
        updateRoomDisplay();
        if (r.data.status === 'ended') {
          completeTourDisplay();
          return;
        }
        setSyncState(roomSocket ? 'live' : 'syncing', roomSocket ? '已与游客端同步' : '正在连接游客端');
      } else {
        setSyncState('error', '房间状态获取失败');
      }
    }).catch(function(){
      setSyncState('error', '房间状态获取失败');
    }).finally(function(){ roomRequestPending = false; });
  }

  function fetchAvatarState() {
    if (!roomId || avatarRequestPending) return;
    avatarRequestPending = true;
    api.get('/rooms/' + roomId + '/avatar-state').then(function(r) {
      if (r.ok && r.data) {
        var st=r.data.aiStatus||'idle';
        if (els.guideStage && (els.guideNarrationPlayer.paused || st !== 'speaking')) {
          els.guideStage.setAttribute('data-status', st);
        }
        var labels={idle:'待命',listening:'正在听取问题',speaking:'讲解中',thinking:'正在准备',paused:'已暂停',resuming:'继续讲解'};
        var colors={idle:'#F5F5F2',listening:'#ECFDF5',speaking:'#FDF6F1',thinking:'#FFFBEB',paused:'#FEF2F2',resuming:'#EFF6FF'};
        var textColors={idle:'#6B7280',listening:'#059669',speaking:'#E07B3C',thinking:'#D97706',paused:'#DC2626',resuming:'#2563EB'};

        // Update guide status badge
        var badge=document.getElementById('ai-status-badge');
        if(badge){badge.textContent=labels[st]||st;badge.style.background=colors[st]||colors.idle;badge.style.color=textColors[st]||textColors.idle;}

        // Keep internal state names out of the visible status text.
        var action=document.getElementById('ai-action-display');
        if(action)action.textContent=r.data.text||(labels[st]||'等待操作');

        // Update status dot
        var statusDot = document.getElementById('member-status-dot');
        if (statusDot) {
          if (st === 'speaking'||st==='thinking') statusDot.className = 'w-2 h-2 rounded-full bg-[#E07B3C] animate-pulse';
          else if (st === 'listening') statusDot.className = 'w-2 h-2 rounded-full bg-[#4ADE80] animate-pulse';
          else if (st === 'idle') statusDot.className = 'w-2 h-2 rounded-full bg-[#34C759]';
          else statusDot.className = 'w-2 h-2 rounded-full bg-[#A0A0A0]';
        }
      }
    }).finally(function(){ avatarRequestPending = false; });
  }

  // === Display Updates ===
  function updateRoomDisplay() {
    if (els.roomIdDisplay) els.roomIdDisplay.textContent = roomId ? roomId.substring(0, 8) : '—';
    var route = getSelectedRoute();
    if (els.routeNameDisplay) els.routeNameDisplay.textContent = route ? route.routeName : '—';
    if (els.memberCount) els.memberCount.textContent = members.length + '人';
    if (els.memberListTitle) els.memberListTitle.textContent = '在线游客 (' + members.length + ')';
    var spotNames = {};
    if (route && route.spots) route.spots.forEach(function(spot){ spotNames[spot.spotId] = spot.name; });
    if (els.currentSpotDisplay) els.currentSpotDisplay.textContent = spotNames[currentSpotId] || currentSpotId || '—';
    if (els.scenicAreaDisplay) els.scenicAreaDisplay.textContent = '灵山胜境';
    if (els.spotSelectorLabel) els.spotSelectorLabel.textContent = spotNames[currentSpotId] || currentSpotId || '切换景点';
    if (els.leaderAudienceSummary) {
      var visitorCount = members.filter(function(member) { return member.userId !== state.get('userId'); }).length;
      if (!roomId) {
        els.leaderAudienceSummary.textContent = '创建同行小队后，游客端会实时接收景点与讲解';
      } else if (isPaused) {
        els.leaderAudienceSummary.textContent = '小队已暂停，' + visitorCount + ' 位游客会看到暂停状态';
      } else if (currentSpotId) {
        els.leaderAudienceSummary.textContent = '正在同步“' + (spotNames[currentSpotId] || currentSpotId) + '”给 ' + visitorCount + ' 位游客';
      } else {
        els.leaderAudienceSummary.textContent = '选择景点后，游客端会自动更新讲解';
      }
    }

    // Progress
    if (route && currentSpotId && els.progressDisplay) {
      var idx = route.spotIds.indexOf(currentSpotId);
      if (idx >= 0) els.progressDisplay.textContent = '第' + (idx + 1) + '段/共' + route.spotIds.length + '段';
      else els.progressDisplay.textContent = '—';
    } else if (els.progressDisplay) {
      els.progressDisplay.textContent = route && route.spotIds ? '等待开始/共' + route.spotIds.length + '段' : '—';
    }
    renderChapterTrack(route, spotNames);

    // Show/hide share/copy buttons
    if (els.btnShare) els.btnShare.style.display = roomId ? '' : 'none';

    // Show/hide pending requests indicator
    var pendingCount = members.filter(function(m){ return m.hasRequest; }).length;
    if (pendingCount > 0 && els.pendingRequestsRow && els.pendingRequestsText) {
      els.pendingRequestsRow.classList.remove('hidden');
      els.pendingRequestsText.textContent = pendingCount + '条私人请求待处理';
      if (els.btnViewRequests) els.btnViewRequests.classList.remove('hidden');
      if (els.requestsBadge) { els.requestsBadge.classList.remove('hidden'); els.requestsBadge.textContent = pendingCount; }
      if (els.notificationBadge) { els.notificationBadge.classList.remove('hidden'); els.notificationBadge.textContent = pendingCount; }
    } else {
      if (els.pendingRequestsRow) els.pendingRequestsRow.classList.add('hidden');
      if (els.requestsBadge) { els.requestsBadge.classList.add('hidden'); els.requestsBadge.textContent = '0'; }
      if (els.notificationBadge) { els.notificationBadge.classList.add('hidden'); els.notificationBadge.textContent = '0'; }
    }

    renderMemberList('all');
  }

  function renderChapterTrack(route, spotNames) {
    if (!els.chapterTrack || !route || !route.spotIds || !route.spotIds.length) return;
    var activeIndex = route.spotIds.indexOf(currentSpotId);
    var nextKey = (route.routeId || '') + ':' + (currentSpotId || 'waiting');
    if (chapterRenderKey === nextKey) return;
    var html = '';
    route.spotIds.forEach(function(spotId, index) {
      var status = activeIndex < 0 ? 'pending' : (index < activeIndex ? 'done' : (index === activeIndex ? 'active' : 'pending'));
      var statusText = status === 'active' ? '，当前讲解' : (status === 'done' ? '，已完成' : '，待讲解');
      html += '<li class="' + status + '" aria-label="第' + (index + 1) + '段：' + ui.escapeHtml(spotNames[spotId] || spotId) + statusText + '"><b>' + (index + 1) + '</b><span>' + ui.escapeHtml(spotNames[spotId] || spotId) + '</span></li>';
    });
    els.chapterTrack.innerHTML = html;
    els.chapterTrack.setAttribute('data-route-state', nextKey);
    chapterRenderKey = nextKey;
    if (activeIndex >= 0) {
      els.chapterTrack.classList.remove('is-progress-updated');
      void els.chapterTrack.offsetWidth;
      els.chapterTrack.classList.add('is-progress-updated');
    }
  }

  function renderMemberList(filter) {
    if (!els.memberList) return;
    var filtered = filter === 'requests' ? members.filter(function(m){ return m.hasRequest; }) : members;
    if (filtered.length === 0) {
      els.memberList.innerHTML = comp.emptyState('group', filter === 'requests' ? '暂无待处理请求' : '等待游客加入...', '分享房间号邀请游客');
      return;
    }
    var html = '';
    filtered.forEach(function(m) {
      var initial = (m.userName || '?').charAt(0).toUpperCase();
      var isSelf = m.userId === state.get('userId');
      html += '<li class="flex items-center justify-between px-lg py-sm hover:bg-surface-container-low transition-colors">' +
        '<div class="flex items-center gap-md">' +
        '<div class="w-[32px] h-[32px] rounded-full bg-surface-variant flex items-center justify-center text-on-surface-variant">' +
        '<span class="material-icons text-[16px]">person</span></div>' +
        '<span class="text-[14px] text-on-surface font-medium font-label-sm">' + ui.escapeHtml(m.userName || '游客') + (isSelf ? ' <span class="text-xs text-on-surface-variant">(团长)</span>' : '') + '</span></div>';
      if (m.hasRequest) {
        html += '<div class="flex items-center gap-xs"><div class="w-1.5 h-1.5 rounded-full bg-secondary"></div><span class="text-[12px] text-secondary font-medium font-label-sm">有提问</span></div>';
      }
      html += '</li>';
    });
    els.memberList.innerHTML = html;
  }

  function openMobilePanel() {
    if (!els.leaderMobileSheet) return;
    mobilePanelReturnFocus = document.activeElement;
    els.leaderMobileSheet.classList.remove('hidden');
    document.body.classList.add('mobile-sheet-open');
    renderMobilePanel('members');
    if (els.leaderMobileClose) els.leaderMobileClose.focus();
  }

  function closeMobilePanel() {
    if (els.leaderMobileSheet) els.leaderMobileSheet.classList.add('hidden');
    document.body.classList.remove('mobile-sheet-open');
    if (mobilePanelReturnFocus && typeof mobilePanelReturnFocus.focus === 'function') mobilePanelReturnFocus.focus();
    else if (els.btnMobilePanel) els.btnMobilePanel.focus();
    mobilePanelReturnFocus = null;
  }

  function renderMobilePanel(mode) {
    if (!els.leaderMobileContent || !els.leaderMobileSheet) return;
    els.leaderMobileSheet.querySelectorAll('[data-leader-panel]').forEach(function(btn){
      btn.classList.toggle('is-active', btn.getAttribute('data-leader-panel') === mode);
    });
    var route = getSelectedRoute();
    var html = '';
    if (mode === 'members') {
      if (!members.length) html = '<p class="text-center text-sm text-[#91887d] py-6">暂时没有游客加入，分享同行码后会显示在这里。</p>';
      else members.forEach(function(member){
        var name = member.userName || '游客';
        html += '<div class="leader-mobile-row"><span class="leader-mobile-mark">' + ui.escapeHtml(name.charAt(0)) + '</span><span style="flex:1"><strong>' + ui.escapeHtml(name) + '</strong><small>' + (member.hasRequest ? '有待处理的私人请求' : '正在同行') + '</small></span>' + (member.hasRequest ? '<span class="leader-mobile-current">待处理</span>' : '') + '</div>';
      });
    } else if (mode === 'route') {
      if (!route || !route.spotIds || !route.spotIds.length) html = '<p class="text-center text-sm text-[#91887d] py-6">路线加载中，请稍后再试。</p>';
      else route.spotIds.forEach(function(spotId, index){
        var spot = (route.spots || []).find(function(item){ return item.spotId === spotId; }) || {};
        var current = spotId === currentSpotId;
        html += '<button class="leader-mobile-row" type="button" data-mobile-spot="' + ui.escapeHtml(spotId) + '" style="width:100%;border:0;background:transparent;text-align:left"><span class="leader-mobile-mark">' + (index + 1) + '</span><span style="flex:1"><strong>' + ui.escapeHtml(spot.name || spotId) + '</strong><small>' + (current ? '当前讲解位置' : '点击切换到此景点') + '</small></span>' + (current ? '<span class="leader-mobile-current">当前</span>' : '') + '</button>';
      });
    } else if (!roomId) {
      html = '<div class="leader-mobile-actions"><p class="leader-mobile-hint">创建同行小队后，才可同步游客、发集合提醒和管理导览。</p><button type="button" data-mobile-action="start">创建同行小队</button><button type="button" data-mobile-action="back">切换身份</button></div>';
    } else if (roomEnded) {
      html = '<div class="leader-mobile-actions"><p class="leader-mobile-hint">本次导览已经结束。游客端会保留结束提示，不能重新开启。</p><button type="button" data-mobile-action="copy">复制本次同行码</button><button type="button" data-mobile-action="back">切换身份</button></div>';
    } else {
      html = '<div class="leader-mobile-actions"><button type="button" data-mobile-action="pause">' + (isPaused ? '继续讲解' : '暂停讲解') + '</button><button type="button" data-mobile-action="skip">跳至下一景点</button><button type="button" data-mobile-action="collect">发送集合提醒</button><button type="button" data-mobile-action="copy">复制同行码</button><button type="button" data-mobile-action="share">分享同行码</button><button type="button" data-mobile-action="requests">查看私人请求</button><button type="button" data-mobile-action="notifications">查看通知</button><button type="button" data-mobile-action="refresh">刷新成员与讲解状态</button><button type="button" data-mobile-action="end" class="danger">结束本次导览</button><button type="button" data-mobile-action="back">切换身份</button></div>';
    }
    els.leaderMobileContent.innerHTML = html;
    els.leaderMobileContent.querySelectorAll('[data-mobile-spot]').forEach(function(btn){
      btn.addEventListener('click', function(){ updateCurrentSpot(btn.getAttribute('data-mobile-spot')); closeMobilePanel(); });
    });
    els.leaderMobileContent.querySelectorAll('[data-mobile-action]').forEach(function(btn){
      btn.addEventListener('click', function(){
        var action = btn.getAttribute('data-mobile-action');
        if (action === 'start') { closeMobilePanel(); handleStart(); return; }
        if (action === 'copy') handleCopyRoom();
        if (action === 'share') handleShare();
        if (action === 'pause') handlePause();
        if (action === 'skip') handleSkip();
        if (action === 'collect') handleCollect();
        if (action === 'refresh') { fetchRoomStatus(); fetchAvatarState(); ui.toast('状态已刷新', 'success'); }
        if (action === 'requests') { closeMobilePanel(); showRequestsModal(); return; }
        if (action === 'notifications') { closeMobilePanel(); showNotificationCenter(); return; }
        if (action === 'end') { closeMobilePanel(); handleEndTour(); return; }
        if (action === 'back') { closeMobilePanel(); router.go('landing'); return; }
        closeMobilePanel();
      });
    });
  }

  // Boot
  if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', init); }
  else { init(); }
})();
