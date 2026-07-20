(function () {
  'use strict';

  function ready(callback) {
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', callback);
    else callback();
  }

  ready(function () {
    var page = document.getElementById('page-body');
    var layout = document.querySelector('.visitor-layout');
    var stage = document.querySelector('.tour-stage');
    var tourSide = document.querySelector('.tour-side');
    var serviceSide = document.querySelector('.service-side');
    var textMode = document.getElementById('text-mode');
    var avatarMode = document.getElementById('avatar-mode');
    var input = document.getElementById('public-chat-input');
    var send = document.getElementById('public-chat-send');

    if (!page || !layout || !stage || !tourSide || !serviceSide || !textMode || !avatarMode) return;

    page.classList.add('visitor-chat-page');
    page.dataset.context = 'personal';

    var shell = document.createElement('header');
    shell.className = 'visitor-shell-bar';
    shell.innerHTML = [
      '<button class="visitor-shell-icon" id="visitor-drawer-open" type="button" aria-label="打开副界面"><span class="material-icons">menu</span></button>',
      '<nav class="visitor-context-orbit" id="visitor-context-orbit" aria-label="导览对象切换"></nav>',
      '<button class="visitor-new-chat" id="visitor-new-chat" type="button" aria-label="新对话"></button>'
    ].join('');
    page.insertBefore(shell, layout);

    var shade = document.createElement('div');
    shade.className = 'visitor-drawer-backdrop';
    var drawer = document.createElement('aside');
    drawer.className = 'visitor-drawer';
    drawer.setAttribute('aria-label', '导览副界面');
    drawer.innerHTML = [
      '<header class="visitor-drawer-head"><div><strong>我的导览</strong><span>房间、同行游客与服务</span></div>',
      '<button class="visitor-shell-icon" id="visitor-drawer-close" type="button" aria-label="关闭副界面"><span class="material-icons">close</span></button></header>',
      '<div class="visitor-drawer-body"></div>'
    ].join('');
    var drawerBody = drawer.querySelector('.visitor-drawer-body');
    drawerBody.appendChild(tourSide);
    drawerBody.appendChild(serviceSide);
    page.appendChild(shade);
    page.appendChild(drawer);

    var groupBanner = document.createElement('div');
    groupBanner.className = 'visitor-context-banner';
    groupBanner.textContent = '旅游团公共频道：消息将同步给已加入房间的同行游客。';
    textMode.insertBefore(groupBanner, textMode.firstChild);

    var contexts = [
      { id: 'personal', label: '个人', placeholder: '问问景点、路线或个人偏好…' },
      { id: 'avatar', label: '数字人', placeholder: '按住说话，或输入文字…' },
      { id: 'group', label: '旅游团', placeholder: '向旅游团发起公共问答…' }
    ];
    var current = 'personal';
    var orbit = document.getElementById('visitor-context-orbit');

    function hasRoom() {
      return !!(window.Aurelian && window.Aurelian.state && window.Aurelian.state.get('roomId'));
    }

    function renderOrbit() {
      var currentIndex = contexts.map(function (item) { return item.id; }).indexOf(current);
      orbit.innerHTML = '';
      contexts.forEach(function (item, index) {
        var offset = (index - currentIndex + contexts.length) % contexts.length;
        var slot = offset === 0 ? 'current' : offset === 1 ? 'next' : 'prev';
        var button = document.createElement('button');
        button.className = 'visitor-orbit-item' + (item.id === 'group' && !hasRoom() ? ' is-disabled' : '');
        button.type = 'button';
        button.dataset.slot = slot;
        button.textContent = item.label;
        button.addEventListener('click', function () { selectContext(item.id); });
        orbit.appendChild(button);
      });
    }

    function showMode(context) {
      if (context === 'avatar') {
        textMode.classList.add('hidden');
        avatarMode.classList.remove('hidden');
      } else {
        avatarMode.classList.add('hidden');
        textMode.classList.remove('hidden');
      }
    }

    function closeDrawer() {
      page.classList.remove('drawer-open');
    }

    function selectContext(context) {
      if (context === 'group' && !hasRoom()) {
        var joinOverlay = document.getElementById('room-join-overlay');
        if (joinOverlay) joinOverlay.classList.remove('hidden');
        return;
      }

      current = context;
      page.dataset.context = context;
      page.classList.add('is-chatting');
      var item = contexts.filter(function (entry) { return entry.id === context; })[0];
      if (input) input.placeholder = item.placeholder;
      showMode(context);
      renderOrbit();
      closeDrawer();
    }

    document.getElementById('visitor-drawer-open').addEventListener('click', function () {
      page.classList.add('drawer-open');
    });
    document.getElementById('visitor-drawer-close').addEventListener('click', closeDrawer);
    shade.addEventListener('click', closeDrawer);

    document.getElementById('visitor-new-chat').addEventListener('click', function () {
      current = 'personal';
      page.dataset.context = 'personal';
      page.classList.remove('is-chatting');
      if (input) {
        input.value = '';
        input.focus();
      }
      showMode('personal');
      renderOrbit();
      closeDrawer();
    });

    if (send) send.addEventListener('click', function () { page.classList.add('is-chatting'); }, true);
    if (input) input.addEventListener('keydown', function (event) {
      if (event.key === 'Enter' && !event.shiftKey) page.classList.add('is-chatting');
    }, true);

    renderOrbit();
    showMode('personal');
  });
})();
