(function () {
  'use strict';

  var path = window.location.pathname.replace(/\\/g, '/');
  var page = path.indexOf('/guide-panel/') > -1 ? 'guide' :
    path.indexOf('/dashboard/') > -1 ? 'dashboard' :
    path.indexOf('/knowledge-base/') > -1 ? 'kb' :
    path.indexOf('/ai-assistant/') > -1 ? 'assistant' :
    path.indexOf('/user-portal/') > -1 ? 'portal' : 'landing';

  document.body.classList.add('sc-' + page);
  if (page === 'guide' || page === 'dashboard') {
    document.body.classList.add('sc-admin');
    addSidebar(page);
  }
  if (page === 'guide') addAttentionPanel();
  if (page === 'guide' && new URLSearchParams(location.search).get('preview') === '1') {
    window.setTimeout(fillGuidePreview, 250);
  }

  function icon(name) {
    return '<span class="material-symbols-outlined" aria-hidden="true">' + name + '</span>';
  }

  function addSidebar(active) {
    var sidebar = document.createElement('aside');
    sidebar.className = 'sc-sidebar';
    sidebar.setAttribute('aria-label', '主导航');
    sidebar.innerHTML =
      '<div class="sc-brand"><div><div class="sc-brand-cn">智慧导览</div><div class="sc-brand-en">AURELIAN GUIDE</div></div></div>' +
      '<nav class="sc-nav">' +
        nav('dashboard', '../dashboard/index.html', 'monitoring', '数据大屏', active) +
        nav('guide', '../guide-panel/index.html', 'tour', '导览控制台', active) +
        nav('kb', '../knowledge-base/index.html', 'library_books', '知识库管理', active) +
        nav('avatar', '#', 'face_6', '数字人形象', active) +
        nav('feedback', '#', 'forum', '游客反馈', active) +
        nav('settings', '#', 'settings', '系统设置', active) +
      '</nav>' +
      '<section class="sc-live-card"><header><span>房间实时状态</span><span style="color:#60c77d">● 运行中</span></header>' +
        '<dl><div><dt>房间号</dt><dd data-sc-room>839201</dd></div><div><dt>在线游客</dt><dd data-sc-members>8 人</dd></div><div><dt>当前景区</dt><dd>黄山风景区</dd></div><div><dt>当前路线</dt><dd>经典路线</dd></div></dl></section>' +
      '<div class="sc-user"><span class="sc-avatar">A</span><span>Admin<small>管理员</small></span></div>';
    document.body.insertBefore(sidebar, document.body.firstChild);
  }

  function nav(key, href, iconName, label, active) {
    return '<a class="' + (key === active ? 'active' : '') + '" href="' + href + '">' + icon(iconName) + '<span>' + label + '</span></a>';
  }

  function addAttentionPanel() {
    var main = document.querySelector('main');
    if (!main) return;
    var panel = document.createElement('aside');
    panel.className = 'sc-attention';
    panel.innerHTML = '<h2>注意事项</h2>' +
      '<button id="sc-request-shortcut" class="w-full text-left px-3 py-3 border border-[#efd4c4] rounded-lg text-[#d85f2d] bg-[#fff9f4]">● 私人请求待处理（2）</button>' +
      '<div class="sc-attention-item"><strong><span>游客 A</span><time>14:23</time></strong><p>想了解山顶日出观景点的位置。</p></div>' +
      '<div class="sc-attention-item"><strong><span>游客 B</span><time>14:21</time></strong><p>请推荐适合老人游览的路线。</p></div>' +
      '<div class="sc-signal-list"><div><span>举手提问</span><b>1</b></div><div><span>停留过久</span><b>2</b></div><div><span>重复咨询</span><b>0</b></div><div><span>网络波动</span><b>0</b></div></div>';
    main.appendChild(panel);
    var shortcut = panel.querySelector('#sc-request-shortcut');
    shortcut.addEventListener('click', function () {
      var target = document.getElementById('btn-view-requests2') || document.getElementById('btn-view-requests');
      if (target) target.click();
    });
  }

  function fillGuidePreview() {
    var values = {
      'room-id-display': '839201', 'route-name-display': '经典路线', 'member-count': '8 人',
      'current-spot-display': '主展厅', 'scenic-area-display': '黄山风景区', 'progress-display': '第3段/共12段',
      'pending-requests-text': '2 条私人请求待处理', 'spot-selector-label': '主展厅', 'requests-badge': '2'
    };
    Object.keys(values).forEach(function (id) {
      var el = document.getElementById(id); if (el) el.textContent = values[id];
    });
    ['pending-requests-row', 'btn-view-requests', 'requests-badge'].forEach(function (id) {
      var el = document.getElementById(id); if (el) el.classList.remove('hidden');
    });
    var list = document.getElementById('member-list');
    var title = document.getElementById('member-list-title');
    if (title) title.textContent = '在线游客 (8)';
    if (list) {
      list.innerHTML = ['A','B','C','D','E','F','G','H'].map(function (name, index) {
        return '<li class="flex items-center justify-between px-lg py-sm"><div class="flex items-center gap-md"><div class="w-[32px] h-[32px] rounded-full bg-surface-variant flex items-center justify-center">' + name + '</div><span class="text-[14px] font-medium">游客' + name + '</span></div><span class="text-xs" style="color:' + (index < 2 ? '#df7032' : '#4e8c63') + '">● ' + (index < 2 ? '有提问' : '在线') + '</span></li>';
      }).join('');
    }
  }

  var observer = new MutationObserver(function () {
    var room = document.getElementById('room-id-display');
    var members = document.getElementById('member-count');
    var roomText = room ? room.textContent.trim() : '';
    var membersText = members ? members.textContent.trim() : '';
    if (!roomText && !membersText) return;
    // Disconnect during update to prevent infinite loop
    observer.disconnect();
    document.querySelectorAll('[data-sc-room]').forEach(function (el) {
      var current = (el.textContent || '').trim();
      if (roomText && current !== roomText) el.textContent = roomText;
    });
    document.querySelectorAll('[data-sc-members]').forEach(function (el) {
      var current = (el.textContent || '').trim();
      if (membersText && current !== membersText) el.textContent = membersText;
    });
    observer.observe(document.body, { childList: true, subtree: true });
  });
  observer.observe(document.body, { childList: true, subtree: true });
})();
