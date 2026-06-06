import type {
  RegisterResponse,
  CreateRoomResponse,
  JoinRoomResponse,
  RoomState,
  UpdateSpotResponse,
  AvatarState,
  VoiceQuestionResponse,
  ASRResponse,
  TTSResponse,
  VisionResponse,
  RouteRecommendResponse,
  ChatMessage,
  KnowledgeDoc,
  DashboardSummary,
  ChatLog,
  PrivateRequest,
  TourState,
} from './types';

const delay = (ms = 400) => new Promise((r) => setTimeout(r, ms));

// ============ In-memory State ============

let users: Record<string, { userId: string; userName: string; token: string }> = {};
let currentUser: { userId: string; userName: string; token: string } | null = null;
let roomId = 'room_001';
let roomPassword = '';

let currentSpot = 'main_hall';
const spotNames: Record<string, string> = {
  main_hall: '主展厅', bell_tower: '钟楼', drum_tower: '鼓楼',
  courtyard: '中心庭院', stone_gallery: '石刻长廊',
  service_center: '游客服务中心', east_gate: '东门出口',
};

let avatarState: AvatarState = {
  aiStatus: 'speaking',
  emotion: 'friendly',
  action: 'speaking',
  text: '大家现在看到的是主展厅，它位于景区中轴线的核心位置，也是理解整座古苑历史的起点。主展厅始建于明代，清代修缮后保留了较完整的空间格局，所以我们能同时看到历史层次和地方工艺。',
  audioUrl: '/mock/audio/welcome.mp3',
};

let tourState: TourState = {
  roomId: 'room_001',
  currentSpotId: 'main_hall',
  currentSpotName: '主展厅',
  currentScriptSegment: 'segment_01',
  resumePoint: '正在介绍主展厅历史背景',
  aiStatus: 'speaking',
  tourStage: 'explaining',
  nextSpotId: 'courtyard',
  onlineUsers: 3,
  pendingPrivateRequests: 1,
};

const messages: ChatMessage[] = [
  { msgId: 'msg_001', roomId: 'room_001', userId: 'ai', nickname: 'AI 导览', channel: 'public', role: 'ai',
    text: '大家现在看到的是主展厅，它位于景区中轴线的核心位置，也是理解整座古苑历史的起点。主展厅始建于明代，清代修缮后保留了较完整的空间格局。请抬头看屋顶，灰瓦、脊兽和木构件的组合，体现了本地传统建筑对礼制和实用性的平衡。', createdAt: new Date(Date.now() - 300000).toISOString() },
  { msgId: 'msg_002', roomId: 'room_001', userId: 'user_001', nickname: '游客A', channel: 'public', role: 'user',
    text: '主展厅是什么时候建的？', createdAt: new Date(Date.now() - 120000).toISOString() },
  { msgId: 'msg_003', roomId: 'room_001', userId: 'ai', nickname: 'AI 导览', channel: 'public', role: 'ai',
    text: '主展厅始建于明代，清代曾进行修缮，是景区保存较完整的礼制建筑。刚才我们讲到它的历史沿革，接下来继续看屋顶装饰中的地方工艺特色。', createdAt: new Date(Date.now() - 100000).toISOString() },
];

const privateMessages: Record<string, ChatMessage[]> = {};
const knowledgeDocs: KnowledgeDoc[] = [
  { docId: 'doc_001', fileName: '灵境古苑讲解手册.txt', fileType: 'txt', scenicAreaId: 'scenic_001', uploadAt: '2026-05-01', status: 'ready' },
  { docId: 'doc_002', fileName: '灵境古苑建筑资料.md', fileType: 'md', scenicAreaId: 'scenic_001', uploadAt: '2026-05-01', status: 'ready' },
  { docId: 'doc_003', fileName: '景区公告及游客服务信息.txt', fileType: 'txt', scenicAreaId: 'scenic_001', uploadAt: '2026-05-01', status: 'ready' },
  { docId: 'doc_004', fileName: '讲解段落脚本.json', fileType: 'json', scenicAreaId: 'scenic_001', uploadAt: '2026-05-01', status: 'ready' },
];
const chatLogs: ChatLog[] = [
  { logId: 'log_001', roomId: 'room_001', userId: 'user_001', channel: 'public', question: '这个建筑是什么时候建的？', answer: '这个建筑始建于明代嘉靖年间...', intent: 'spot_history', decision: 'interrupt_and_answer', knowledgeHit: true, createdAt: '2026-06-03T09:30:00' },
  { logId: 'log_002', roomId: 'room_001', userId: 'user_002', channel: 'private', question: '我有点累，附近有休息区吗？', answer: '最近的休息区在主展厅右侧出口附近...', intent: 'facility_question', decision: 'private_reply', knowledgeHit: true, createdAt: '2026-06-03T09:35:00' },
];
const privateRequests: PrivateRequest[] = [
  { id: 'pr_001', roomId: 'room_001', userId: 'user_002', nickname: '游客B', content: '我有点累，附近有休息区吗？', aiReply: '最近的休息区在主展厅右侧出口附近，步行约120米。', needLeaderConfirm: true, status: 'pending', createdAt: '2026-06-03T09:35:00' },
];

// ============ Auth ============

export async function apiRegister(userName: string, _password: string): Promise<RegisterResponse> {
  await delay(300);
  const userId = 'user_' + Date.now();
  const token = 'tok_' + Math.random().toString(36).slice(2, 16);
  const user = { userId, userName, token };
  users[userId] = user;
  currentUser = user;
  return { userId, userName, token };
}

// ============ Room ============

export async function apiCreateRoom(_roomName: string, password?: string): Promise<CreateRoomResponse> {
  await delay();
  roomId = 'room_001';
  roomPassword = password || '';
  return { roomId, status: 'created' };
}

export async function apiVerifyRoomPassword(password: string): Promise<boolean> {
  await delay(300);
  return password === roomPassword;
}

export async function apiRoomHasPassword(): Promise<boolean> {
  await delay(200);
  return roomPassword !== '';
}

export async function apiGetRoomState(): Promise<RoomState> {
  await delay(200);
  return {
    roomId,
    members: [
      { userId: 'leader_001', userName: '团长' },
      { userId: 'user_001', userName: '游客A' },
      { userId: 'user_002', userName: '游客B' },
      { userId: 'user_003', userName: '游客C' },
    ],
    currentSpot,
    status: 'active',
  };
}

export async function apiJoinRoom(): Promise<JoinRoomResponse> {
  await delay();
  const userId = currentUser?.userId || 'user_001';
  return { roomId, userId, status: 'joined' };
}

export async function apiUpdateCurrentSpot(spotId: string): Promise<UpdateSpotResponse> {
  await delay();
  currentSpot = spotId;
  tourState = { ...tourState, currentSpotId: spotId, currentSpotName: spotNames[spotId] || spotId };
  return { roomId, currentSpot: spotId, status: 'updated' };
}

// ============ Digital Human (Avatar State) ============

export async function apiGetAvatarState(): Promise<AvatarState> {
  await delay(150);
  return { ...avatarState };
}

export async function apiSetAvatarState(partial: Partial<AvatarState>): Promise<void> {
  avatarState = { ...avatarState, ...partial };
}

// ============ AI Q&A ============

export async function apiSendPublicQuestion(
  question: string,
  userId: string,
  nickname: string,
): Promise<{ answer: string; resumeText: string }> {
  await delay(800);

  // Add user message
  messages.push({
    msgId: 'msg_' + Date.now(), roomId, userId, nickname, channel: 'public', role: 'user',
    text: question, createdAt: new Date().toISOString(),
  });

  // Update avatar to thinking then answering
  avatarState = { ...avatarState, aiStatus: 'thinking', emotion: 'thinking', action: 'thinking', text: '思考中...', audioUrl: '' };

  let answer: string;
  let resumeText: string;

  if (question.includes('建') || question.includes('时') || question.includes('历史')) {
    answer = '主展厅始建于明代，清代曾进行修缮，是景区保存较完整的礼制建筑，所以能同时看到历史层次和地方工艺。';
    resumeText = '刚才我们了解了主展厅的历史沿革，接下来请抬头看屋顶，灰瓦和脊兽体现了本地传统建筑工艺。';
  } else if (question.includes('屋顶') || question.includes('装饰') || question.includes('工艺')) {
    answer = '主展厅屋顶采用灰瓦和脊兽装饰，体现本地传统木作与瓦作工艺，兼具礼制和实用性的平衡。';
    resumeText = '了解了屋顶装饰的特色之后，我们继续看展厅内部的空间格局。';
  } else if (question.includes('开放') || question.includes('时间') || question.includes('几点')) {
    answer = '景区常规开放时间为9:00至17:30，重大节假日以当日公告为准。';
    resumeText = '回到导览，我们现在继续看主展厅的建筑特色。';
  } else if (question.includes('钟楼') || question.includes('报时')) {
    answer = '钟楼位于中轴线北侧，曾用于报时和礼仪活动，采用重檐结构，木构件连接处保留榫卯做法。';
    resumeText = '接下来我们从主展厅右侧廊道继续前往下一个景点。';
  } else {
    answer = '根据景区资料，' + question.replace('？', '').replace('吗', '') + '。如果你需要更详细的信息，可以在私人频道继续咨询。';
    resumeText = '刚才我们探讨了这个问题，现在继续回到主展厅的导览讲解。';
  }

  // Update avatar to speaking
  avatarState = {
    aiStatus: 'speaking', emotion: 'friendly', action: 'speaking',
    text: answer,
    audioUrl: '/mock/tts/answer_' + Date.now() + '.mp3',
  };

  // Add AI message
  const aiText = answer + ' ' + resumeText;
  messages.push({
    msgId: 'msg_' + (Date.now() + 1), roomId, userId: 'ai', nickname: 'AI 导览', channel: 'public', role: 'ai',
    text: aiText, sources: [{ title: '主展厅历史资料', chunkId: 'chunk_001' }],
    createdAt: new Date().toISOString(),
  });

  // Schedule resume
  setTimeout(() => {
    avatarState = {
      aiStatus: 'speaking', emotion: 'friendly', action: 'speaking',
      text: resumeText,
      audioUrl: '/mock/tts/resume_' + Date.now() + '.mp3',
    };
  }, 2500);

  return { answer, resumeText };
}

export async function apiSendVoiceQuestion(
  userId: string,
  channel: 'public' | 'private',
): Promise<VoiceQuestionResponse> {
  await delay(1500);

  const asrText = '这个建筑是什么时候建的？';
  const answer = '这个建筑始建于明代嘉靖年间（约1540年），清代乾隆年间曾进行过大规模修缮，融合了明清两代的建筑风格。';
  const resumeText = '刚才我们了解了这座建筑的建造年代，接下来继续看它屋顶上精美的装饰纹样。';

  messages.push({
    msgId: 'msg_' + Date.now(), roomId, userId, nickname: '游客A', channel, role: 'user',
    text: '🎤 ' + asrText, createdAt: new Date().toISOString(),
  });
  messages.push({
    msgId: 'msg_' + (Date.now() + 1), roomId, userId: 'ai', nickname: 'AI 导览', channel, role: 'ai',
    text: answer + ' ' + resumeText,
    sources: [{ title: '主展厅历史资料', chunkId: 'chunk_001' }],
    createdAt: new Date().toISOString(),
  });

  return {
    asrText,
    decision: 'interrupt_and_answer',
    answer,
    audioUrl: '/mock/tts/answer_' + Date.now() + '.mp3',
    resumeText,
    resumeAudioUrl: '/mock/tts/resume_' + Date.now() + '.mp3',
    sources: [{ title: '主展厅历史资料', chunkId: 'chunk_001' }],
  };
}

// ============ ASR / TTS ============

export async function apiASR(_channel: 'public' | 'private'): Promise<ASRResponse> {
  await delay(600);
  return { text: '这个建筑是什么时候建的？', confidence: 0.92 };
}

export async function apiTTS(text: string): Promise<TTSResponse> {
  await delay(400);
  return {
    audioUrl: '/mock/tts/tts_' + Date.now() + '.mp3',
    durationMs: text.length * 80,
  };
}

// ============ Vision ============

export async function apiVisionRecognize(_imageUrl: string, _currentSpotId?: string): Promise<VisionResponse> {
  await delay(1200);
  return {
    recognizedSpot: { spotId: 'bell_tower', spotName: '钟楼', confidence: 0.87 },
    description: '你拍到的是钟楼，位于中轴线北侧，曾用于报时和礼仪活动。钟楼采用重檐结构，木构件连接处保留榫卯做法，是观察传统建筑受力方式的好位置。',
    visualFeatures: ['木结构', '重檐', '钟鼓建筑'],
    relatedSpots: [{ spotId: 'drum_tower', spotName: '鼓楼' }],
  };
}

// ============ Route Recommendation ============

export async function apiRecommendRoute(preferences: { interest: string[]; timeLimit: number; physicalStrength: 'low' | 'medium' | 'high'; withChildren: boolean; withElderly: boolean; avoidCrowd: boolean }): Promise<RouteRecommendResponse> {
  await delay(800);
  const routes: Record<string, RouteRecommendResponse> = {
    elderly: {
      routeName: '轻松短线', estimatedTime: 35, difficulty: 'low', walkingDifficulty: 'low',
      suitableForChildren: true, suitableForElderly: true, distance: 0.8,
      matchedPreferences: ['老人友好', '少走路'],
      scoreBreakdown: { interest: 3, time: 2, stamina: 2, companion: 2, distance: 1 },
      spots: [
        { spotId: 'main_hall', spotName: '主展厅', stayMinutes: 10 },
        { spotId: 'courtyard', spotName: '中心庭院', stayMinutes: 10 },
        { spotId: 'service_center', spotName: '游客服务中心', stayMinutes: 10 },
        { spotId: 'east_gate', spotName: '东门出口', stayMinutes: 5 },
      ], reason: '步行距离最短，沿途有休息点和饮水设施，适合有老人同行的游客。东门靠近停车区。',
    },
    children: {
      routeName: '轻松短线', estimatedTime: 35, difficulty: 'low', walkingDifficulty: 'low',
      suitableForChildren: true, suitableForElderly: false, distance: 0.8,
      matchedPreferences: ['亲子友好', '节奏舒缓'],
      scoreBreakdown: { interest: 3, time: 2, stamina: 2, companion: 2, distance: 0 },
      spots: [
        { spotId: 'main_hall', spotName: '主展厅', stayMinutes: 10 },
        { spotId: 'courtyard', spotName: '中心庭院', stayMinutes: 15 },
        { spotId: 'service_center', spotName: '游客服务中心', stayMinutes: 10 },
      ], reason: '带儿童游客可在主展厅右侧领取亲子任务卡，庭院和服务中心为主要停留点，节奏舒缓。',
    },
    history: {
      routeName: '历史深读线', estimatedTime: 80, difficulty: 'high', walkingDifficulty: 'high',
      suitableForChildren: false, suitableForElderly: false, distance: 1.5,
      matchedPreferences: ['历史建筑', '深度讲解'],
      scoreBreakdown: { interest: 3, time: 2, stamina: 1, companion: 0, distance: 1 },
      spots: [
        { spotId: 'main_hall', spotName: '主展厅', stayMinutes: 20 },
        { spotId: 'bell_tower', spotName: '钟楼', stayMinutes: 20 },
        { spotId: 'drum_tower', spotName: '鼓楼', stayMinutes: 20 },
        { spotId: 'stone_gallery', spotName: '石刻长廊', stayMinutes: 20 },
      ], reason: '深度覆盖历史文化景点，包含钟楼榫卯结构、鼓楼展陈和石刻碑文，适合历史建筑爱好者。',
    },
    default: {
      routeName: '经典中轴线', estimatedTime: 60, difficulty: 'medium', walkingDifficulty: 'medium',
      suitableForChildren: true, suitableForElderly: false, distance: 1.2,
      matchedPreferences: ['历史文化', '建筑艺术'],
      scoreBreakdown: { interest: 3, time: 2, stamina: 2, companion: 1, distance: 1 },
      spots: [
        { spotId: 'main_hall', spotName: '主展厅', stayMinutes: 20 },
        { spotId: 'courtyard', spotName: '中心庭院', stayMinutes: 10 },
        { spotId: 'bell_tower', spotName: '钟楼', stayMinutes: 15 },
        { spotId: 'drum_tower', spotName: '鼓楼', stayMinutes: 15 },
      ], reason: '沿中轴线游览核心景点，体验一钟一鼓的传统格局，节奏适中适合首次游览。',
    },
  };

  let key = 'default';
  if (preferences.withElderly) key = 'elderly';
  else if (preferences.withChildren) key = 'children';
  else if (preferences.interest.includes('历史')) key = 'history';

  return routes[key];
}

// ============ Private Q&A ============

export async function apiSendPrivateQuestion(
  question: string,
  userId: string,
  nickname: string,
): Promise<{ answer: string; needLeaderConfirm: boolean; suggestedLeaderMessage: string }> {
  await delay(800);

  if (!privateMessages[userId]) privateMessages[userId] = [];
  privateMessages[userId].push({
    msgId: 'msg_p_' + Date.now(), roomId, userId, nickname, channel: 'private', role: 'user',
    text: question, createdAt: new Date().toISOString(),
  });

  let answer: string;
  let needLeaderConfirm = false;
  let suggestedLeaderMessage = '';

  if (question.includes('厕所') || question.includes('洗手间')) {
    answer = '最近的洗手间在主展厅左侧出口旁，步行约50米。';
  } else if (question.includes('累') || question.includes('休息')) {
    answer = '最近的休息区在主展厅右侧出口附近，步行约120米，那里有长椅和饮水机。';
    needLeaderConfirm = true;
    suggestedLeaderMessage = nickname + '表示身体疲劳，建议在主展厅右侧休息区短暂停留。';
  } else if (question.includes('走不动') || question.includes('老人')) {
    answer = '理解你的情况。建议你和同行老人在主展厅右侧休息区休息。需要我帮你通知团长调整后续路线吗？';
    needLeaderConfirm = true;
    suggestedLeaderMessage = nickname + '同行老人行动不便，建议在主展厅右侧休息区短暂停留。';
  } else if (question.includes('路线') || question.includes('怎么走')) {
    answer = '推荐你走"经典主路线"：主展厅 → 钟楼 → 后花园 → 文创商店，全程约1.5小时。';
  } else if (question.includes('小孩') || question.includes('孩子')) {
    answer = '推荐"亲子轻松线"：主展厅（互动展区）→ 中庭休息区 → 文创商店，全程约45分钟，步行距离短。';
  } else {
    answer = '已收到你的问题。根据当前导览信息，建议你可以在自由活动时间详细咨询。';
  }

  privateMessages[userId].push({
    msgId: 'msg_p_' + (Date.now() + 1), roomId, userId: 'ai', nickname: 'AI 导览', channel: 'private', role: 'ai',
    text: answer, createdAt: new Date().toISOString(),
  });

  if (needLeaderConfirm) {
    privateRequests.push({
      id: 'pr_' + Date.now(), roomId, userId, nickname,
      content: question, aiReply: answer,
      needLeaderConfirm: true, status: 'pending',
      createdAt: new Date().toISOString(),
    });
    tourState.pendingPrivateRequests = privateRequests.filter((r) => r.status === 'pending').length;
  }

  return { answer, needLeaderConfirm, suggestedLeaderMessage };
}

// ============ Member Private Chat ============

interface MemberMsg {
  msgId: string; fromUserId: string; toUserId: string; text: string; createdAt: string;
}

const memberMessages: MemberMsg[] = [];
const unreadCounts: Record<string, Record<string, number>> = {}; // userId -> { fromUserId: count }

export async function apiGetMemberMessages(myUserId: string, targetUserId: string): Promise<MemberMsg[]> {
  await delay(200);
  return memberMessages.filter(
    (m) => (m.fromUserId === myUserId && m.toUserId === targetUserId) ||
           (m.fromUserId === targetUserId && m.toUserId === myUserId)
  ).sort((a, b) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime());
}

export async function apiSendMemberMessage(fromUserId: string, toUserId: string, text: string): Promise<MemberMsg> {
  await delay(300);
  const msg: MemberMsg = { msgId: 'mm_' + Date.now(), fromUserId, toUserId, text, createdAt: new Date().toISOString() };
  memberMessages.push(msg);
  // Add unread for the recipient
  if (!unreadCounts[toUserId]) unreadCounts[toUserId] = {};
  unreadCounts[toUserId][fromUserId] = (unreadCounts[toUserId][fromUserId] || 0) + 1;
  return msg;
}

export async function apiGetUnreadCounts(userId: string): Promise<Record<string, number>> {
  await delay(100);
  return { ...(unreadCounts[userId] || {}) };
}

export async function apiMarkRead(userId: string, fromUserId: string): Promise<void> {
  if (unreadCounts[userId]) {
    unreadCounts[userId][fromUserId] = 0;
  }
}

// ============ Knowledge ============

export async function apiGetKnowledgeDocs(): Promise<KnowledgeDoc[]> {
  await delay();
  return [...knowledgeDocs];
}

export async function apiUploadKnowledge(fileName: string): Promise<KnowledgeDoc> {
  await delay(1000);
  const doc: KnowledgeDoc = {
    docId: 'doc_' + Date.now(), fileName,
    fileType: fileName.split('.').pop() || 'txt',
    scenicAreaId: 'scenic_001',
    uploadAt: new Date().toISOString().slice(0, 10),
    status: 'processing',
  };
  knowledgeDocs.push(doc);
  setTimeout(() => { doc.status = 'ready'; }, 3000);
  return doc;
}

// ============ Messages ============

export async function apiGetPublicMessages(): Promise<ChatMessage[]> {
  await delay(200);
  return [...messages];
}

export async function apiGetPrivateMessages(userId: string): Promise<ChatMessage[]> {
  await delay(200);
  return privateMessages[userId] || [];
}

// ============ Dashboard ============

export async function apiGetDashboard(): Promise<DashboardSummary> {
  await delay();
  return {
    todayQuestions: 24, publicQuestions: 18, privateQuestions: 6,
    knowledgeHitRate: 0.88,
    topQuestions: [
      { question: '这个建筑是什么时候建的？', count: 8 },
      { question: '附近有厕所吗？', count: 5 },
      { question: '接下来去哪里？', count: 4 },
      { question: '这里有什么特色？', count: 3 },
      { question: '有没有少走路路线？', count: 2 },
    ],
    onlineRooms: 3, onlineUsers: 12, avgSatisfaction: 4.2,
  };
}

export async function apiGetChatLogs(): Promise<ChatLog[]> {
  await delay();
  return [...chatLogs];
}

// ============ Tour State & Leader ============

export async function apiGetTourState(): Promise<TourState> {
  await delay(200);
  return { ...tourState };
}

export async function apiUpdateAIStatus(status: string): Promise<void> {
  await delay(200);
  tourState.aiStatus = status;
  avatarState.aiStatus = status as AvatarState['aiStatus'];
}

export async function apiGetPrivateRequests(): Promise<PrivateRequest[]> {
  await delay(200);
  return [...privateRequests];
}

export async function apiNotifyLeader(requestId: string): Promise<void> {
  await delay();
  const req = privateRequests.find((r) => r.id === requestId);
  if (req) { req.status = 'notified'; }
  tourState.pendingPrivateRequests = privateRequests.filter((r) => r.status === 'pending').length;
}

export async function apiResolvePrivateRequest(requestId: string): Promise<void> {
  await delay();
  const req = privateRequests.find((r) => r.id === requestId);
  if (req) { req.status = 'resolved'; }
  tourState.pendingPrivateRequests = privateRequests.filter((r) => r.status === 'pending').length;
}
