/**
 * AI Assistant — Private Chat with voice input
 */
(function () {
  'use strict';
  var A = window.Aurelian, state = A.state, api = A.api, ui = A.ui, router = A.router, comp = A.components;

  var roomId, userId;
  var messages = [];
  var isRecording = false;
  var recognition = null;

  var chatContainer, chatInput, btnSend, btnMic, btnBack;

  function init() {
    if (!A.auth.guard()) return;
    roomId = state.get('roomId');
    userId = state.get('userId');
    if (!roomId || !userId) { ui.toast('请先加入房间', 'error'); return; }

    chatContainer = document.getElementById('chat-container');
    chatInput = document.getElementById('chat-input');
    btnSend = document.getElementById('btn-send');
    btnMic = document.getElementById('btn-mic');
    btnBack = document.getElementById('btn-back');

    bindEvents();
    initSpeechRecognition();
    addWelcomeMessage();
    scrollToBottom();
  }

  function bindEvents() {
    if (btnSend) btnSend.addEventListener('click', sendMessage);
    if (btnBack) btnBack.addEventListener('click', function(){ router.go('user-portal'); });
    if (chatInput) chatInput.addEventListener('keydown', function(e){ if (e.key==='Enter') sendMessage(); });
    if (btnMic) btnMic.addEventListener('click', toggleRecording);

    document.querySelectorAll('.quick-btn').forEach(function(btn) {
      btn.addEventListener('click', function() {
        var q = this.getAttribute('data-question');
        if (q) sendMessage(q);
      });
    });

    // Help prompt buttons (delegated)
    if (chatContainer) {
      chatContainer.addEventListener('click', function(e) {
        if (e.target.classList.contains('help-notify')) {
          ui.toast('已通知团长，请稍候', 'success');
          removeHelpCard();
        }
        if (e.target.classList.contains('help-dismiss')) {
          removeHelpCard();
        }
      });
    }
  }

  function addWelcomeMessage() {
    messages.push({ role: 'system', text: '对话开始 · 私人模式' });
    messages.push({ role: 'ai', text: '你好！这里是私人助手模式，你可以随时问我任何问题——找洗手间、推荐轻松路线、或者只是想聊聊天。你问的内容只有我们两个知道 😊' });
    renderMessages();
  }

  function sendMessage(text) {
    text = text || (chatInput ? chatInput.value.trim() : '');
    if (!text) return;
    if (chatInput) chatInput.value = '';

    addMessage('user', text);
    showTyping();

    api.post('/ai/public-question', {
      roomId: roomId,
      userId: userId,
      question: text,
      needAudio: false
    }).then(function(r) {
      removeTyping();
      if (r.ok && r.data) {
        addMessage('ai', r.data.answer || '抱歉，我没有理解你的问题');

        // Check for help keywords
        if (text.indexOf('累')!==-1 || text.indexOf('休息')!==-1 || text.indexOf('不舒服')!==-1 || text.indexOf('走不动')!==-1) {
          addHelpPrompt(text);
        }
      } else {
        var errMsg = (r.error && r.error.message) || '网络连接失败，请确认后端已启动';
        addMessage('system', errMsg);
        ui.toast(errMsg, 'error');
      }
      scrollToBottom();
    });
  }

  function addMessage(role, text) {
    messages.push({ role: role, text: text, time: new Date().toISOString() });
    renderMessages();
  }

  function renderMessages() {
    if (!chatContainer) return;
    var html = '';
    messages.forEach(function(m) {
      if (m.role === 'system') {
        html += '<div class="text-center msg-animate"><span class="text-[12px] text-chat-text-muted bg-white/50 px-3 py-1 rounded-full border border-chat-border/50">' + ui.escapeHtml(m.text) + '</span></div>';
      } else if (m.role === 'ai') {
        html += '<div class="flex flex-col gap-1 items-start w-full msg-animate"><div class="bg-chat-bubble-gray rounded-r-xl rounded-bl-xl p-4 max-w-[80%] text-[15px] leading-[1.6]">' + ui.escapeHtml(m.text) + '</div></div>';
      } else if (m.role === 'user') {
        html += '<div class="flex flex-col gap-1 items-end w-full msg-animate"><div class="bg-white border border-chat-border rounded-l-xl rounded-tr-xl p-4 max-w-[65%] text-[15px] leading-[1.6]">' + ui.escapeHtml(m.text) + '</div></div>';
      } else if (m.role === 'help') {
        html += '<div class="flex flex-col gap-1 items-start w-full msg-animate" id="help-card"><div class="bg-chat-bubble-gray border-l-[3px] border-chat-accent rounded-r-xl rounded-bl-xl p-4 max-w-[85%]"><p class="text-[14px] font-medium mb-3">检测到你可能需要帮助，是否通知团长？</p><div class="flex gap-2 justify-end"><button class="help-dismiss px-4 py-2 text-[13px] bg-transparent border border-chat-border text-chat-text-dark rounded-lg hover:bg-chat-border/50 transition-colors">暂不通知</button><button class="help-notify px-4 py-2 text-[13px] bg-chat-accent text-white rounded-lg hover:opacity-90 transition-opacity">通知团长</button></div></div></div>';
      }
    });
    chatContainer.innerHTML = html;
  }

  function showTyping() {
    var el = document.createElement('div');
    el.id = 'typing-indicator';
    el.className = 'flex mb-1 msg-animate';
    el.innerHTML = '<div class="bg-chat-bubble-gray rounded-r-xl rounded-bl-xl px-4 py-3 border-l-[3px] border-chat-accent"><span class="text-sm text-chat-text-muted">AI 正在思考</span><span class="text-chat-accent">...</span></div>';
    if (chatContainer) chatContainer.appendChild(el);
  }

  function removeTyping() {
    var el = document.getElementById('typing-indicator');
    if (el) el.remove();
  }

  function addHelpPrompt(question) {
    messages.push({ role: 'help', text: question });
    renderMessages();
  }

  function removeHelpCard() {
    var card = document.getElementById('help-card');
    if (card) card.remove();
    messages = messages.filter(function(m){ return m.role !== 'help'; });
  }

  function scrollToBottom() {
    setTimeout(function() {
      if (chatContainer) chatContainer.scrollTop = chatContainer.scrollHeight;
    }, 100);
  }

  // === Voice Input (Web Speech API) ===
  function initSpeechRecognition() {
    var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      if (btnMic) btnMic.style.display = 'none';
      return;
    }
    recognition = new SpeechRecognition();
    recognition.lang = 'zh-CN';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.continuous = false;

    recognition.onresult = function(event) {
      var text = event.results[0][0].transcript;
      if (text) {
        if (chatInput) chatInput.value = text;
        sendMessage(text);
      }
    };
    recognition.onerror = function(event) {
      isRecording = false;
      updateMicButton();
      if (event.error === 'not-allowed') ui.toast('请允许麦克风权限', 'warning');
      else if (event.error !== 'aborted') ui.toast('语音识别出错: ' + event.error, 'error');
    };
    recognition.onend = function() {
      isRecording = false;
      updateMicButton();
    };
  }

  function toggleRecording() {
    if (!recognition) { ui.toast('当前浏览器不支持语音识别，请使用文字输入', 'info'); return; }
    if (isRecording) {
      recognition.stop();
    } else {
      recognition.start();
      isRecording = true;
      updateMicButton();
      ui.toast('正在聆听...', 'info');
    }
  }

  function updateMicButton() {
    if (!btnMic) return;
    if (isRecording) {
      btnMic.style.background = '#FEE2E2';
      btnMic.querySelector('.material-symbols-outlined').textContent = 'mic_off';
      btnMic.querySelector('.material-symbols-outlined').style.color = '#EF4444';
    } else {
      btnMic.style.background = '';
      btnMic.querySelector('.material-symbols-outlined').textContent = 'mic';
      btnMic.querySelector('.material-symbols-outlined').style.color = '';
    }
  }

  // Boot
  if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', init); }
  else { init(); }
})();
