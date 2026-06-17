/**
 * Guide Panel — Tour Leader Control Console
 */
(function () {
  'use strict';
  var A = window.Aurelian, state = A.state, api = A.api, ui = A.ui, router = A.router, comp = A.components;

  // State
  var roomId = null;
  var roomPollTimer = null;
  var avatarPollTimer = null;
  var routes = [];
  var selectedRouteId = null;
  var selectedSpotId = null;
  var currentSpotId = null;
  var isPaused = false;
  var members = [];

  // DOM
  var els = {};

  function init() {
    A.auth.guardRole('tour_leader', function(){
      cacheDom(); bindEvents(); loadRoutes();
    });
  }

  function cacheDom() {
    var ids = ['roomIdDisplay','routeNameDisplay','memberCount','memberStatusDot','currentSpotDisplay',
      'scenicAreaDisplay','progressDisplay','pendingRequestsRow','pendingRequestsText',
      'btnStart','btnSkip','btnCollect','btnPause','btnCopyRoom','btnShare','btnViewRequests',
      'btnViewRequests2','requestsBadge','spotSelectorBtn','spotSelectorLabel','spotDropdown',
      'memberList','memberListTitle','tabAll','tabRequests',
      'routeModal','routeList','routeCancel','routeConfirm'];
    ids.forEach(function(id) {
      var camel = id.replace(/-([a-z])/g, function(m,c){ return c.toUpperCase(); });
      els[camel] = document.getElementById(id);
    });
  }

  function bindEvents() {
    if (els.btnStart) els.btnStart.addEventListener('click', handleStart);
    if (els.btnSkip) els.btnSkip.addEventListener('click', handleSkip);
    if (els.btnCollect) els.btnCollect.addEventListener('click', handleCollect);
    if (els.btnPause) els.btnPause.addEventListener('click', handlePause);
    if (els.btnCopyRoom) els.btnCopyRoom.addEventListener('click', handleCopyRoom);
    if (els.btnShare) els.btnShare.addEventListener('click', handleShare);
    if (els.spotSelectorBtn) els.spotSelectorBtn.addEventListener('click', toggleSpotDropdown);
    if (els.routeCancel) els.routeCancel.addEventListener('click', closeRouteModal);
    if (els.routeConfirm) els.routeConfirm.addEventListener('click', confirmCreateRoom);
    if (els.tabAll) els.tabAll.addEventListener('click', function(){ renderMemberList('all'); });
    if (els.tabRequests) els.tabRequests.addEventListener('click', function(){ renderMemberList('requests'); });
    if (els.btnViewRequests) els.btnViewRequests.addEventListener('click', showRequestsModal);
    if (els.btnViewRequests2) els.btnViewRequests2.addEventListener('click', showRequestsModal);
    // Close dropdown on outside click
    document.addEventListener('click', function(e) {
      if (els.spotDropdown && els.spotSelectorBtn && !els.spotSelectorBtn.contains(e.target) && !els.spotDropdown.contains(e.target)) {
        els.spotDropdown.classList.add('hidden');
      }
    });
  }

  // === Route Loading ===
  function loadRoutes() {
    api.get('/routes').then(function(r) {
      if (r.ok && r.data && r.data.routes) {
        routes = r.data.routes;
        if (routes.length > 0) selectedRouteId = routes[0].routeId;
        renderSpotDropdown();
      }
    });
  }

  function renderSpotDropdown() {
    if (!els.spotDropdown) return;
    // Build spot list from selected route's spots
    var route = getSelectedRoute();
    if (!route || !route.spotIds) { els.spotDropdown.innerHTML = '<div class="p-3 text-sm text-[#A0A0A0]">暂无景点数据</div>'; return; }
    var html = '';
    route.spotIds.forEach(function(sid) {
      html += '<button class="spot-option w-full text-left px-4 py-2.5 text-sm hover:bg-[#FAFAF7] transition-colors border-b border-[#F0F0ED] last:border-b-0" data-spot-id="' + ui.escapeHtml(sid) + '">' + ui.escapeHtml(sid) + '</button>';
    });
    els.spotDropdown.innerHTML = html;
    els.spotDropdown.querySelectorAll('.spot-option').forEach(function(btn) {
      btn.addEventListener('click', function() {
        selectedSpotId = btn.getAttribute('data-spot-id');
        if (els.spotSelectorLabel) els.spotSelectorLabel.textContent = selectedSpotId;
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
      token: state.get('token'),
      roomName: state.get('userName') + '的导览团',
      scenicAreaId: 'huangshan',
      routeId: selectedRouteId
    }).then(function(r) {
      if (r.ok && r.data) {
        roomId = r.data.roomId;
        state.set('roomId', roomId);
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
      if (els.btnPause) els.btnPause.innerHTML = '<span class="material-symbols-outlined">pause</span> 暂停讲解';
      ui.toast('讲解已继续', 'info');
    } else {
      if (selectedSpotId) updateCurrentSpot(selectedSpotId);
      ui.toast('讲解已开始', 'success');
    }
  }

  function handleSkip() {
    if (!roomId) { ui.toast('请先创建房间', 'warning'); return; }
    // Find next spot in route
    var route = getSelectedRoute();
    if (!route) return;
    var idx = route.spotIds.indexOf(currentSpotId);
    var nextSpot = idx >= 0 && idx < route.spotIds.length - 1 ? route.spotIds[idx + 1] : route.spotIds[0];
    updateCurrentSpot(nextSpot);
  }

  function handleCollect() {
    if (!roomId) { ui.toast('请先创建房间', 'warning'); return; }
    // Broadcast collect reminder to the room
    api.post('/ai/public-question', {
      roomId: roomId,
      userId: state.get('userId'),
      question: '【集合提醒】请各位游客注意，即将在当前位置集合，跟随团长继续游览。',
      needAudio: false
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
        ? '<span class="material-symbols-outlined">play_arrow</span> 继续讲解'
        : '<span class="material-symbols-outlined">pause</span> 暂停讲解';
    }
    // Attempt to update room status
    if (isPaused) {
      api.post('/rooms/' + roomId + '/current-spot', { spotId: currentSpotId || 'paused' }).then(function(){});
    }
    ui.toast(isPaused ? '讲解已暂停 · AI 将停止播报' : '讲解已继续 · AI 将恢复播报', 'info');
  }

  function updateCurrentSpot(spotId) {
    if (!roomId) return;
    api.post('/rooms/' + roomId + '/current-spot', { spotId: spotId }).then(function(r) {
      if (r.ok) {
        currentSpotId = spotId;
        updateRoomDisplay();
        ui.toast('已切换到: ' + spotId, 'success');
      }
    });
  }

  function handleCopyRoom() {
    if (!roomId) return;
    navigator.clipboard.writeText(roomId).then(function() {
      ui.toast('房间号已复制', 'success');
    }).catch(function() {
      ui.toast('复制失败，房间号: ' + roomId, 'info');
    });
  }

  function handleShare() {
    if (!roomId) { ui.toast('请先创建房间', 'warning'); return; }
    var text = '加入我的智慧导览房间: ' + roomId;
    if (navigator.share) {
      navigator.share({ title: 'Aurelian Guide', text: text }).catch(function(){});
    } else {
      ui.toast('房间号: ' + roomId + ' (已复制)', 'info');
      navigator.clipboard.writeText(roomId).catch(function(){});
    }
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

  // === Polling ===
  function startPolling() {
    if (roomPollTimer) clearInterval(roomPollTimer);
    if (avatarPollTimer) clearInterval(avatarPollTimer);
    fetchRoomStatus();
    fetchAvatarState();
    roomPollTimer = setInterval(fetchRoomStatus, A.config.POLL_INTERVAL_ROOM);
    avatarPollTimer = setInterval(fetchAvatarState, A.config.POLL_INTERVAL_AVATAR);
  }

  function fetchRoomStatus() {
    if (!roomId) return;
    api.get('/rooms/' + roomId).then(function(r) {
      if (r.ok && r.data) {
        members = r.data.members || [];
        currentSpotId = r.data.currentSpot || currentSpotId;
        updateRoomDisplay();
      }
    });
  }

  function fetchAvatarState() {
    if (!roomId) return;
    api.get('/rooms/' + roomId + '/avatar-state').then(function(r) {
      if (r.ok && r.data) {
        var st=r.data.aiStatus||'idle';
        var labels={idle:'待命',listening:'聆听中',speaking:'讲解中',thinking:'思考中',paused:'已暂停',resuming:'续讲中'};
        var colors={idle:'#F5F5F2',listening:'#ECFDF5',speaking:'#FDF6F1',thinking:'#FFFBEB',paused:'#FEF2F2',resuming:'#EFF6FF'};
        var textColors={idle:'#6B7280',listening:'#059669',speaking:'#E07B3C',thinking:'#D97706',paused:'#DC2626',resuming:'#2563EB'};

        // Update AI status badge
        var badge=document.getElementById('ai-status-badge');
        if(badge){badge.textContent=labels[st]||st;badge.style.background=colors[st]||colors.idle;badge.style.color=textColors[st]||textColors.idle;}

        // Update AI action display
        var action=document.getElementById('ai-action-display');
        if(action)action.textContent=r.data.action||r.data.text||(labels[st]||st);

        // Update status dot
        var statusDot = document.getElementById('member-status-dot');
        if (statusDot) {
          if (st === 'speaking'||st==='thinking') statusDot.className = 'w-2 h-2 rounded-full bg-[#E07B3C] animate-pulse';
          else if (st === 'listening') statusDot.className = 'w-2 h-2 rounded-full bg-[#4ADE80] animate-pulse';
          else if (st === 'idle') statusDot.className = 'w-2 h-2 rounded-full bg-[#34C759]';
          else statusDot.className = 'w-2 h-2 rounded-full bg-[#A0A0A0]';
        }
      }
    });
  }

  // === Display Updates ===
  function updateRoomDisplay() {
    if (els.roomIdDisplay) els.roomIdDisplay.textContent = roomId ? roomId.substring(0, 8) : '—';
    var route = getSelectedRoute();
    if (els.routeNameDisplay) els.routeNameDisplay.textContent = route ? route.routeName : '—';
    if (els.memberCount) els.memberCount.textContent = members.length + '人';
    if (els.memberListTitle) els.memberListTitle.textContent = '在线游客 (' + members.length + ')';
    if (els.currentSpotDisplay) els.currentSpotDisplay.textContent = currentSpotId || '—';
    if (els.scenicAreaDisplay) els.scenicAreaDisplay.textContent = '黄山风景区';

    // Progress
    if (route && currentSpotId && els.progressDisplay) {
      var idx = route.spotIds.indexOf(currentSpotId);
      if (idx >= 0) els.progressDisplay.textContent = '第' + (idx + 1) + '段/共' + route.spotIds.length + '段';
      else els.progressDisplay.textContent = '—';
    }

    // Show/hide share/copy buttons
    if (els.btnShare) els.btnShare.style.display = roomId ? '' : 'none';

    // Show/hide pending requests indicator
    var pendingCount = members.filter(function(m){ return m.hasRequest; }).length;
    if (pendingCount > 0 && els.pendingRequestsRow && els.pendingRequestsText) {
      els.pendingRequestsRow.classList.remove('hidden');
      els.pendingRequestsText.textContent = pendingCount + '条私人请求待处理';
      if (els.btnViewRequests) els.btnViewRequests.classList.remove('hidden');
      if (els.requestsBadge) { els.requestsBadge.classList.remove('hidden'); els.requestsBadge.textContent = pendingCount; }
    }

    renderMemberList('all');
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
        '<span class="material-symbols-outlined text-[16px]">person</span></div>' +
        '<span class="text-[14px] text-on-surface font-medium font-label-sm">' + ui.escapeHtml(m.userName || '游客') + (isSelf ? ' <span class="text-xs text-on-surface-variant">(团长)</span>' : '') + '</span></div>';
      if (m.hasRequest) {
        html += '<div class="flex items-center gap-xs"><div class="w-1.5 h-1.5 rounded-full bg-secondary"></div><span class="text-[12px] text-secondary font-medium font-label-sm">有提问</span></div>';
      }
      html += '</li>';
    });
    els.memberList.innerHTML = html;
  }

  // Boot
  if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', init); }
  else { init(); }
})();
