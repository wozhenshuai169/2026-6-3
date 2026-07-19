(function () {
  'use strict';

  window.COMPETITION_FIXTURE = Object.freeze({
    mode: 'competition-showcase',
    badge: '景区知识库已核验',
    roomAlias: 'YUNYOU',
    questions: {
      culture: {
        question: '灵山大佛有哪些值得留意的文化与建筑细节？',
        title: '灵山大佛 · 文化导览',
        answer: '灵山大佛为露天青铜释迦牟尼立像，通高 88 米。参观时可以先从远处观察造像与山势、太湖方向的整体关系，再靠近留意莲花座、手印和衣纹细节。关于数字寓意，现有景区资料没有给出确定解释，因此不作推测。',
        confidence: '高可信',
        source: '灵山胜境公开资料 · 灵山大佛条目',
        sourceDetail: '通高 88 米 · 露天青铜释迦牟尼立像'
      },
      interrupt: {
        question: '为什么建议先从远处看？',
        answer: '远观更容易看清大佛与山势、广场和游览轴线的整体关系；接近后再观察莲花座与衣纹细节，层次会更完整。',
        source: '景区结构化知识库 · 观赏建议',
        audio: '../../assets/audio/competition/interrupt-resume.wav'
      },
      private: {
        question: '我有点头晕，附近哪里可以休息？',
        answer: '已为你切换到私人服务。建议先在原地或最近休息点坐下，不要继续快速行走；情况加重时请联系现场工作人员。领队只会收到需要协助的提醒，不会看到你的完整提问。'
      }
    },
    visionScenes: {
      symbol: {
        question: '掌心中央这个圆形小图案是什么？有什么寓意？',
        subtitle: '从细节纹样连接到文化寓意',
        image: '../../assets/images/competition/vision-palm-wheel.jpg',
        imageAlt: '灵山佛手掌心法轮纹样特写',
        imagePosition: 'center center',
        cropClass: 'detail-crop',
        focusLabel: '已定位掌心圆轮纹样',
        result: '千辐轮相',
        confidence: 96,
        category: '佛教造像细节',
        features: ['掌心圆轮', '放射状辐条', '右手造型'],
        output: '这是“千辐轮相”，也称手足轮相，是佛陀三十二相之一。轮象征佛法运转，常被解释为智慧照破愚痴与无明；整只右手呈“施无畏印”，表达安定、解除恐惧。',
        source: '无锡市档案史志馆《灵山胜境》 · 《佛的三十二相》',
        sourceDetail: '图案含义与右手手印分别核验',
        imageCredit: '图片：Wikimedia Commons · CC BY-SA 3.0'
      },
      building: {
        question: '前面这座红白相间、带金顶的建筑是什么？',
        subtitle: '从建筑特征连接到景区知识',
        image: '../../assets/images/competition/vision-five-seal-mandala.jpg',
        imageAlt: '灵山五印坛城建筑外观',
        imagePosition: 'center 76%',
        cropClass: 'building-crop',
        focusLabel: '已定位金顶与藏式外墙',
        result: '灵山五印坛城',
        confidence: 97,
        category: '藏传佛教文化建筑',
        features: ['红白藏式外墙', '鎏金屋顶', '坛城式布局'],
        output: '这是灵山五印坛城。名称来自释迦牟尼佛常用的五种手印，以及它们象征的五种智慧。建筑集中展示藏传佛教文化艺术，内部可见彩绘、壁画、木雕和唐卡等传统装饰。',
        source: '灵山胜境官方网站 · 景区介绍',
        sourceDetail: '名称由来、文化类型与展陈内容已核验',
        imageCredit: '图片：西安兵马俑 / Wikimedia Commons · CC BY-SA 4.0'
      }
    },
    route: {
      input: '两小时 · 长者同行 · 历史文化 · 少走路',
      title: '长者友好文化线',
      duration: '112 分钟',
      distance: '1.6 公里',
      feature: '坡度较缓 · 2 处休息点 · 预留 18 分钟缓冲',
      matched: ['长者同行', '历史文化', '少走路'],
      stops: [
        { name: '灵山大照壁', time: '10 分钟', status: '文化起点' },
        { name: '九龙灌浴', time: '18 分钟', status: '动态景观' },
        { name: '灵山大佛', time: '32 分钟', status: '核心讲解' },
        { name: '休息驿站', time: '12 分钟', status: '补水休息' },
        { name: '灵山梵宫', time: '22 分钟', status: '室内参观' }
      ]
    },
    routeEvent: {
      type: '人流预警',
      title: '九龙灌浴观景区客流升高',
      detail: '预计等待 26 分钟，已避开拥挤区域并保留核心讲解。',
      before: '大照壁 → 九龙灌浴 → 灵山大佛 → 梵宫',
      after: '大照壁 → 佛手广场 → 灵山大佛 → 休息驿站 → 梵宫',
      duration: '108 分钟',
      distance: '1.5 公里',
      saved: '少等待 22 分钟',
      fallback: '定位信号较弱时，可拍摄附近地标恢复位置'
    },
    spots: {
      jiulong_guanyu: {
        name: '九龙灌浴',
        narration: '眼前的九龙灌浴把佛教故事转化为动态景观。九龙、莲花、太子佛与水景会随音乐开合升降，适合稍微退后观看完整的空间层次。',
        tags: ['动态音乐群雕', '佛陀诞生故事', '莲花开合 · 九龙喷水']
      },
      lingshan_buddha: {
        name: '灵山大佛',
        narration: '来到灵山大佛，先从远处看整体。通高 88 米的青铜立像背靠灵山、面向太湖，造像、山势与游览轴线共同形成庄严而开阔的空间。接下来我们再走近观察莲花座与衣纹细节。',
        resume: '了解了远观的原因，我们继续走近莲花座，看看造像细部如何延续整体的庄严感。',
        tags: ['通高 88 米', '青铜释迦牟尼立像', '山水与游览轴线'],
        audio: '../../assets/audio/competition/guide-lingshan.wav'
      }
    },
    privateAssist: {
      tourist: '游客 B',
      publicAction: '公共频道保持安静',
      privateAction: '已转入私人服务',
      leaderAction: '领队收到“游客需要协助”提醒',
      privacy: '完整健康描述不进入公共频道'
    },
    profile: {
      name: '长者友好模式',
      tags: ['历史文化', '体力偏低', '需要休息点'],
      changes: [
        { icon: 'speed', label: '讲解语速', value: '0.85×' },
        { icon: 'text_fields', label: '字幕字号', value: '大号' },
        { icon: 'accessible', label: '路线强度', value: '轻松' },
        { icon: 'chair', label: '休息安排', value: '每 25 分钟' }
      ],
      narration: '我会放慢讲解速度，优先安排坡度较缓的路段，并在每段游览之间提醒休息。'
    },
    leaderRoom: {
      code: 'LS2026',
      route: '长者友好文化线',
      online: '4 人在线',
      current: '灵山大佛 · 第 3 / 5 站',
      members: [
        { name: '陈阿姨', state: '跟随中', request: '' },
        { name: '游客 B', state: '需要协助', request: '1 条请求' },
        { name: '小林', state: '跟随中', request: '' },
        { name: '王叔叔', state: '稍后到达', request: '' }
      ],
      stops: ['大照壁', '九龙灌浴', '灵山大佛', '休息驿站', '灵山梵宫']
    },
    leaderControl: {
      spot: '灵山大佛',
      action: '讲解正在同步到 4 位游客',
      commands: [
        { icon: 'pause', label: '暂停 / 继续' },
        { icon: 'skip_next', label: '跳至下一站' },
        { icon: 'swap_horiz', label: '切换景点' },
        { icon: 'campaign', label: '集合提醒' }
      ],
      request: '游客 B 需要就近休息协助',
      notice: '路线变化与讲解进度已同步',
      finish: '导览结束后统一生成游客行程回顾'
    },
    analytics: {
      metrics: [
        { label: '今日服务', value: '328' },
        { label: '文字 / 语音', value: '186 / 92' },
        { label: '图片识景', value: '31' },
        { label: '路线推荐', value: '19' }
      ],
      trend: [26, 41, 58, 47, 76, 91, 82],
      questions: [
        { text: '灵山大佛为什么高 88 米？', count: '46 次' },
        { text: '最近的休息点在哪里？', count: '31 次' },
        { text: '梵宫建议参观多久？', count: '24 次' }
      ],
      satisfaction: '96.8%',
      rooms: '6 个同行小队',
      topics: ['休息设施', '排队时间', '文化讲解']
    },
    knowledgeBase: {
      count: '128 份',
      categories: ['全部资料', '讲解词', '文史资料', '常见问题'],
      docs: [
        { name: '灵山大佛讲解词.md', category: '讲解词', status: '可用' },
        { name: '梵宫建筑资料.pdf', category: '文史资料', status: '可用' },
        { name: '游客服务设施.json', category: '服务信息', status: '已更新' },
        { name: '高频问题与答复.md', category: '常见问题', status: '待复核' }
      ],
      actions: ['搜索与分类筛选', '上传 TXT / MD / JSON / PDF', '编辑、删除与重新整理']
    },
    avatarStudio: {
      selected: '形象 A · 清朗中性',
      outfit: '景区文化 · 朱红',
      voice: '温暖女声',
      speed: '0.9×',
      expression: '亲切',
      switches: ['口型同步', '表情变化', '眨眼与待机动作'],
      preview: '欢迎来到灵山胜境，让我陪你了解这里的故事。',
      audio: '../../assets/audio/competition/avatar-preview.wav'
    },
    operations: {
      metrics: [
        { label: '知识引用覆盖', value: '96%' },
        { label: '隐私误播', value: '0 次' },
        { label: '风险提醒召回', value: '100%' }
      ],
      gapQuestion: '“88 米”是否有确定的数字寓意？',
      gapStatus: '资料依据不足 · 已转人工审核',
      suggestion: '补充官方讲解词后再开放确定性回答'
    },
    passport: {
      title: '我的灵山文化护照',
      subtitle: '长者友好文化线 · 2026 夏',
      stats: [
        { value: '4', label: '文化景点' },
        { value: '2', label: '深度问答' },
        { value: '1.5km', label: '步行距离' }
      ],
      badge: '山水观佛 · 初章',
      note: '已为你保存今天的路线、问答与文化知识卡。'
    },
    steps: [
      { id: 'qa', label: '可信知识问答', duration: 7600 },
      { id: 'vision-symbol', label: '细节识图·千辐轮相', duration: 7200 },
      { id: 'vision-building', label: '建筑识图·五印坛城', duration: 7200 },
      { id: 'route', label: '长者友好路线', duration: 7000 },
      { id: 'route-event', label: '客流事件动态改线', duration: 7600 },
      { id: 'guide', label: '数字人自动讲解', duration: 8000 },
      { id: 'interrupt', label: '打断问答与自然续讲', duration: 8500 },
      { id: 'leader-room', label: '团长端·小队与路线', duration: 7600 },
      { id: 'leader-control', label: '团长端·讲解控制', duration: 7600 },
      { id: 'private-assist', label: '私人需求安全分流', duration: 7600 },
      { id: 'profile', label: '长者友好模式切换', duration: 7000 },
      { id: 'admin-analytics', label: '管理端·运营分析', duration: 7600 },
      { id: 'admin-kb', label: '管理端·知识库管理', duration: 7600 },
      { id: 'operations', label: '运营知识闭环', duration: 7000 },
      { id: 'admin-avatar', label: '管理端·讲解形象', duration: 7600 },
      { id: 'passport', label: '生成文化护照', duration: 6500 }
    ]
  });
})();
