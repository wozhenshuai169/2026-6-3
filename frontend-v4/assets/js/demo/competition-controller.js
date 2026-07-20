(function () {
  'use strict';

  var fixture = window.COMPETITION_FIXTURE;
  var stage = document.getElementById('demo-stage');
  var stepLabel = document.getElementById('demo-step-label');
  var progressBar = document.getElementById('demo-progress-bar');
  var audio = document.getElementById('competition-audio');
  var navButtons = Array.prototype.slice.call(document.querySelectorAll('[data-nav]'));
  var recordingMode = new URLSearchParams(window.location.search).get('record') === '1';
  if (!fixture || !stage) return;

  var runtime = {
    runId: 0,
    stepIndex: -1,
    timers: [],
    playing: false
  };

  function escapeHtml(value) {
    var node = document.createElement('div');
    node.textContent = value == null ? '' : String(value);
    return node.innerHTML;
  }

  function delay(ms) {
    return new Promise(function (resolve) { window.setTimeout(resolve, ms); });
  }

  function later(fn, ms) {
    var timer = window.setTimeout(fn, ms);
    runtime.timers.push(timer);
    return timer;
  }

  function clearTimers() {
    runtime.timers.forEach(window.clearTimeout);
    runtime.timers = [];
  }

  function playProgramAudio(source) {
    if (!source || !audio) return;
    audio.src = source;
    audio.currentTime = 0;
    audio.play().catch(function () {});
  }

  function setNav(name) {
    navButtons.forEach(function (button) {
      button.classList.toggle('active', button.dataset.nav === name);
    });
  }

  function setStepMeta(index) {
    var step = fixture.steps[index];
    runtime.stepIndex = index;
    stepLabel.textContent = step ? step.label : '智能随行导览';
    progressBar.style.width = step ? (((index + 1) / fixture.steps.length) * 100).toFixed(1) + '%' : '0%';
    try { localStorage.setItem('competition-demo-step', String(index)); } catch (_) {}
  }

  function dataChip(label, iconName) {
    return '<span class="demo-data-chip"><span class="material-icons" aria-hidden="true">' +
      escapeHtml(iconName || 'verified') + '</span>' + escapeHtml(label || fixture.badge) + '</span>';
  }

  function sourceBlock(source, detail) {
    return '<div class="source-proof"><span class="material-icons" aria-hidden="true">menu_book</span><div><strong>回答依据</strong><p>' +
      escapeHtml(source) + '</p>' + (detail ? '<small>' + escapeHtml(detail) + '</small>' : '') + '</div></div>';
  }

  function wave() {
    return '<div class="wave" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div>';
  }

  function renderAsk() {
    var qa = fixture.questions.culture;
    setNav('ask');
    stage.innerHTML = '<section class="demo-screen">' +
      '<header class="screen-heading"><div><h1>问导游</h1><p>有依据地回答，也知道何时说不确定</p></div>' + dataChip('知识库已核验') + '</header>' +
      '<div class="place-strip"><span class="material-icons">location_on</span><span>灵山胜境 · 灵山大佛</span><b>独自导览</b></div>' +
      '<div class="chat-scroll"><article class="welcome-card"><span class="material-icons">record_voice_over</span><div><strong>云游讲解</strong><p>文化故事、路线安排和现场服务都可以问我。</p></div></article><div id="typed-question" class="chat-bubble mine typing' + (recordingMode ? ' hidden' : '') + '"></div><div id="answer-slot"></div></div>' +
      '<footer class="ask-composer"><button aria-label="语音输入"><span class="material-icons">mic</span></button><input value="" placeholder="问景点、路线或玩法"' + (recordingMode ? '' : ' readonly') + '><button class="ask-send" aria-label="发送"><span class="material-icons">arrow_upward</span></button></footer>' +
      '</section>';

    var bubble = document.getElementById('typed-question');
    var input = stage.querySelector('.ask-composer input');
    var sendButton = stage.querySelector('.ask-send');
    var position = 0;
    function showAnswer() {
      var slot = document.getElementById('answer-slot');
      if (!slot) return;
      slot.innerHTML = '<article class="answer-card evidence-answer"><header><h2>' + escapeHtml(qa.title) + '</h2><span class="trust-state"><i></i>' + escapeHtml(qa.confidence) + '</span></header><p>' + escapeHtml(qa.answer) + '</p>' + sourceBlock(qa.source, qa.sourceDetail) + '</article>';
    }
    if (recordingMode) {
      input.addEventListener('input', function () {
        bubble.classList.remove('hidden');
        bubble.textContent = input.value;
      });
      sendButton.addEventListener('click', function () {
        if (!input.value.trim()) return;
        bubble.classList.remove('typing');
        input.blur();
        later(showAnswer, 720);
      });
      return;
    }
    function typeNext() {
      if (!bubble || !bubble.isConnected) return;
      position += 1;
      var text = qa.question.slice(0, position);
      bubble.textContent = text;
      input.value = text;
      if (position < qa.question.length) later(typeNext, 46);
      else {
        bubble.classList.remove('typing');
        later(showAnswer, 520);
      }
    }
    later(typeNext, 420);
  }

  function renderVision(sceneName) {
    var vision = fixture.visionScenes[sceneName];
    setNav('ask');
    var features = vision.features.map(function (feature) { return '<span>' + escapeHtml(feature) + '</span>'; }).join('');
    if (recordingMode) {
      stage.innerHTML = '<section class="demo-screen">' +
        '<header class="screen-heading"><div><h1>拍照识景</h1><p>' + escapeHtml(vision.subtitle) + '</p></div>' + dataChip('等待图片', 'add_a_photo') + '</header>' +
        '<div class="vision-input-card"><span class="material-icons">add_photo_alternate</span><h2>选择一张现场照片</h2><p>可以拍摄造像细节，也可以上传刚刚拍下的建筑。</p><button class="vision-pick" type="button"><span class="material-icons">photo_library</span>从相册选择</button></div>' +
        '<div id="vision-recording-result"></div>' +
        '</section>';
      var pickButton = stage.querySelector('.vision-pick');
      pickButton.addEventListener('click', function () {
        stage.querySelector('.vision-input-card').innerHTML = '<div class="vision-question"><span class="material-icons">photo_camera</span><p>' + escapeHtml(vision.question) + '</p><em>图片已选择</em></div>' +
          '<div class="vision-preview has-photo ' + escapeHtml(vision.cropClass) + '"><img src="' + escapeHtml(vision.image) + '" alt="' + escapeHtml(vision.imageAlt) + '" style="object-position:' + escapeHtml(vision.imagePosition) + '"><span class="camera-frame"></span><small class="vision-credit">' + escapeHtml(vision.imageCredit) + '</small></div>' +
          '<button class="vision-recognize" type="button"><span class="material-icons">center_focus_strong</span>开始识别</button>';
        stage.querySelector('.vision-recognize').addEventListener('click', function () {
          var button = this;
          button.disabled = true;
          button.innerHTML = '<span class="recording-spinner"></span>正在识别画面特征';
          later(function () {
            stage.querySelector('.vision-input-card').classList.add('vision-input-compact');
            button.remove();
            document.getElementById('vision-recording-result').innerHTML = '<article class="vision-result"><span class="result-check material-icons">done_all</span><div><small>' + escapeHtml(vision.category) + '</small><h2>' + escapeHtml(vision.result) + '</h2><p>' + escapeHtml(vision.output) + '</p></div></article><div class="feature-row">' + features + '</div>' + sourceBlock(vision.source, vision.sourceDetail);
          }, 1050);
        });
      });
      return;
    }
    stage.innerHTML = '<section class="demo-screen">' +
      '<header class="screen-heading"><div><h1>拍照识景</h1><p>' + escapeHtml(vision.subtitle) + '</p></div>' + dataChip('匹配 ' + vision.confidence + '%', 'center_focus_strong') + '</header>' +
      '<div class="vision-question"><span class="material-icons">photo_camera</span><p>' + escapeHtml(vision.question) + '</p><em>刚刚拍摄</em></div>' +
      '<div class="vision-preview has-photo ' + escapeHtml(vision.cropClass) + '"><img src="' + escapeHtml(vision.image) + '" alt="' + escapeHtml(vision.imageAlt) + '" style="object-position:' + escapeHtml(vision.imagePosition) + '"><span class="camera-frame"></span><small class="vision-credit">' + escapeHtml(vision.imageCredit) + '</small><label>' + escapeHtml(vision.focusLabel) + '</label></div>' +
      '<article class="vision-result"><span class="result-check material-icons">done_all</span><div><small>' + escapeHtml(vision.category) + '</small><h2>' + escapeHtml(vision.result) + '</h2><p>' + escapeHtml(vision.output) + '</p></div></article>' +
      '<div class="feature-row">' + features + '</div>' +
      sourceBlock(vision.source, vision.sourceDetail) +
      '</section>';
  }

  function routeStops(stops, compact) {
    return stops.map(function (stop, index) {
      return '<article class="route-stop' + (compact ? ' compact' : '') + '"><b>' + (index + 1) + '</b><div><strong>' + escapeHtml(stop.name) + '</strong><small>' + escapeHtml(stop.time) + '</small></div><em>' + escapeHtml(stop.status) + '</em></article>';
    }).join('');
  }

  function renderRoute() {
    var route = fixture.route;
    setNav('ask');
    var matched = route.matched.map(function (tag) { return '<span><span class="material-icons">done</span>' + escapeHtml(tag) + '</span>'; }).join('');
    if (recordingMode) {
      stage.innerHTML = '<section class="demo-screen">' +
        '<header class="screen-heading"><div><h1>路线规划</h1><p>先告诉我时间、兴趣和同行情况</p></div>' + dataChip('新行程', 'route') + '</header>' +
        '<section class="route-form"><label><span>游览时间</span><strong>2 小时</strong></label><label><span>同行成员</span><strong>长者同行</strong></label><label><span>兴趣偏好</span><strong>历史文化</strong></label><label><span>体力偏好</span><strong>少走路</strong></label><button class="route-build" type="button"><span class="material-icons">auto_awesome</span>生成适合我们的路线</button></section>' +
        '<div id="route-recording-result"></div>' +
        '</section>';
      stage.querySelector('.route-build').addEventListener('click', function () {
        var button = this;
        button.disabled = true;
        button.innerHTML = '<span class="recording-spinner"></span>正在组合景点与休息点';
        later(function () {
          document.getElementById('route-recording-result').innerHTML = '<article class="route-summary"><div><small>推荐路线</small><h2>' + escapeHtml(route.title) + '</h2><p>' + escapeHtml(route.feature) + '</p></div><strong>' + escapeHtml(route.duration) + '</strong></article><div class="route-kpis"><span><b>' + escapeHtml(route.distance) + '</b>预计步行</span><span><b>2 处</b>休息点</span><span><b>轻松</b>路线强度</span></div><div class="matched-row">' + matched + '</div><div class="route-list dense">' + routeStops(route.stops, true) + '</div>';
          stage.querySelector('.route-form').classList.add('route-form-complete');
        }, 950);
      });
      return;
    }
    stage.innerHTML = '<section class="demo-screen">' +
      '<header class="screen-heading"><div><h1>个性路线</h1><p>' + escapeHtml(route.input) + '</p></div>' + dataChip('偏好已匹配', 'tune') + '</header>' +
      '<article class="route-summary"><div><small>推荐路线</small><h2>' + escapeHtml(route.title) + '</h2><p>' + escapeHtml(route.feature) + '</p></div><strong>' + escapeHtml(route.duration) + '</strong></article>' +
      '<div class="route-kpis"><span><b>' + escapeHtml(route.distance) + '</b>预计步行</span><span><b>2 处</b>休息点</span><span><b>轻松</b>路线强度</span></div>' +
      '<div class="matched-row">' + matched + '</div>' +
      '<div class="route-list dense">' + routeStops(route.stops, true) + '</div>' +
      '</section>';
  }

  function renderRouteEvent() {
    var event = fixture.routeEvent;
    setNav('ask');
    stage.innerHTML = '<section class="demo-screen">' +
      '<header class="screen-heading"><div><h1>路线已调整</h1><p>现场变化发生后，行程随即更新</p></div>' + dataChip(event.type, 'sensors') + '</header>' +
      '<article class="live-event-card"><span class="material-icons">groups</span><div><small>实时运营事件</small><h2>' + escapeHtml(event.title) + '</h2><p>' + escapeHtml(event.detail) + '</p></div></article>' +
      '<section class="route-compare"><article class="before"><span>原路线</span><p>' + escapeHtml(event.before) + '</p></article><div class="reroute-arrow"><span class="material-icons">south</span><b>' + escapeHtml(event.saved) + '</b></div><article class="after"><span>新路线</span><p>' + escapeHtml(event.after) + '</p><footer><b>' + escapeHtml(event.duration) + '</b><b>' + escapeHtml(event.distance) + '</b></footer></article></section>' +
      '<div class="event-toast"><span class="material-icons">explore</span><span>' + escapeHtml(event.fallback) + '</span></div>' +
      '</section>';
  }

  function renderGuide() {
    var spot = fixture.spots.lingshan_buddha;
    setNav('guide');
    var tags = spot.tags.map(function (tag) { return '<span>' + escapeHtml(tag) + '</span>'; }).join('');
    stage.innerHTML = '<section class="demo-screen guide-screen">' +
      '<header class="screen-heading"><div><h1>数字人讲解</h1><p>到达景点后自动进入适配讲解</p></div>' + dataChip('长者友好 · 0.85×', 'accessibility_new') + '</header>' +
      '<div class="guide-spotline"><span>当前景点 · ' + escapeHtml(spot.name) + '</span><b>同行端已同步</b></div>' +
      '<article class="avatar-card"><img src="../../assets/images/digital-guide-foreground.png" alt="云游数字讲解员"><div class="guide-copy"><span class="status"><i></i>正在讲解</span><h1>' + escapeHtml(spot.name) + '</h1><p>' + escapeHtml(spot.narration) + '</p>' + wave() + '</div></article>' +
      '<div class="knowledge-tags">' + tags + '</div>' +
      '<article class="guide-transcript"><header><strong>实时字幕</strong><span>大号字幕 · 播放中</span></header><p>' + escapeHtml(spot.narration) + '</p></article>' +
      '</section>';
    playProgramAudio(spot.audio);
  }

  function renderInterrupt(answered) {
    var spot = fixture.spots.lingshan_buddha;
    var qa = fixture.questions.interrupt;
    setNav('guide');
    stage.innerHTML = '<section class="demo-screen guide-screen">' +
      '<header class="screen-heading"><div><h1>讲解被提问</h1><p>先回答，再自然回到原讲解</p></div>' + dataChip(answered ? '准备续讲' : '讲解已暂停', answered ? 'play_circle' : 'pause_circle') + '</header>' +
      '<article class="interrupt-stage"><div class="mini-avatar"><img src="../../assets/images/digital-guide-foreground.png" alt="云游数字讲解员"><span>' + (answered ? '正在衔接' : '正在聆听') + '</span></div><div class="interrupt-chat"><div class="chat-bubble mine">' + escapeHtml(qa.question) + '</div>' +
      (answered ? '<article class="answer-card compact-answer"><p>' + escapeHtml(qa.answer) + '</p>' + sourceBlock(qa.source) + '</article>' : '<div class="thinking-line"><i></i><i></i><i></i><span>正在查找相关景区资料</span></div>') + '</div></article>' +
      (answered ? '<article class="resume-card"><span class="material-icons">subdirectory_arrow_right</span><div><strong>自然续讲</strong><p>' + escapeHtml(spot.resume) + '</p></div></article>' : '<article class="pause-card"><span class="material-icons">graphic_eq</span><div><strong>原讲解位置已保存</strong><p>“……再靠近观察莲花座与衣纹细节。”</p></div></article>') +
      '</section>';
    if (!answered) later(function () { renderInterrupt(true); }, 2500);
    else playProgramAudio(qa.audio);
  }

  function renderPrivateAssist() {
    var qa = fixture.questions.private;
    var assist = fixture.privateAssist;
    setNav('team');
    stage.innerHTML = '<section class="demo-screen">' +
      '<header class="screen-heading"><div><h1>懂分寸的协助</h1><p>私人需求不在公共频道播报</p></div>' + dataChip('隐私保护已启用', 'shield') + '</header>' +
      '<div class="privacy-question"><span class="member-avatar">B</span><div><small>' + escapeHtml(assist.tourist) + ' · 语音提问</small><p>' + escapeHtml(qa.question) + '</p></div></div>' +
      '<div class="decision-flow"><article><span class="material-icons">volume_off</span><div><small>公共频道</small><strong>' + escapeHtml(assist.publicAction) + '</strong></div><em>未播报</em></article><article class="active"><span class="material-icons">lock</span><div><small>游客私人频道</small><strong>' + escapeHtml(assist.privateAction) + '</strong></div><em>已回复</em></article><article><span class="material-icons">notifications_active</span><div><small>领队工作台</small><strong>' + escapeHtml(assist.leaderAction) + '</strong></div><em>需关注</em></article></div>' +
      '<article class="private-answer"><span class="material-icons">health_and_safety</span><div><strong>仅你可见</strong><p>' + escapeHtml(qa.answer) + '</p></div></article>' +
      '<div class="event-toast"><span class="material-icons">privacy_tip</span><span>' + escapeHtml(assist.privacy) + '</span></div>' +
      '</section>';
  }

  function renderProfile() {
    var profile = fixture.profile;
    setNav('guide');
    var tags = profile.tags.map(function (tag) { return '<span>' + escapeHtml(tag) + '</span>'; }).join('');
    var changes = profile.changes.map(function (change) {
      return '<article><span class="material-icons">' + escapeHtml(change.icon) + '</span><small>' + escapeHtml(change.label) + '</small><strong>' + escapeHtml(change.value) + '</strong></article>';
    }).join('');
    stage.innerHTML = '<section class="demo-screen">' +
      '<header class="screen-heading"><div><h1>因人而变</h1><p>画像变化，讲解和路线同时变化</p></div>' + dataChip('偏好已生效', 'auto_awesome') + '</header>' +
      '<article class="profile-hero"><div><small>当前导览画像</small><h2>' + escapeHtml(profile.name) + '</h2><div class="profile-tags">' + tags + '</div></div><span class="material-icons">accessible</span></article>' +
      '<section class="adapt-grid">' + changes + '</section>' +
      '<article class="adapt-narration"><span class="material-icons">record_voice_over</span><div><small>数字人讲解策略</small><p>' + escapeHtml(profile.narration) + '</p></div></article>' +
      '<div class="mode-switch"><span>普通导览</span><b><i></i></b><strong>长者友好</strong></div>' +
      '</section>';
  }

  function renderLeaderRoom() {
    var room = fixture.leaderRoom;
    setNav('team');
    var stops = room.stops.map(function (stop, index) {
      var state = index < 2 ? 'done' : index === 2 ? 'active' : '';
      return '<span class="leader-stop ' + state + '"><b>' + (index + 1) + '</b><small>' + escapeHtml(stop) + '</small></span>';
    }).join('');
    var members = room.members.map(function (member, index) {
      return '<article class="leader-member' + (member.request ? ' needs-help' : '') + '"><span class="member-avatar">' + escapeHtml(member.name.slice(0, 1)) + '</span><div><strong>' + escapeHtml(member.name) + '</strong><small>' + escapeHtml(member.state) + '</small></div>' +
        (member.request ? '<em><span class="material-icons">notifications</span>' + escapeHtml(member.request) + '</em>' : '<i>' + (index + 1) + '</i>') + '</article>';
    }).join('');
    stage.innerHTML = '<section class="demo-screen role-screen">' +
      '<header class="screen-heading"><div><h1>团长工作台</h1><p>建队、带队与成员状态集中管理</p></div>' + dataChip(room.online, 'groups') + '</header>' +
      '<article class="leader-room-card"><header><div><small>同行口令</small><strong>' + escapeHtml(room.code) + '</strong></div><span>进行中</span></header><p><span class="material-icons">route</span>' + escapeHtml(room.route) + '</p><footer><button type="button"><span class="material-icons">content_copy</span>复制口令</button><button type="button"><span class="material-icons">ios_share</span>邀请同行</button></footer></article>' +
      '<section class="leader-route"><header><strong>当前行程</strong><span>' + escapeHtml(room.current) + '</span></header><div class="leader-stops">' + stops + '</div></section>' +
      '<section class="leader-members"><header><strong>成员状态</strong><div><button class="active" type="button">全部</button><button type="button">请求</button><span class="material-icons">refresh</span></div></header><div>' + members + '</div></section>' +
      '<div class="leader-bottom-actions"><button type="button"><span class="material-icons">add_circle</span>新建小队</button><button type="button"><span class="material-icons">tune</span>选择路线</button></div>' +
      '</section>';
  }

  function renderLeaderControl() {
    var control = fixture.leaderControl;
    setNav('team');
    var commands = control.commands.map(function (command, index) {
      return '<button type="button"' + (index === 0 ? ' class="primary"' : '') + '><span class="material-icons">' + escapeHtml(command.icon) + '</span><strong>' + escapeHtml(command.label) + '</strong></button>';
    }).join('');
    stage.innerHTML = '<section class="demo-screen role-screen">' +
      '<header class="screen-heading"><div><h1>讲解控制台</h1><p>一个动作，同步全队导览节奏</p></div><button class="notice-bell" type="button"><span class="material-icons">notifications</span><i>1</i></button></header>' +
      '<article class="leader-live"><header><span><i></i>讲解进行中</span><b>第 3 / 5 站</b></header><small>当前景点</small><h2>' + escapeHtml(control.spot) + '</h2><p>' + escapeHtml(control.action) + '</p><div class="leader-audio"><button type="button"><span class="material-icons">play_arrow</span></button><div>' + wave() + '<small>温暖女声 · 0.9×</small></div><span>03:18</span></div></article>' +
      '<section class="leader-command-grid">' + commands + '</section>' +
      '<article class="leader-request"><span class="material-icons">health_and_safety</span><div><small>待处理协助</small><strong>' + escapeHtml(control.request) + '</strong><p>仅显示协助类型与位置提醒</p></div><button type="button">处理</button></article>' +
      '<article class="leader-sync"><span class="material-icons">sync</span><div><strong>' + escapeHtml(control.notice) + '</strong><small>' + escapeHtml(control.finish) + '</small></div></article>' +
      '<div class="leader-end-actions"><button type="button"><span class="material-icons">refresh</span>刷新房间</button><button type="button"><span class="material-icons">stop_circle</span>结束导览</button></div>' +
      '</section>';
  }

  function renderAnalytics() {
    var analytics = fixture.analytics;
    setNav('team');
    var metrics = analytics.metrics.map(function (metric, index) {
      return '<article><span class="material-icons">' + ['groups', 'forum', 'photo_camera', 'route'][index] + '</span><div><strong>' + escapeHtml(metric.value) + '</strong><small>' + escapeHtml(metric.label) + '</small></div></article>';
    }).join('');
    var trend = analytics.trend.map(function (value, index) {
      return '<i style="height:' + value + '%"><small>' + (index + 12) + '</small></i>';
    }).join('');
    var questions = analytics.questions.map(function (question, index) {
      return '<li><b>' + (index + 1) + '</b><span>' + escapeHtml(question.text) + '</span><em>' + escapeHtml(question.count) + '</em></li>';
    }).join('');
    var topics = analytics.topics.map(function (topic) { return '<span>' + escapeHtml(topic) + '</span>'; }).join('');
    stage.innerHTML = '<section class="demo-screen role-screen admin-screen">' +
      '<header class="screen-heading"><div><h1>景区运营中心</h1><p>服务效果、游客需求与系统状态一屏掌握</p></div>' + dataChip('今日实时汇总', 'dashboard') + '</header>' +
      '<section class="admin-metrics">' + metrics + '</section>' +
      '<section class="analytics-grid"><article class="trend-card"><header><strong>服务趋势</strong><span>近 7 日</span></header><div class="trend-bars">' + trend + '</div></article><article class="satisfaction-card"><small>游客满意度</small><strong>' + escapeHtml(analytics.satisfaction) + '</strong><span>正向评价持续上升</span><div><b>同行房间</b><em>' + escapeHtml(analytics.rooms) + '</em></div></article></section>' +
      '<article class="hot-questions"><header><strong>高频问题</strong><span>文本 · 语音 · 识图</span></header><ol>' + questions + '</ol></article>' +
      '<section class="admin-bottom-grid"><article><small>当前热点</small><div class="topic-tags">' + topics + '</div></article><article><small>系统状态</small><strong><i></i>稳定运行</strong><p>响应 0.8s · 异常 0</p></article></section>' +
      '</section>';
  }

  function renderKnowledgeBase() {
    var kb = fixture.knowledgeBase;
    setNav('team');
    var categories = kb.categories.map(function (category, index) { return '<button type="button"' + (index === 0 ? ' class="active"' : '') + '>' + escapeHtml(category) + '</button>'; }).join('');
    var docs = kb.docs.map(function (doc) {
      var extension = doc.name.split('.').pop().toUpperCase();
      return '<article class="kb-row"><b>' + escapeHtml(extension) + '</b><div><strong>' + escapeHtml(doc.name) + '</strong><small>' + escapeHtml(doc.category) + ' · ' + escapeHtml(doc.status) + '</small></div><span><button type="button"><i class="material-icons">edit</i></button><button type="button"><i class="material-icons">delete</i></button></span></article>';
    }).join('');
    stage.innerHTML = '<section class="demo-screen role-screen admin-screen">' +
      '<header class="screen-heading"><div><h1>知识库管理</h1><p>把景区资料沉淀为可追溯的回答依据</p></div>' + dataChip(kb.count, 'menu_book') + '</header>' +
      '<div class="kb-toolbar"><label><span class="material-icons">search</span><input value="" placeholder="搜索资料名称或内容" readonly></label><button type="button"><span class="material-icons">cloud_upload</span>上传资料</button></div>' +
      '<div class="kb-categories">' + categories + '</div>' +
      '<section class="kb-list"><header><strong>资料列表</strong><span>支持 TXT · MD · JSON · PDF</span></header>' + docs + '</section>' +
      '<article class="kb-actions"><div><span class="material-icons">account_tree</span><p><strong>资料整理完成</strong><small>分段、分类与引用关系已更新</small></p></div><button type="button"><span class="material-icons">refresh</span>重新整理</button></article>' +
      '<div class="kb-page"><button type="button">上一页</button><span>1 / 13</span><button type="button">下一页</button></div>' +
      '</section>';
  }

  function renderAvatarStudio() {
    var avatar = fixture.avatarStudio;
    setNav('team');
    var switches = avatar.switches.map(function (item) { return '<label><span>' + escapeHtml(item) + '</span><i><b></b></i></label>'; }).join('');
    stage.innerHTML = '<section class="demo-screen role-screen admin-screen">' +
      '<header class="screen-heading"><div><h1>数字人形象</h1><p>统一配置讲解形象、声音与动作表现</p></div>' + dataChip('预览已同步', 'face') + '</header>' +
      '<article class="avatar-studio-hero"><div class="avatar-stage"><img src="../../assets/images/digital-guide-foreground.png" alt="云游数字讲解员"><span>预览中</span></div><div class="avatar-pickers"><small>选择形象</small><div><button class="active" type="button">A</button><button type="button">B</button></div><label>服装风格<strong>' + escapeHtml(avatar.outfit) + '</strong></label><button class="upload-look" type="button"><span class="material-icons">photo_camera</span>上传形象图片</button></div></article>' +
      '<section class="voice-settings"><header><strong>声音与表达</strong><button type="button"><span class="material-icons">play_arrow</span>试听</button></header><div><label><small>讲解声音</small><strong>' + escapeHtml(avatar.voice) + '</strong></label><label><small>语速</small><strong>' + escapeHtml(avatar.speed) + '</strong></label><label><small>默认表情</small><strong>' + escapeHtml(avatar.expression) + '</strong></label></div></section>' +
      '<section class="avatar-switches">' + switches + '</section>' +
      '<article class="avatar-preview-line"><span class="material-icons">record_voice_over</span><p>' + escapeHtml(avatar.preview) + '</p></article>' +
      '<div class="avatar-save"><button type="button"><span class="material-icons">visibility</span>全屏预览</button><button type="button"><span class="material-icons">save</span>保存配置</button></div>' +
      '</section>';
    var previewButton = stage.querySelector('.voice-settings header button');
    if (previewButton) previewButton.addEventListener('click', function () { playProgramAudio(avatar.audio); });
  }

  function renderOperations() {
    var operations = fixture.operations;
    setNav('team');
    var metrics = operations.metrics.map(function (metric) { return '<article><strong>' + escapeHtml(metric.value) + '</strong><small>' + escapeHtml(metric.label) + '</small></article>'; }).join('');
    stage.innerHTML = '<section class="demo-screen">' +
      '<header class="screen-heading"><div><h1>运营知识闭环</h1><p>不确定的问题进入审核，而不是编造</p></div>' + dataChip('今日质量监测', 'monitoring') + '</header>' +
      '<section class="quality-grid">' + metrics + '</section>' +
      '<article class="knowledge-gap"><header><span class="material-icons">help_center</span><div><small>新发现的知识缺口</small><h2>' + escapeHtml(operations.gapQuestion) + '</h2></div></header><div class="gap-status"><span class="material-icons">rule</span>' + escapeHtml(operations.gapStatus) + '</div><p>' + escapeHtml(operations.suggestion) + '</p><footer><span>游客端已使用谨慎回答</span><button type="button">进入资料审核</button></footer></article>' +
      '<article class="loop-flow"><span>游客提问</span><i></i><span>可信度检查</span><i></i><span>人工审核</span><i></i><span>知识更新</span></article>' +
      '</section>';
  }

  function renderPassport() {
    var passport = fixture.passport;
    setNav('guide');
    var stats = passport.stats.map(function (stat) { return '<div><strong>' + escapeHtml(stat.value) + '</strong><small>' + escapeHtml(stat.label) + '</small></div>'; }).join('');
    stage.innerHTML = '<section class="demo-screen passport-screen">' +
      '<div class="passport-seal"><span class="material-icons">star</span></div><small class="passport-kicker">本次导览已完成</small><h1>' + escapeHtml(passport.title) + '</h1><p>' + escapeHtml(passport.subtitle) + '</p>' +
      '<div class="passport-stats">' + stats + '</div>' +
      '<article class="passport-badge"><span class="material-icons">landscape</span><div><small>获得文化徽章</small><strong>' + escapeHtml(passport.badge) + '</strong></div></article>' +
      '<div class="passport-note"><span class="material-icons">bookmark_added</span>' + escapeHtml(passport.note) + '</div>' +
      '<button class="passport-action" type="button"><span class="material-icons">ios_share</span>保存我的文化护照</button>' +
      '</section>';
  }

  function renderIntro() {
    setNav('ask');
    if (recordingMode) {
      stage.innerHTML = '<section class="demo-screen role-intro-screen">' +
        '<div class="role-intro-hero"><div class="end-seal"><span class="material-icons">landscape</span></div><p class="intro-eyebrow">灵山胜境智能导览</p><h1>云游智导</h1><p>选择身份，开始今天的导览。</p></div>' +
        '<div class="role-entry-list"><button class="role-entry active" data-role-entry="visitor" type="button"><span class="material-icons">person</span><div><strong>我是游客</strong><small>问答、识景、路线与随行讲解</small></div><i class="material-icons">arrow_forward</i></button><button class="role-entry" data-role-entry="leader" type="button"><span class="material-icons">groups</span><div><strong>我是团长</strong><small>创建小队并控制团队导览</small></div><i class="material-icons">arrow_forward</i></button><button class="role-entry" data-role-entry="admin" type="button"><span class="material-icons">admin_panel_settings</span><div><strong>景区管理员</strong><small>查看运营数据并维护内容</small></div><i class="material-icons">arrow_forward</i></button></div>' +
        '<div class="role-intro-foot"><span><i></i>景区服务在线</span><span>三端协同</span></div>' +
        '</section>';
      return;
    }
    stage.innerHTML = '<section class="demo-screen intro-screen"><div class="end-seal"><span class="material-icons">landscape</span></div><p class="intro-eyebrow">可信 · 自适应 · 懂分寸</p><h1>云游智导</h1><p>让每一次景区讲解，都能因人、因地、因现场变化而调整。</p><div class="reset-note"><span class="material-icons">explore</span>导览即将开始</div></section>';
  }

  function renderReset() {
    setNav('ask');
    stage.innerHTML = '<section class="demo-screen end-screen"><div class="end-seal"><span class="material-icons">restart_alt</span></div><h1>演示状态已重置</h1><p>所有界面和进度已经恢复到录制起点。</p><div class="reset-note"><span class="material-icons">check_circle</span>可以开始下一次录制</div></section>';
  }

  function renderStep(stepId) {
    if (audio) { audio.pause(); audio.currentTime = 0; }
    if (stepId === 'qa') renderAsk();
    else if (stepId === 'vision-symbol') renderVision('symbol');
    else if (stepId === 'vision-building') renderVision('building');
    else if (stepId === 'route') renderRoute();
    else if (stepId === 'route-event') renderRouteEvent();
    else if (stepId === 'guide') renderGuide();
    else if (stepId === 'interrupt') renderInterrupt(false);
    else if (stepId === 'leader-room') renderLeaderRoom();
    else if (stepId === 'leader-control') renderLeaderControl();
    else if (stepId === 'private-assist') renderPrivateAssist();
    else if (stepId === 'profile') renderProfile();
    else if (stepId === 'admin-analytics') renderAnalytics();
    else if (stepId === 'admin-kb') renderKnowledgeBase();
    else if (stepId === 'operations') renderOperations();
    else if (stepId === 'admin-avatar') renderAvatarStudio();
    else if (stepId === 'passport') renderPassport();
  }

  function go(index) {
    index = Number(index);
    if (!Number.isFinite(index) || index < 0 || index >= fixture.steps.length) return Promise.resolve(false);
    clearTimers();
    setStepMeta(index);
    renderStep(fixture.steps[index].id);
    return Promise.resolve(true);
  }

  function stop() {
    runtime.runId += 1;
    runtime.playing = false;
    clearTimers();
    if (audio) { audio.pause(); audio.currentTime = 0; }
  }

  function reset() {
    stop();
    if (window.CompetitionReset) window.CompetitionReset.clearLocal();
    setStepMeta(-1);
    renderReset();
  }

  async function start() {
    stop();
    runtime.playing = true;
    var thisRun = runtime.runId;
    for (var index = 0; index < fixture.steps.length; index += 1) {
      if (thisRun !== runtime.runId) return;
      await go(index);
      if (thisRun !== runtime.runId) return;
      await delay(fixture.steps[index].duration);
    }
    if (thisRun === runtime.runId) runtime.playing = false;
  }

  try {
    var channel = new BroadcastChannel('competition-demo-control');
    channel.addEventListener('message', function (event) {
      var message = event.data || {};
      if (message.type === 'go') { stop(); go(message.index); }
      else if (message.type === 'start') start();
      else if (message.type === 'reset') reset();
    });
  } catch (_) {}

  function indexFor(stepId) {
    return fixture.steps.findIndex(function (step) { return step.id === stepId; });
  }

  navButtons.forEach(function (button) {
    button.addEventListener('click', function () {
      var target = button.dataset.nav === 'ask' ? 'qa' : button.dataset.nav === 'guide' ? 'guide' : 'private-assist';
      stop();
      go(indexFor(target));
    });
  });

  window.CompetitionDemo = {
    fixture: fixture,
    runtime: runtime,
    start: start,
    stop: stop,
    reset: reset,
    go: go,
    intro: renderIntro,
    duration: fixture.steps.reduce(function (sum, step) { return sum + step.duration; }, 0)
  };

  setStepMeta(-1);
  if (recordingMode) {
    document.body.classList.add('recording-mode');
    renderIntro();
  } else if (new URLSearchParams(window.location.search).get('autoplay') === '1') {
    renderIntro();
    later(start, 900);
  } else {
    renderAsk();
  }
})();
