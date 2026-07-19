(function () {
  'use strict';

  var params = new URLSearchParams(window.location.search);
  if (params.get('record') !== '1' || !window.CompetitionDemo) return;

  var speed = Number(params.get('speed')) || 1;
  var demo = window.CompetitionDemo;
  var cursor = document.createElement('div');
  cursor.className = 'demo-cursor';
  cursor.innerHTML = '<i></i>';
  document.body.appendChild(cursor);

  var rolePill = document.createElement('div');
  rolePill.className = 'recording-role-pill';
  rolePill.textContent = '身份选择';
  document.body.appendChild(rolePill);

  var live = document.querySelector('.demo-live');
  if (live) live.textContent = '功能实录';

  function wait(ms) {
    return new Promise(function (resolve) { window.setTimeout(resolve, Math.max(20, ms * speed)); });
  }

  function element(selector) {
    return typeof selector === 'string' ? document.querySelector(selector) : selector;
  }

  async function moveTo(selector, offsetX, offsetY) {
    var target = element(selector);
    if (!target) return false;
    var rect = target.getBoundingClientRect();
    var x = rect.left + rect.width / 2 + (offsetX || 0);
    var y = rect.top + rect.height / 2 + (offsetY || 0);
    cursor.style.transform = 'translate(' + x + 'px,' + y + 'px)';
    await wait(620);
    return true;
  }

  async function click(selector) {
    var target = element(selector);
    if (!target) return false;
    await moveTo(target);
    cursor.classList.add('clicking');
    target.classList.add('recording-click-target');
    await wait(170);
    target.click();
    cursor.classList.remove('clicking');
    await wait(220);
    target.classList.remove('recording-click-target');
    return true;
  }

  async function typeInto(selector, text) {
    var input = element(selector);
    if (!input) return false;
    await moveTo(input);
    input.focus();
    input.value = '';
    input.dispatchEvent(new Event('input', { bubbles: true }));
    for (var index = 0; index < text.length; index += 1) {
      var character = text.charAt(index);
      input.dispatchEvent(new KeyboardEvent('keydown', { key: character, bubbles: true }));
      input.value += character;
      input.dispatchEvent(new Event('input', { bubbles: true }));
      input.dispatchEvent(new KeyboardEvent('keyup', { key: character, bubbles: true }));
      await wait(82);
    }
    return true;
  }

  function setRole(label) {
    rolePill.textContent = label;
    rolePill.classList.add('changed');
    window.setTimeout(function () { rolePill.classList.remove('changed'); }, 900 * speed);
  }

  function toast(message, icon) {
    var old = document.querySelector('.recording-action-toast');
    if (old) old.remove();
    var node = document.createElement('div');
    node.className = 'recording-action-toast';
    node.innerHTML = '<span class="material-icons">' + (icon || 'check_circle') + '</span><strong>' + message + '</strong>';
    document.body.appendChild(node);
    window.setTimeout(function () { node.classList.add('show'); }, 30);
    window.setTimeout(function () {
      node.classList.remove('show');
      window.setTimeout(function () { node.remove(); }, 320);
    }, 1700 * speed);
  }

  async function holdScene(seconds, action) {
    var started = performance.now();
    if (action) await action();
    var target = seconds * 1000 * speed;
    var remaining = target - (performance.now() - started);
    if (remaining > 0) await new Promise(function (resolve) { window.setTimeout(resolve, remaining); });
  }

  async function run() {
    cursor.style.transform = 'translate(52vw,72vh)';
    demo.intro();
    document.body.classList.add('recording-running');

    await holdScene(20, async function () {
      await wait(1800);
      await moveTo('[data-role-entry="visitor"]');
      await wait(1600);
      await moveTo('[data-role-entry="leader"]');
      await wait(1300);
      await moveTo('[data-role-entry="admin"]');
    });

    await holdScene(10, async function () {
      await wait(1800);
      await click('[data-role-entry="visitor"]');
      toast('已进入游客端', 'person');
      setRole('游客端');
    });

    await holdScene(25, async function () {
      await demo.go(0);
      await wait(1300);
      await typeInto('.ask-composer input', demo.fixture.questions.culture.question);
      await wait(520);
      await click('.ask-send');
      await wait(1500);
      await moveTo('.source-proof');
    });

    await holdScene(25, async function () {
      await demo.go(1);
      await wait(1200);
      await click('.vision-pick');
      await wait(1250);
      await click('.vision-recognize');
      await wait(1700);
      await moveTo('.vision-result');
    });

    await holdScene(22, async function () {
      await demo.go(2);
      await wait(1000);
      await click('.vision-pick');
      await wait(1100);
      await click('.vision-recognize');
      await wait(1700);
      await moveTo('.source-proof');
    });

    await holdScene(28, async function () {
      await demo.go(3);
      await wait(1200);
      await moveTo('.route-form label:nth-child(2)');
      await wait(700);
      await moveTo('.route-form label:nth-child(4)');
      await wait(500);
      await click('.route-build');
      await wait(1550);
      await moveTo('.route-summary');
    });

    await holdScene(20, async function () {
      await demo.go(4);
      await wait(1400);
      await moveTo('.live-event-card');
      await wait(1200);
      await moveTo('.route-compare .after');
    });

    await holdScene(28, async function () {
      await demo.go(5);
      await wait(1300);
      await moveTo('.avatar-card');
      await wait(1600);
      await moveTo('.guide-transcript');
    });

    await holdScene(22, async function () {
      await demo.go(6);
      await wait(1100);
      await moveTo('.chat-bubble.mine');
      await wait(2500);
      await moveTo('.resume-card');
    });

    await holdScene(25, async function () {
      await demo.go(9);
      await wait(1200);
      await moveTo('.privacy-question');
      await wait(1250);
      await moveTo('.decision-flow .active');
      await wait(1050);
      await moveTo('.private-answer');
    });

    await holdScene(15, async function () {
      await demo.go(10);
      await wait(1000);
      await click('.mode-switch');
      toast('长者友好设置已生效', 'accessibility_new');
    });

    await holdScene(30, async function () {
      setRole('团长端');
      toast('切换至团长工作台', 'groups');
      await demo.go(7);
      await wait(1300);
      await click('.leader-room-card footer button:first-child');
      toast('同行口令已复制', 'content_copy');
      await wait(950);
      await click('.leader-members header button:nth-child(2)');
      await wait(800);
      await moveTo('.leader-member.needs-help');
    });

    await holdScene(30, async function () {
      await demo.go(8);
      await wait(1200);
      await click('.leader-command-grid button:nth-child(1)');
      toast('全队讲解已暂停', 'pause_circle');
      await wait(1000);
      await click('.leader-command-grid button:nth-child(4)');
      toast('集合提醒已发送', 'campaign');
      await wait(1000);
      await click('.leader-request button');
      toast('协助请求已接收', 'health_and_safety');
    });

    await holdScene(30, async function () {
      setRole('管理端');
      toast('切换至景区运营中心', 'admin_panel_settings');
      await demo.go(11);
      await wait(1300);
      await moveTo('.admin-metrics');
      await wait(1300);
      await moveTo('.trend-card');
      await wait(1200);
      await moveTo('.hot-questions');
    });

    await holdScene(25, async function () {
      await demo.go(12);
      await wait(1000);
      await typeInto('.kb-toolbar input', '灵山大佛');
      await wait(650);
      await click('.kb-toolbar > button');
      toast('资料已加入知识库', 'cloud_upload');
      await wait(900);
      await click('.kb-actions > button');
      toast('知识索引已更新', 'refresh');
    });

    await holdScene(20, async function () {
      await demo.go(13);
      await wait(1300);
      await moveTo('.knowledge-gap');
      await wait(900);
      await click('.knowledge-gap button');
      toast('已进入资料审核', 'fact_check');
    });

    await holdScene(20, async function () {
      await demo.go(14);
      await wait(1000);
      await click('.voice-settings header button');
      toast('正在试听程序讲解音色', 'volume_up');
      await wait(900);
      await click('.avatar-pickers > div button:nth-child(2)');
      await wait(800);
      await click('.avatar-switches label:nth-child(2)');
      await wait(650);
      await click('.avatar-save button:last-child');
      toast('数字人配置已保存', 'save');
    });

    await holdScene(25, async function () {
      setRole('游客端 · 行程完成');
      await demo.go(15);
      await wait(1700);
      await moveTo('.passport-badge');
      await wait(1000);
      await click('.passport-action');
      toast('文化护照已保存', 'bookmark_added');
    });

    document.body.classList.add('recording-finished');
    cursor.classList.add('hidden');
    document.title = '云游智导 · 功能实录完成';
  }

  window.CompetitionRecording = { run: run, cursor: cursor };
  if (params.get('autostart') !== '0') window.setTimeout(run, 1200);
})();
