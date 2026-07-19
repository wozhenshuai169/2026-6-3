(function () {
  'use strict';

  var A = window.Aurelian;
  var page = document.getElementById('page-body');
  var main = document.getElementById('journey-main');
  if (!A || !page || !main) return;

  var scenes = ['ask', 'guide', 'team'];
  var labels = { ask: '问导游', guide: '看讲解', team: '聊同行' };
  var currentScene = page.dataset.scene || 'ask';
  var roomId = A.state.get('roomId') || '';
  var currentSpotId = A.state.get('currentSpotId') || '';
  var room = null;
  var conversations = [];
  var activeConversation = 'group';
  var teamMessages = [];
  var pendingMedia = [];
  var knownMessageIds = {};
  var roomPoll = null;
  var socket = null;
  var socketRetry = null;
  var lastNarrationId = '';
  var arrivalHandledFor = '';
  var drawerReturnFocus = null;
  var teamRecorder = null;
  var teamStream = null;
  var teamChunks = [];
  var teamRecordingStartedAt = 0;
  var teamRecordingTimer = null;
  var teamRecordingCancelled = false;
  var guideHoldTimer = null;
  var touchStartX = 0;
  var touchStartY = 0;
  var selectedVoice = A.state.get('narrationVoice') || 'guide_female';

  var els = {
    switchRole: document.getElementById('visitor-switch-role'),
    title: document.getElementById('journey-scene-title'),
    viewport: document.getElementById('journey-viewport'),
    surfaces: Array.prototype.slice.call(document.querySelectorAll('.journey-surface')),
    dock: Array.prototype.slice.call(document.querySelectorAll('[data-scene-target]')),
    spotName: document.getElementById('journey-spot-name'),
    spotStatus: document.getElementById('journey-spot-status'),
    publicArea: document.getElementById('public-chat-area'),
    publicInput: document.getElementById('public-chat-input'),
    publicSend: document.getElementById('public-chat-send'),
    publicVoice: document.getElementById('btn-voice'),
    guidePerson: document.getElementById('guide-person-invoke'),
    guideImage: document.getElementById('guide-person-image'),
    guideStatus: document.getElementById('avatar-status-label'),
    guideText: document.getElementById('narration-text'),
    guideArrivalName: document.getElementById('guide-arrival-name'),
    guideArrivalMeta: document.getElementById('guide-arrival-meta'),
    guideQuestion: document.getElementById('guide-question'),
    tts: document.getElementById('tts-player'),
    teamTitle: document.getElementById('team-chat-title'),
    teamMeta: document.getElementById('team-chat-meta'),
    teamOpen: document.getElementById('team-drawer-open'),
    teamMark: document.getElementById('team-conversation-mark'),
    teamLabel: document.getElementById('team-conversation-label'),
    teamDetail: document.getElementById('team-conversation-detail'),
    teamEmpty: document.getElementById('team-empty-state'),
    teamMessages: document.getElementById('team-message-list'),
    teamComposer: document.getElementById('team-composer'),
    teamInput: document.getElementById('team-message-input'),
    teamSend: document.getElementById('team-message-send'),
    teamVoice: document.getElementById('team-voice-button'),
    teamVoiceCancel: document.getElementById('team-voice-cancel'),
    attachment: document.getElementById('team-attachment-button'),
    drawer: document.getElementById('chat-drawer'),
    drawerBackdrop: document.getElementById('chat-drawer-backdrop'),
    drawerClose: document.getElementById('team-drawer-close'),
    drawerUnjoined: document.getElementById('drawer-unjoined'),
    drawerJoined: document.getElementById('drawer-joined'),
    drawerTeamId: document.getElementById('drawer-team-id'),
    conversationList: document.getElementById('conversation-list'),
    drawerJoin: document.getElementById('chat-join-team'),
    copyRoomId: document.getElementById('copy-team-id'),
    leaveRoom: document.getElementById('leave-team'),
    joinSheet: document.getElementById('room-join-overlay'),
    joinInput: document.getElementById('room-code-input'),
    joinError: document.getElementById('room-join-error'),
    joinButton: document.getElementById('room-join-btn'),
    soloButton: document.getElementById('room-solo-btn'),
    cancelButton: document.getElementById('room-cancel-btn'),
    visitorVoice: document.getElementById('visitor-voice'),
    voiceSelect: document.getElementById('room-voice-select'),
    teamEmptyJoin: document.getElementById('team-empty-join'),
    teamSoloMode: document.getElementById('team-solo-mode')
  };

  function escapeHtml(value) {
    var node = document.createElement('div');
    node.textContent = value == null ? '' : String(value);
    return node.innerHTML;
  }

  function toast(message, type) {
    if (A.ui && A.ui.toast) A.ui.toast(message, type || 'info');
  }

  function fullUrl(path) {
    if (!path || /^https?:/i.test(path)) return path || '';
    return path.charAt(0) === '/' ? path : '/' + path;
  }

  function setScene(next) {
    if (scenes.indexOf(next) === -1 || next === currentScene) return;
    currentScene = next;
    page.dataset.scene = next;
    els.title.textContent = labels[next];
    els.surfaces.forEach(function (surface) {
      surface.classList.toggle('hidden', surface.dataset.scene !== next);
    });
    els.dock.forEach(function (button) {
      button.classList.toggle('is-active', button.dataset.sceneTarget === next);
    });
    if (next === 'team') renderTeamState();
  }

  function appendPublic(role, text, retryText) {
    var article = document.createElement('article');
    article.className = 'journey-public-message ' + role;
    if (role === 'system') {
      article.className += ' system';
      article.textContent = text;
    } else {
      var bubble = document.createElement('div');
      bubble.textContent = text;
      article.appendChild(bubble);
    }
    if (retryText) {
      var retry = document.createElement('button');
      retry.type = 'button'; retry.textContent = '重试';
      retry.addEventListener('click', function () { sendPublicQuestion(retryText); article.remove(); });
      article.appendChild(retry);
    }
    els.publicArea.appendChild(article);
    els.publicArea.scrollTop = els.publicArea.scrollHeight;
  }

  function setPublicLoading(loading) {
    var existing = document.getElementById('public-answer-loading');
    if (existing) existing.remove();
    if (!loading) return;
    var node = document.createElement('article');
    node.id = 'public-answer-loading';
    node.className = 'journey-public-message guide';
    node.textContent = '正在整理讲解…';
    els.publicArea.appendChild(node);
    els.publicArea.scrollTop = els.publicArea.scrollHeight;
  }

  function playAudio(audioUrl) {
    if (!audioUrl || !els.tts) return;
    els.tts.src = fullUrl(audioUrl);
    els.tts.play().catch(function () {
      if (els.guideStatus) els.guideStatus.textContent = '轻触页面后可播放讲解';
    });
  }

  function sendPublicQuestion(forcedText, inputMode) {
    var question = (forcedText || els.publicInput.value || '').trim();
    if (!question) { toast('输入问题后再发送', 'warning'); return; }
    els.publicInput.value = '';
    appendPublic('visitor', question);
    setPublicLoading(true);
    var endpoint = roomId ? '/ai/public-question' : '/ai/solo-question';
    var payload = roomId ? {
      roomId: roomId, userId: A.state.get('userId'), question: question,
      needAudio: true, voice: selectedVoice, inputMode: inputMode || 'text'
    } : {
      userId: A.state.get('userId'), question: question,
      currentSpotId: currentSpotId || 'lingshan_dazhaobi', needAudio: true,
      voice: selectedVoice, inputMode: inputMode || 'text'
    };
    A.api.post(endpoint, payload).then(function (result) {
      setPublicLoading(false);
      if (!result.ok || !result.data) {
        appendPublic('system', (result.error && result.error.message) || '暂时无法回答，请稍后重试。', question);
        return;
      }
      var answer = result.data.answer || result.data.text || '暂时没有找到对应讲解。';
      appendPublic('guide', answer);
      if (els.guideText) els.guideText.textContent = answer;
      playAudio(result.data.audioUrl);
    });
  }

  function beginPublicVoice() {
    var Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) { toast('当前浏览器不支持实时语音识别，请使用文字输入', 'warning'); return; }
    var recognition = new Recognition();
    recognition.lang = 'zh-CN'; recognition.interimResults = false; recognition.continuous = false;
    els.publicVoice.classList.add('is-recording');
    recognition.onresult = function (event) {
      els.publicVoice.classList.remove('is-recording');
      sendPublicQuestion(event.results[0][0].transcript, 'voice');
    };
    recognition.onerror = function () { els.publicVoice.classList.remove('is-recording'); toast('没有听清，请再说一次', 'warning'); };
    recognition.onend = function () { els.publicVoice.classList.remove('is-recording'); };
    try { recognition.start(); toast('请开始说话', 'info'); } catch (_) { els.publicVoice.classList.remove('is-recording'); }
  }

  function recognisePhoto(file) {
    if (!file || !/^image\/(jpeg|png|webp)$/.test(file.type)) { toast('请选择 JPG、PNG 或 WebP 图片', 'warning'); return; }
    var reader = new FileReader();
    reader.onload = function (event) {
      appendPublic('visitor', '请识别这张照片中的景点。');
      setPublicLoading(true);
      A.api.post('/vision/recognize', {
        roomId: roomId || 'solo', userId: A.state.get('userId'), imageUrl: event.target.result,
        currentSpotId: currentSpotId || ''
      }).then(function (result) {
        setPublicLoading(false);
        if (!result.ok || !result.data) { appendPublic('system', '暂时无法识别这张照片，请换一张更清晰的照片。'); return; }
        var spot = result.data.recognizedSpot || {};
        appendPublic('guide', '识别到：' + (spot.spotName || result.data.spotName || '这个景点') + '。' + (result.data.description || '已为你找到相关讲解。'));
      });
    };
    reader.readAsDataURL(file);
  }

  function updateSpot(nextSpot, isArrival) {
    if (!nextSpot) return;
    var changed = currentSpotId && nextSpot !== currentSpotId;
    currentSpotId = nextSpot;
    A.state.set('currentSpotId', nextSpot);
    els.spotName.textContent = nextSpot;
    els.guideArrivalName.textContent = nextSpot;
    els.guideArrivalMeta.textContent = isArrival ? '已到达 · 正在准备讲解' : '当前位置';
    if (changed && isArrival && arrivalHandledFor !== nextSpot) {
      arrivalHandledFor = nextSpot;
      activateGuide('arrival');
    }
  }

  function activateGuide(source) {
    var spot = currentSpotId || '当前景点';
    els.guideStatus.textContent = source === 'arrival' ? '正在自动讲解' : '正在响应你的唤起';
    els.guideText.textContent = '正在准备“' + spot + '”的讲解…';
    A.api.get('/spots/' + encodeURIComponent(spot)).then(function (result) {
      var detail = result.ok && result.data ? (result.data.description || result.data.spotName || '') : '';
      var script = '这里是' + spot + '。' + (detail || '它是这段游览中的重要停留点，值得慢慢看看其中的细节。') + ' 想继续了解故事、建筑特点或下一站路线，都可以问我。';
      els.guideText.textContent = script;
      els.guideStatus.textContent = '正在讲解';
      A.api.post('/audio/tts', { text: script, voice: selectedVoice, speed: 1, audioFormat: 'mp3' }).then(function (audio) {
        if (audio.ok && audio.data) playAudio(audio.data.audioUrl);
      });
    });
  }

  function syncAvatar() {
    if (!roomId) return;
    A.api.get('/rooms/' + encodeURIComponent(roomId) + '/avatar-state').then(function (result) {
      if (!result.ok || !result.data) return;
      var data = result.data;
      if (data.voice && data.voice !== selectedVoice) changeVoice(data.voice, false);
      var labels = { idle: '等待讲解', speaking: '正在讲解', paused: '讲解已暂停', listening: '聆听中', thinking: '正在思考' };
      els.guideStatus.textContent = labels[data.aiStatus] || data.aiStatus || '待命中';
      if (data.text) els.guideText.textContent = data.text;
      if (data.narrationId && data.narrationId !== lastNarrationId) {
        lastNarrationId = data.narrationId;
        playAudio(data.audioUrl);
      }
    });
  }

  function openJoin() {
    closeDrawer();
    els.joinError.classList.add('hidden');
    els.joinSheet.classList.remove('hidden');
    window.setTimeout(function () { els.joinInput.focus(); }, 30);
  }

  function closeJoin() { els.joinSheet.classList.add('hidden'); }

  function joinRoom() {
    var code = (els.joinInput.value || '').trim();
    if (!code) { els.joinError.textContent = '请输入领队分享的同行码'; els.joinError.classList.remove('hidden'); return; }
    els.joinButton.disabled = true; els.joinButton.textContent = '加入中…'; els.joinError.classList.add('hidden');
    A.api.post('/rooms/' + encodeURIComponent(code) + '/join', {}).then(function (result) {
      els.joinButton.disabled = false; els.joinButton.textContent = '加入同行小队';
      if (!result.ok) {
        var error = result.error || {};
        els.joinError.textContent = error.status === 404 ? '同行码不存在，请核对后再试' : (error.message || '暂时无法加入同行小队');
        els.joinError.classList.remove('hidden');
        return;
      }
      roomId = code;
      A.state.set('roomId', roomId);
      A.state.set('narrationVoice', selectedVoice);
      activeConversation = 'group';
      closeJoin();
      toast('已加入同行小队', 'success');
      hydrateRoom(true);
    });
  }

  function enterSoloMode() {
    closeJoin();
    closeDrawer();
    if (roomId) leaveRoom(true);
    else { renderTeamState(); toast('已进入独自导览', 'success'); }
  }

  function leaveRoom(silent) {
    if (!roomId) return;
    var leaving = roomId;
    function finish() {
      disconnectSocket();
      roomId = ''; room = null; conversations = []; teamMessages = []; pendingMedia = []; knownMessageIds = {};
      A.state.remove('roomId'); A.state.remove('routeId');
      renderTeamState();
      if (!silent) toast('已离开同行小队', 'success');
    }
    A.api.delete('/rooms/' + encodeURIComponent(leaving) + '/members/me').then(function (result) {
      if (result.ok) finish();
      else if (!silent) toast((result.error && result.error.message) || '暂时无法离开，请稍后重试', 'warning');
    });
  }

  function hydrateRoom(fromJoin) {
    if (!roomId) { renderTeamState(); return; }
    A.api.get('/rooms/' + encodeURIComponent(roomId)).then(function (result) {
      if (!result.ok || !result.data) {
        if (result.error && (result.error.status === 403 || result.error.status === 404)) {
          disconnectSocket(); roomId = ''; room = null; A.state.remove('roomId'); renderTeamState();
        }
        return;
      }
      room = result.data;
      A.state.set('routeId', room.routeId || '');
      if (room.currentSpot) updateSpot(room.currentSpot, false);
      els.spotStatus.textContent = room.status === 'active' ? '同行中' : '讲解已暂停';
      renderTeamState();
      loadConversations();
      if (fromJoin || !socket) connectSocket();
      syncAvatar();
    });
  }

  function startRoomPolling() {
    if (roomPoll) window.clearInterval(roomPoll);
    roomPoll = window.setInterval(function () { if (roomId) hydrateRoom(false); }, 12000);
  }

  function connectSocket() {
    disconnectSocket();
    if (!roomId) return;
    A.api.post('/auth/ws-ticket', { roomId: roomId }).then(function (ticketResult) {
      if (!ticketResult.ok || !ticketResult.data || !roomId) return;
      var scheme = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      socket = new WebSocket(scheme + '//' + window.location.host + '/ws/rooms/' + encodeURIComponent(roomId) + '?ticket=' + encodeURIComponent(ticketResult.data.ticket));
      socket.onmessage = function (event) { try { handleSocketEvent(JSON.parse(event.data)); } catch (_) {} };
      socket.onclose = function () {
        socket = null;
        if (roomId) socketRetry = window.setTimeout(connectSocket, 3000);
      };
    });
  }

  function disconnectSocket() {
    if (socketRetry) { window.clearTimeout(socketRetry); socketRetry = null; }
    if (socket) { var closing = socket; socket = null; closing.close(); }
  }

  function handleSocketEvent(event) {
    if (!event || !event.type) return;
    if (event.type === 'room.connected') { loadConversations(); return; }
    if (event.type === 'room.members' || event.type === 'room.status') { hydrateRoom(false); return; }
    if (event.type === 'room.spot') { updateSpot((event.data || {}).currentSpot, true); syncAvatar(); return; }
    if (event.type === 'room.narration') { syncAvatar(); return; }
    if (event.type === 'conversation.updated') { loadConversations(); return; }
    if (event.type === 'room.message') {
      if (activeConversation === 'group') receiveTeamMessage(event.data, 'group');
      loadConversations();
      return;
    }
    if (event.type === 'direct.message') {
      var message = event.data || {};
      var peer = message.senderId === A.state.get('userId') ? message.recipientId : message.senderId;
      if (activeConversation === 'direct:' + peer) receiveTeamMessage(message, activeConversation);
      loadConversations();
    }
  }

  function loadConversations(shouldLoadMessages) {
    if (!roomId) { conversations = []; renderTeamState(); return; }
    A.api.get('/rooms/' + encodeURIComponent(roomId) + '/conversations').then(function (result) {
      if (!result.ok || !result.data) return;
      conversations = result.data.conversations || [];
      if (!conversations.some(function (item) { return item.conversationId === activeConversation; })) activeConversation = 'group';
      renderTeamState();
      if (shouldLoadMessages !== false) loadActiveMessages();
    });
  }

  function activeItem() {
    return conversations.find(function (item) { return item.conversationId === activeConversation; }) || null;
  }

  function selectConversation(conversationId) {
    activeConversation = conversationId;
    teamMessages = []; knownMessageIds = {};
    closeDrawer();
    renderTeamState();
    loadActiveMessages();
  }

  function loadActiveMessages() {
    if (!roomId) return;
    var item = activeItem();
    if (!item) return;
    var endpoint = item.kind === 'group'
      ? '/rooms/' + encodeURIComponent(roomId) + '/messages?limit=100'
      : '/rooms/' + encodeURIComponent(roomId) + '/direct/' + encodeURIComponent(item.peerUserId) + '/messages?limit=100';
    A.api.get(endpoint).then(function (result) {
      if (!result.ok || !result.data) return;
      teamMessages = result.data.messages || [];
      knownMessageIds = {};
      teamMessages.forEach(function (message) { knownMessageIds[message.id] = true; });
      renderTeamMessages();
      loadConversations(false);
    });
  }

  function receiveTeamMessage(message, conversationId) {
    if (!message || conversationId !== activeConversation || knownMessageIds[message.id]) return;
    knownMessageIds[message.id] = true;
    teamMessages.push(message);
    renderTeamMessages();
  }

  function formatTime(timestamp) {
    if (!timestamp) return '';
    var date = new Date(timestamp);
    var today = new Date();
    if (date.toDateString() === today.toDateString()) return String(date.getHours()).padStart(2, '0') + ':' + String(date.getMinutes()).padStart(2, '0');
    return (date.getMonth() + 1) + '/' + date.getDate();
  }

  function initial(name) { return (name || '同').slice(0, 1); }

  function renderTeamState() {
    var joined = !!roomId && !!room;
    els.teamEmpty.classList.toggle('hidden', joined);
    els.teamMessages.classList.toggle('hidden', !joined);
    els.teamComposer.classList.toggle('hidden', !joined);
    els.drawerUnjoined.classList.toggle('hidden', joined);
    els.drawerJoined.classList.toggle('hidden', !joined);
    if (!joined) {
      els.teamTitle.textContent = '同行聊天';
      els.teamMeta.textContent = '加入小队后，和同行的人保持联系';
      els.teamLabel.textContent = '加入同行小队';
      els.teamDetail.textContent = '群聊、私信和同行码都在这里';
      els.teamMark.textContent = '聊';
      return;
    }
    var item = activeItem() || conversations[0];
    if (!item) return;
    els.drawerTeamId.textContent = roomId;
    els.teamTitle.textContent = item.title;
    els.teamMeta.textContent = item.kind === 'group'
      ? (room.members.length + ' 人同行 · 领队 ' + ((room.members.find(function (member) { return member.userId === room.leaderId; }) || {}).userName || ''))
      : ((item.isLeader ? '领队' : '同行游客') + ' · 私信');
    els.teamLabel.textContent = item.title;
    els.teamDetail.textContent = item.kind === 'group' ? '群聊 · 查看成员和私信' : (item.isLeader ? '领队私信' : '同行游客私信');
    els.teamMark.textContent = initial(item.title);
    els.teamInput.placeholder = item.kind === 'group' ? '发消息给同行的人' : '发消息给' + item.title;
    renderConversationList();
    renderTeamMessages();
  }

  function renderConversationList() {
    els.conversationList.innerHTML = '';
    conversations.forEach(function (item) {
      var button = document.createElement('button');
      button.type = 'button';
      button.className = item.conversationId === activeConversation ? 'is-active' : '';
      button.innerHTML = '<span class="conversation-mark">' + escapeHtml(initial(item.title)) + '</span><span><strong>' + escapeHtml(item.title) + '</strong><small>' + escapeHtml(item.latestMessage || '暂无消息') + '</small></span><span class="conversation-side"><time>' + escapeHtml(formatTime(item.latestAt)) + '</time>' + (item.unreadCount ? '<b>' + Math.min(item.unreadCount, 99) + '</b>' : '') + '</span>';
      button.addEventListener('click', function () { selectConversation(item.conversationId); });
      els.conversationList.appendChild(button);
    });
  }

  function mediaMarkup(message) {
    var url = escapeHtml(fullUrl(message.mediaUrl));
    if (message.kind === 'image') return '<img class="team-image" src="' + url + '" alt="聊天图片">';
    if (message.kind === 'audio') return '<audio controls preload="metadata" src="' + url + '"></audio><small class="team-audio-duration">' + Math.max(1, Math.round(message.duration || 0)) + ' 秒</small>';
    return escapeHtml(message.content);
  }

  function renderTeamMessages() {
    if (!roomId || !room || !els.teamMessages) return;
    var self = A.state.get('userId');
    var html = '';
    teamMessages.forEach(function (message) {
      if (message.type === 'system') { html += '<p class="team-time">' + escapeHtml(message.content) + '</p>'; return; }
      var isSelf = (message.userId || message.senderId) === self;
      var name = message.userName || message.senderName || '同行游客';
      var leader = (message.userId || message.senderId) === room.leaderId;
      html += '<article class="team-message' + (isSelf ? ' is-self' : '') + '">' + (isSelf ? '' : '<span class="member-initial">' + escapeHtml(initial(name)) + '</span>') + '<div><small>' + escapeHtml(isSelf ? '我' : name) + (leader ? ' <em>领队</em>' : '') + '</small><p>' + mediaMarkup(message) + '</p></div>' + (isSelf ? '<span class="member-initial">我</span>' : '') + '</article>';
    });
    pendingMedia.forEach(function (item) {
      html += '<article class="team-message is-self pending"><div><small>我 · ' + (item.status === 'failed' ? '发送失败' : '发送中…') + '</small><p>' + (item.kind === 'image' ? '<img class="team-image" src="' + escapeHtml(item.preview) + '" alt="待发送图片">' : '<span class="material-icons">graphic_eq</span> 语音 ' + Math.max(1, Math.round(item.duration || 0)) + ' 秒') + (item.status === 'failed' ? '<button type="button" data-retry-media="' + item.id + '">重试</button>' : '') + '</p></div><span class="member-initial">我</span></article>';
    });
    if (!html) html = '<div class="team-empty-message">还没有消息，发一句话开始聊天吧。</div>';
    els.teamMessages.innerHTML = html;
    Array.prototype.slice.call(els.teamMessages.querySelectorAll('[data-retry-media]')).forEach(function (button) {
      button.addEventListener('click', function () {
        var item = pendingMedia.find(function (entry) { return entry.id === button.dataset.retryMedia; });
        if (item) uploadAndSendMedia(item);
      });
    });
    els.teamMessages.scrollTop = els.teamMessages.scrollHeight;
  }

  function sendTextMessage() {
    var content = (els.teamInput.value || '').trim();
    var item = activeItem();
    if (!content || !roomId || !item) { if (!content) toast('输入内容后再发送', 'warning'); return; }
    els.teamSend.disabled = true;
    var endpoint = item.kind === 'group'
      ? '/rooms/' + encodeURIComponent(roomId) + '/messages'
      : '/rooms/' + encodeURIComponent(roomId) + '/direct/' + encodeURIComponent(item.peerUserId) + '/messages';
    var payload = item.kind === 'group' ? { content: content, type: 'user' } : { content: content };
    A.api.post(endpoint, payload).then(function (result) {
      els.teamSend.disabled = false;
      if (!result.ok || !result.data) { toast((result.error && result.error.message) || '发送失败，请重试', 'warning'); return; }
      els.teamInput.value = '';
      receiveTeamMessage(result.data, activeConversation);
      loadConversations();
    });
  }

  function addPendingMedia(file, kind, duration) {
    var item = { id: 'pending-' + Date.now() + '-' + Math.random(), file: file, kind: kind, duration: duration || 0, status: 'uploading', preview: kind === 'image' ? URL.createObjectURL(file) : '' };
    pendingMedia.push(item);
    renderTeamMessages();
    uploadAndSendMedia(item);
  }

  function uploadAndSendMedia(item) {
    var conversation = activeItem();
    if (!conversation || !roomId) return;
    item.status = 'uploading'; renderTeamMessages();
    var form = new FormData(); form.append('file', item.file, item.file.name || (item.kind === 'audio' ? 'voice.webm' : 'image.png'));
    A.api.upload('/rooms/' + encodeURIComponent(roomId) + '/chat-media', form).then(function (upload) {
      if (!upload.ok || !upload.data) throw new Error((upload.error && upload.error.message) || '上传失败');
      var endpoint = conversation.kind === 'group'
        ? '/rooms/' + encodeURIComponent(roomId) + '/messages'
        : '/rooms/' + encodeURIComponent(roomId) + '/direct/' + encodeURIComponent(conversation.peerUserId) + '/messages';
      var payload = { content: '', kind: item.kind, mediaUrl: upload.data.mediaUrl, fileName: upload.data.fileName, duration: item.duration || upload.data.duration || 0 };
      if (conversation.kind === 'group') payload.type = 'user';
      return A.api.post(endpoint, payload);
    }).then(function (sent) {
      if (!sent || !sent.ok || !sent.data) throw new Error((sent && sent.error && sent.error.message) || '发送失败');
      pendingMedia = pendingMedia.filter(function (entry) { return entry.id !== item.id; });
      if (item.preview) URL.revokeObjectURL(item.preview);
      receiveTeamMessage(sent.data, activeConversation);
      loadConversations(); renderTeamMessages();
    }).catch(function () {
      item.status = 'failed'; renderTeamMessages(); toast('发送失败，点击消息内“重试”即可继续', 'warning');
    });
  }

  function beginTeamVoice() {
    if (teamRecorder && teamRecorder.state === 'recording') { finishTeamVoice(false); return; }
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia || !window.MediaRecorder) { toast('当前浏览器不支持录制语音消息', 'warning'); return; }
    navigator.mediaDevices.getUserMedia({ audio: true }).then(function (stream) {
      teamStream = stream; teamChunks = []; teamRecordingCancelled = false;
      teamRecorder = new MediaRecorder(stream);
      teamRecorder.ondataavailable = function (event) { if (event.data.size) teamChunks.push(event.data); };
      teamRecorder.onstop = function () {
        if (teamStream) teamStream.getTracks().forEach(function (track) { track.stop(); });
        var elapsed = (Date.now() - teamRecordingStartedAt) / 1000;
        setTeamRecordingUi(false);
        if (teamRecordingCancelled || elapsed < 0.4) { if (!teamRecordingCancelled) toast('语音太短，未发送', 'warning'); return; }
        addPendingMedia(new File([new Blob(teamChunks, { type: teamRecorder.mimeType || 'audio/webm' })], 'voice.webm', { type: teamRecorder.mimeType || 'audio/webm' }), 'audio', elapsed);
      };
      teamRecordingStartedAt = Date.now(); teamRecorder.start(); setTeamRecordingUi(true);
    }).catch(function () { toast('无法访问麦克风，请检查浏览器权限', 'warning'); });
  }

  function setTeamRecordingUi(recording) {
    if (teamRecordingTimer) { window.clearInterval(teamRecordingTimer); teamRecordingTimer = null; }
    els.teamVoice.querySelector('.material-icons').textContent = recording ? 'stop_circle' : 'graphic_eq';
    els.teamVoice.setAttribute('aria-label', recording ? '结束并发送录音' : '录制语音消息');
    els.teamVoiceCancel.classList.toggle('hidden', !recording);
    els.teamInput.disabled = recording;
    if (recording) {
      els.teamInput.placeholder = '正在录音 0:00 · 再点一次发送';
      teamRecordingTimer = window.setInterval(function () {
        var seconds = Math.floor((Date.now() - teamRecordingStartedAt) / 1000);
        els.teamInput.placeholder = '正在录音 ' + Math.floor(seconds / 60) + ':' + String(seconds % 60).padStart(2, '0') + ' · 再点一次发送';
      }, 500);
    } else { els.teamInput.placeholder = activeItem() && activeItem().kind === 'group' ? '发消息给同行的人' : '输入消息'; }
  }

  function finishTeamVoice(cancelled) {
    teamRecordingCancelled = cancelled;
    if (teamRecorder && teamRecorder.state === 'recording') teamRecorder.stop();
  }

  function openDrawer(opener) {
    drawerReturnFocus = opener || document.activeElement;
    if (!roomId || !room) hydrateRoom(false);
    els.drawerBackdrop.classList.remove('hidden');
    page.classList.add('chat-drawer-open'); els.drawer.classList.add('is-open');
    els.drawer.setAttribute('aria-hidden', 'false'); main.setAttribute('aria-hidden', 'true');
    if ('inert' in main) main.inert = true;
    window.setTimeout(function () { els.drawerClose.focus(); }, 40);
  }

  function closeDrawer() {
    page.classList.remove('chat-drawer-open'); els.drawer.classList.remove('is-open'); els.drawer.setAttribute('aria-hidden', 'true');
    main.removeAttribute('aria-hidden'); if ('inert' in main) main.inert = false;
    window.setTimeout(function () { if (!page.classList.contains('chat-drawer-open')) els.drawerBackdrop.classList.add('hidden'); }, 220);
    if (drawerReturnFocus && drawerReturnFocus.focus) drawerReturnFocus.focus();
  }

  function copyRoomId() {
    if (!roomId) return;
    var done = function () { toast('同行码已复制', 'success'); };
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(roomId).then(done).catch(function () { toast('复制失败，请手动长按选择', 'warning'); });
    else { var helper = document.createElement('textarea'); helper.value = roomId; document.body.appendChild(helper); helper.select(); document.execCommand('copy'); helper.remove(); done(); }
  }

  function initEvents() {
    els.switchRole.addEventListener('click', function () {
      els.switchRole.disabled = true;
      A.auth.logout();
    });
    els.dock.forEach(function (button) { button.addEventListener('click', function () { setScene(button.dataset.sceneTarget); }); });
    els.viewport.addEventListener('touchstart', function (event) { var touch = event.changedTouches[0]; touchStartX = touch.clientX; touchStartY = touch.clientY; }, { passive: true });
    els.viewport.addEventListener('touchend', function (event) { var touch = event.changedTouches[0]; var dx = touch.clientX - touchStartX; var dy = touch.clientY - touchStartY; if (Math.abs(dx) < 52 || Math.abs(dx) < Math.abs(dy) * 1.25) return; var index = scenes.indexOf(currentScene); setScene(scenes[Math.max(0, Math.min(scenes.length - 1, index + (dx < 0 ? 1 : -1)))]); }, { passive: true });
    els.publicSend.addEventListener('click', function () { sendPublicQuestion(); });
    els.publicInput.addEventListener('keydown', function (event) { if (event.key === 'Enter') { event.preventDefault(); sendPublicQuestion(); } });
    els.publicVoice.addEventListener('click', beginPublicVoice);
    var photoInput = document.createElement('input'); photoInput.type = 'file'; photoInput.accept = 'image/jpeg,image/png,image/webp'; photoInput.hidden = true; document.body.appendChild(photoInput);
    photoInput.addEventListener('change', function () { recognisePhoto(photoInput.files[0]); photoInput.value = ''; });
    document.querySelector('[data-tool="vision"]').addEventListener('click', function () { photoInput.click(); });
    document.querySelector('[data-tool="route"]').addEventListener('click', function () { els.publicInput.value = '请按我当前的位置规划一条适合继续游览的路线'; els.publicInput.focus(); });
    els.guideQuestion.addEventListener('click', function () { setScene('ask'); els.publicInput.focus(); });
    ['pointerdown', 'touchstart'].forEach(function (eventName) { els.guidePerson.addEventListener(eventName, function () { if (guideHoldTimer) window.clearTimeout(guideHoldTimer); guideHoldTimer = window.setTimeout(function () { guideHoldTimer = null; activateGuide('visitor'); }, 620); }, { passive: true }); });
    ['pointerup', 'pointerleave', 'touchend', 'touchcancel'].forEach(function (eventName) { els.guidePerson.addEventListener(eventName, function () { if (guideHoldTimer) { window.clearTimeout(guideHoldTimer); guideHoldTimer = null; } }, { passive: true }); });
    els.guidePerson.addEventListener('keydown', function (event) { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); activateGuide('visitor'); } });
    els.teamOpen.addEventListener('click', function () { openDrawer(els.teamOpen); });
    els.drawerClose.addEventListener('click', closeDrawer); els.drawerBackdrop.addEventListener('click', closeDrawer);
    els.drawerJoin.addEventListener('click', openJoin); els.teamEmptyJoin.addEventListener('click', openJoin); els.teamSoloMode.addEventListener('click', enterSoloMode);
    els.joinButton.addEventListener('click', joinRoom); els.joinInput.addEventListener('keydown', function (event) { if (event.key === 'Enter') joinRoom(); }); els.soloButton.addEventListener('click', enterSoloMode); els.cancelButton.addEventListener('click', closeJoin);
    els.voiceSelect.addEventListener('change', function () { changeVoice(els.voiceSelect.value, true); });
    els.visitorVoice.addEventListener('change', function () { changeVoice(els.visitorVoice.value, true); });
    els.copyRoomId.addEventListener('click', copyRoomId); els.leaveRoom.addEventListener('click', function () { if (window.confirm('确定离开当前同行小队吗？')) { closeDrawer(); leaveRoom(false); } });
    els.teamSend.addEventListener('click', sendTextMessage); els.teamInput.addEventListener('keydown', function (event) { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); sendTextMessage(); } });
    var attachmentInput = document.createElement('input'); attachmentInput.type = 'file'; attachmentInput.accept = 'image/jpeg,image/png,image/webp'; attachmentInput.hidden = true; document.body.appendChild(attachmentInput);
    attachmentInput.addEventListener('change', function () { if (attachmentInput.files[0]) addPendingMedia(attachmentInput.files[0], 'image'); attachmentInput.value = ''; });
    els.attachment.addEventListener('click', function () { attachmentInput.click(); }); els.teamVoice.addEventListener('click', beginTeamVoice); els.teamVoiceCancel.addEventListener('click', function () { finishTeamVoice(true); });
    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && page.classList.contains('chat-drawer-open')) closeDrawer();
      if (event.key === 'Tab' && page.classList.contains('chat-drawer-open')) {
        var focusable = Array.prototype.slice.call(els.drawer.querySelectorAll('button:not([disabled]), [tabindex]:not([tabindex="-1"])')); var first = focusable[0]; var last = focusable[focusable.length - 1];
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
      }
    });
  }

  function initialise() {
    selectedVoice = ['guide_female', 'xiaomei', 'guide_male', 'xiaowei'].indexOf(selectedVoice) !== -1 ? selectedVoice : 'guide_female';
    els.voiceSelect.value = selectedVoice;
    els.visitorVoice.value = selectedVoice;
    applyVoiceAvatar(selectedVoice);
    initEvents(); setScene(currentScene); renderTeamState();
    if (A.lipSync && els.tts && els.guideImage) A.lipSync.attach(els.tts, els.guideImage);
    if (roomId) hydrateRoom(false); else { els.spotName.textContent = currentSpotId || '独自导览'; els.guideArrivalName.textContent = currentSpotId || '独自导览'; }
    startRoomPolling();
  }

  function changeVoice(value, notify) {
    var supported = ['guide_female', 'xiaomei', 'guide_male', 'xiaowei'];
    selectedVoice = supported.indexOf(value) !== -1 ? value : 'guide_female';
    A.state.set('narrationVoice', selectedVoice);
    els.voiceSelect.value = selectedVoice;
    els.visitorVoice.value = selectedVoice;
    applyVoiceAvatar(selectedVoice);
    if (notify) toast('讲解音色和数字人形象已切换', 'success');
  }

  function applyVoiceAvatar(voice) {
    if (!A.avatarVoices) return;
    A.avatarVoices.apply(voice, els.guideImage, els.guidePerson);
  }

  A.auth.guard(initialise);
}());
