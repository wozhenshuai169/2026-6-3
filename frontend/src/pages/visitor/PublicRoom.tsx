import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import DigitalHuman from '../../components/DigitalHuman';
import {
  apiGetTourState, apiGetAvatarState, apiSendPublicQuestion,
  apiSendVoiceQuestion, apiGetRoomState,
  apiRecommendRoute, apiVisionRecognize,
  apiGetMemberMessages, apiSendMemberMessage, apiGetUnreadCounts, apiMarkRead,
} from '../../api/mock';
import type { TourState, AvatarState, AIStatus, RoomState, RouteRecommendResponse, VisionResponse } from '../../api/types';

// ---- types ----
interface TextMsg { id: string; role: 'ai' | 'user'; text: string; }

interface MemberMsg {
  msgId: string; fromUserId: string; toUserId: string; text: string; createdAt: string;
}

type RightView = 'members' | 'route' | 'vision' | 'feedback' | 'privateChat';

interface MenuItem { key: RightView; icon: string; label: string; desc: string; }

const MENU_ITEMS: MenuItem[] = [
  { key: 'members', icon: '🧑‍🤝‍🧑', label: '查看成员', desc: '查看房间成员并私聊' },
  { key: 'route', icon: '🗺️', label: '路线推荐', desc: '根据偏好推荐游览路线' },
  { key: 'vision', icon: '📸', label: '图片识景', desc: '拍照识别景点或展品' },
  { key: 'feedback', icon: '⭐', label: '满意度反馈', desc: '对本次导览进行评价' },
];

const myUserId = 'user_001';
const myNickname = '游客A';

// ---- helpers ----
function sortMembers(members: { userId: string; userName: string }[]) {
  return [...members].sort((a, b) => {
    if (a.userId === 'leader_001') return -1;
    if (b.userId === 'leader_001') return 1;
    return 0;
  });
}

export default function PublicRoom() {
  const navigate = useNavigate();

  // Left panel
  const [isMuted, setIsMuted] = useState(false);
  const [isTextMode, setIsTextMode] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [textMessages, setTextMessages] = useState<TextMsg[]>([
    { id: '0', role: 'ai', text: '大家现在看到的是主展厅，它位于灵境古苑中轴线的核心位置，也是理解整座古苑历史的起点。主展厅始建于明代，清代修缮后保留了较完整的空间格局。' },
  ]);
  const [textInput, setTextInput] = useState('');

  // Right panel
  const [rightView, setRightView] = useState<RightView>('members');
  const [showMenu, setShowMenu] = useState(false);
  const [roomState, setRoomState] = useState<RoomState | null>(null);
  const [tourState, setTourState] = useState<TourState | null>(null);
  const [avatar, setAvatar] = useState<AvatarState | null>(null);
  const [sending, setSending] = useState(false);

  // Private chat
  const [slideBack, setSlideBack] = useState(false);
  const [chatTarget, setChatTarget] = useState<{ userId: string; userName: string } | null>(null);
  const [memberMsgs, setMemberMsgs] = useState<MemberMsg[]>([]);
  const [memberInput, setMemberInput] = useState('');
  const [unreadCounts, setUnreadCounts] = useState<Record<string, number>>({});

  // Route / Vision
  const [routeResult, setRouteResult] = useState<RouteRecommendResponse | null>(null);
  const [visionResult, setVisionResult] = useState<VisionResponse | null>(null);

  // Refs
  const memberEndRef = useRef<HTMLDivElement>(null);

  // ---- effects ----
  useEffect(() => {
    apiGetTourState().then(setTourState);
    apiGetAvatarState().then(setAvatar);
    apiGetRoomState().then(setRoomState);
    const poll = setInterval(() => {
      apiGetAvatarState().then(setAvatar);
      apiGetRoomState().then(setRoomState);
      apiGetUnreadCounts(myUserId).then(setUnreadCounts);
    }, 3000);
    return () => clearInterval(poll);
  }, []);

  useEffect(() => { memberEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [memberMsgs]);

  // ---- left panel handlers ----
  const handleToggleMute = () => setIsMuted(!isMuted);
  const handleToggleMode = () => setIsTextMode((prev) => !prev);

  const handleVoiceRecord = async () => {
    if (isRecording) return;
    setIsRecording(true);
    if (isTextMode) {
      setTextInput('这个建筑是什么时候建的？');
    } else {
      const result = await apiSendVoiceQuestion(myUserId, 'public');
      setTextMessages((prev) => [...prev, { id: 'ai_' + Date.now(), role: 'ai', text: result.answer + '\n\n' + result.resumeText }]);
      setAvatar({ aiStatus: 'speaking', emotion: 'friendly', action: 'speaking', text: result.answer, audioUrl: result.audioUrl });
    }
    setIsRecording(false);
  };

  const handleTextSend = async () => {
    if (!textInput.trim() || sending) return;
    const q = textInput.trim();
    setTextInput('');
    setSending(true);
    setTextMessages((prev) => [...prev, { id: 'u_' + Date.now(), role: 'user', text: q }]);
    const result = await apiSendPublicQuestion(q, myUserId, myNickname);
    setTextMessages((prev) => [...prev, { id: 'ai_' + Date.now(), role: 'ai', text: result.answer + '\n\n🔄 ' + result.resumeText }]);
    setAvatar(await apiGetAvatarState());
    setSending(false);
  };

  // ---- member private chat ----
  const handleMemberClick = async (member: { userId: string; userName: string }) => {
    if (member.userId === myUserId) return;
    setSlideBack(false);
    setChatTarget(member);
    setRightView('privateChat');
    const msgs = await apiGetMemberMessages(myUserId, member.userId);
    setMemberMsgs(msgs);
    await apiMarkRead(myUserId, member.userId);
    setUnreadCounts(await apiGetUnreadCounts(myUserId));
  };

  const handleMemberSend = async () => {
    if (!memberInput.trim() || !chatTarget) return;
    const text = memberInput.trim();
    setMemberInput('');
    await apiSendMemberMessage(myUserId, chatTarget.userId, text);
    setMemberMsgs(await apiGetMemberMessages(myUserId, chatTarget.userId));
  };

  const handleMemberVoice = async () => {
    if (!chatTarget) return;
    // Simulate voice-to-text
    const asrText = '好的，我知道了。';
    await apiSendMemberMessage(myUserId, chatTarget.userId, asrText);
    setMemberMsgs(await apiGetMemberMessages(myUserId, chatTarget.userId));
  };

  const handleBackFromChat = () => {
    setSlideBack(true);
    setChatTarget(null);
    setMemberMsgs([]);
    setRightView('members');
  };

  // ============================================
  return (
    <div className="landscape-room">
      {/* ===== LEFT PANEL ===== */}
      {!isTextMode ? (
        <DigitalHuman
          aiStatus={(avatar?.aiStatus || 'idle') as AIStatus}
          spotName={tourState?.currentSpotName || '主展厅'}
          onlineUsers={tourState?.onlineUsers || 3}
          isMuted={isMuted}
          isTextMode={isTextMode}
          isRecording={isRecording}
          onToggleMute={handleToggleMute}
          onToggleMode={handleToggleMode}
          onVoiceRecord={handleVoiceRecord}
        />
      ) : (
        <div className="text-chat-panel">
          <div className="text-chat-header">
            <span className="dh-spot">📍 {tourState?.currentSpotName || '主展厅'}</span>
            <span className="dh-online">👥 {tourState?.onlineUsers || 3} 在线</span>
          </div>
          <div className="text-chat-messages">
            {textMessages.map((msg) => (
              <div key={msg.id} className={`text-msg ${msg.role === 'user' ? 'user' : 'ai'}`}>
                <span className="text-msg-role">{msg.role === 'ai' ? '🤖 小灵' : '👤 你'}</span>
                <div className="text-msg-bubble">{msg.text}</div>
              </div>
            ))}
          </div>
          <div className="text-chat-input">
            <input className="input" value={textInput} onChange={(e) => setTextInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleTextSend()}
              placeholder={sending ? 'AI 回答中...' : '打字或语音转文字...'} disabled={sending} />
            <button className="btn btn-primary btn-sm" onClick={handleTextSend} disabled={sending || !textInput.trim()}>发送</button>
          </div>
          <div className="dh-controls bottom">
            <button className={`dh-ctrl-btn ${isMuted ? 'off' : ''}`} onClick={handleToggleMute}>
              <span className="dh-ctrl-icon">{isMuted ? '🔇' : '🔊'}</span>
              <span className="dh-ctrl-label">{isMuted ? '已静音' : '播报中'}</span>
            </button>
            <button className={`dh-ctrl-btn mic large ${isRecording ? 'active' : ''}`} onMouseDown={handleVoiceRecord}>
              <span className="dh-ctrl-icon">🎤</span>
              <span className="dh-ctrl-label">{isRecording ? '识别中' : '语音转文字'}</span>
            </button>
            <button className="dh-ctrl-btn active" onClick={handleToggleMode}>
              <span className="dh-ctrl-icon">👤</span>
              <span className="dh-ctrl-label">数字人</span>
            </button>
          </div>
        </div>
      )}

      {/* ===== RIGHT PANEL ===== */}
      <div className="chat-panel">

        {/* ---- Members View ---- */}
        {rightView === 'members' && (
          <div className={`slide-view ${slideBack ? 'back' : ''}`}>
            <div className="chat-panel-header">
              <span>🧑‍🤝‍🧑 房间成员 · {roomState?.members.length || 4} 人</span>
              <button className="chat-exit-btn" onClick={() => navigate('/visitor/join')}>← 退出</button>
            </div>
            <div className="member-list">
              {sortMembers(roomState?.members || [
                { userId: 'leader_001', userName: '团长' },
                { userId: 'user_001', userName: '游客A（我）' },
                { userId: 'user_002', userName: '游客B' },
                { userId: 'user_003', userName: '游客C' },
              ]).map((m) => (
                <button
                  key={m.userId}
                  className={`member-item ${m.userId === myUserId ? 'me' : ''}`}
                  onClick={() => handleMemberClick(m)}
                  disabled={m.userId === myUserId}
                  style={{ width: '100%', textAlign: 'left', fontFamily: 'inherit', cursor: m.userId === myUserId ? 'default' : 'pointer' }}
                >
                  <div className="member-avatar">{m.userName.charAt(0)}</div>
                  <div className="member-info">
                    <span className="member-name">
                      {m.userName}
                      {m.userId === myUserId && <span className="member-me-tag">我</span>}
                      {m.userId === 'leader_001' && <span className="member-leader-tag">团长</span>}
                    </span>
                  </div>
                  {m.userId !== myUserId && (unreadCounts[m.userId] || 0) > 0 && (
                    <span className="member-badge">{unreadCounts[m.userId]}</span>
                  )}
                  <span className="member-arrow">→</span>
                </button>
              ))}
            </div>

            {/* ---- Menu ---- */}
            <div className="menu-area">
              {showMenu && (
                <div className="menu-drawer">
                  {MENU_ITEMS.map((item) => (
                    <button key={item.key} className="menu-item-btn"
                      onClick={() => { setRightView(item.key); setShowMenu(false); }}>
                      <span className="menu-item-icon">{item.icon}</span>
                      <div className="menu-item-text">
                        <span className="menu-item-label">{item.label}</span>
                        <span className="menu-item-desc">{item.desc}</span>
                      </div>
                      <span className="menu-item-arrow">→</span>
                    </button>
                  ))}
                </div>
              )}
              <button className="menu-toggle-btn" onClick={() => setShowMenu(!showMenu)}>
                <span>{showMenu ? '✕' : '📋'}</span>
                <span>{showMenu ? '关闭菜单' : '功能菜单'}</span>
              </button>
            </div>
          </div>
        )}

        {/* ---- Private Chat ---- */}
        {rightView === 'privateChat' && chatTarget && (
          <div className={`slide-view ${slideBack ? 'back' : ''}`}>
            <div className="chat-panel-header">
              <span>💬 {chatTarget.userName}</span>
              <button className="chat-exit-btn" onClick={handleBackFromChat}>← 返回</button>
            </div>
            <div className="chat-panel-messages">
              {memberMsgs.map((msg) => (
                <div key={msg.msgId} className={`land-message ${msg.fromUserId === myUserId ? 'user' : 'ai'}`}>
                  <span className="land-msg-sender">
                    {msg.fromUserId === myUserId ? '👤 我' : '👤 ' + chatTarget.userName}
                  </span>
                  <div className="land-msg-bubble">{msg.text}</div>
                </div>
              ))}
              <div ref={memberEndRef} />
            </div>
            <div className="chat-panel-input">
              <input className="input" value={memberInput} onChange={(e) => setMemberInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleMemberSend()}
                placeholder="输入消息..." style={{ fontSize: 12, padding: '8px 12px' }} />
              <button className="btn btn-primary btn-sm" onClick={handleMemberSend} disabled={!memberInput.trim()}>发送</button>
              <button className="voice-btn" onMouseDown={handleMemberVoice} title="语音转文字" style={{ minWidth: 40, minHeight: 40, fontSize: 14 }}>🎤</button>
            </div>
          </div>
        )}

        {/* ---- Route ---- */}
        {rightView === 'route' && (
          <>
            <div className="chat-panel-header">
              <span>🗺️ 路线推荐</span>
              <button className="chat-exit-btn" onClick={() => { setRightView('members'); setRouteResult(null); }}>← 返回</button>
            </div>
            <div className="route-panel">
              <p className="route-intro">根据你的偏好，AI 为你推荐最佳游览路线</p>
              <div className="route-btns">
                {[
                  { label: '经典中轴线 (60分钟)', pref: {} },
                  { label: '轻松短线 (35分钟)', pref: { withElderly: true } },
                  { label: '亲子友好 (35分钟)', pref: { withChildren: true } },
                  { label: '历史深读线 (80分钟)', pref: { interest: ['历史'] } },
                ].map((opt) => (
                  <button key={opt.label} className="btn btn-outline btn-sm" style={{ marginBottom: 6 }}
                    onClick={async () => {
                      const r = await apiRecommendRoute({
                        interest: opt.pref.interest || ['历史'], timeLimit: 60, physicalStrength: 'medium',
                        withChildren: opt.pref.withChildren || false, withElderly: opt.pref.withElderly || false, avoidCrowd: false,
                      });
                      setRouteResult(r);
                    }}>{opt.label}</button>
                ))}
              </div>
              {routeResult && (
                <div className="route-result">
                  <h4>📌 {routeResult.routeName} · 约 {routeResult.estimatedTime} 分钟</h4>
                  <div className="route-tags">
                    {routeResult.difficulty && <span className={`route-tag ${routeResult.difficulty}`}>体力: {routeResult.difficulty === 'low' ? '轻松' : routeResult.difficulty === 'medium' ? '适中' : '较高'}</span>}
                    {routeResult.suitableForChildren && <span className="route-tag green">👶 亲子友好</span>}
                    {routeResult.suitableForElderly && <span className="route-tag green">👴 老人友好</span>}
                  </div>
                  <ol className="route-spots">{routeResult.spots.map((s, i) => (
                    <li key={i}><strong>{s.spotName}</strong> — 停留 {s.stayMinutes} 分钟</li>
                  ))}</ol>
                  <p className="route-reason">💡 {routeResult.reason}</p>
                  {routeResult.scoreBreakdown && (
                    <div className="route-scores">
                      {Object.entries(routeResult.scoreBreakdown).map(([k, v]) => (
                        <span key={k} className="score-item">{k}: +{v}</span>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </>
        )}

        {/* ---- Vision ---- */}
        {rightView === 'vision' && (
          <>
            <div className="chat-panel-header">
              <span>📸 图片识景</span>
              <button className="chat-exit-btn" onClick={() => { setRightView('members'); setVisionResult(null); }}>← 返回</button>
            </div>
            <div className="vision-panel">
              <div className="upload-area" onClick={async () => {
                const r = await apiVisionRecognize('/mock/photo.jpg', tourState?.currentSpotId);
                setVisionResult(r);
              }}>
                <div className="upload-icon">📷</div>
                <p><strong>点击拍照或上传图片</strong></p>
                <p>AI 将识别景点并生成讲解</p>
              </div>
              {visionResult && (
                <div className="vision-result">
                  <h4>📍 识别结果：{visionResult.recognizedSpot.spotName}</h4>
                  <p className="vision-confidence">置信度：{(visionResult.recognizedSpot.confidence * 100).toFixed(0)}%</p>
                  {visionResult.visualFeatures && visionResult.visualFeatures.length > 0 && (
                    <div className="vision-features">
                      {visionResult.visualFeatures.map((f) => <span key={f} className="feature-tag">🏷️ {f}</span>)}
                    </div>
                  )}
                  <p>{visionResult.description}</p>
                  {visionResult.relatedSpots.length > 0 && (
                    <div className="related-spots">
                      <span>🗺️ 周边景点：</span>
                      {visionResult.relatedSpots.map((s) => <span key={s.spotId} className="related-tag">{s.spotName}</span>)}
                    </div>
                  )}
                </div>
              )}
            </div>
          </>
        )}

        {/* ---- Feedback ---- */}
        {rightView === 'feedback' && (
          <>
            <div className="chat-panel-header">
              <span>⭐ 满意度反馈</span>
              <button className="chat-exit-btn" onClick={() => setRightView('members')}>← 返回</button>
            </div>
            <div className="feedback-panel">
              <p className="feedback-intro">请对本次导览体验进行评价</p>
              <div className="feedback-stars">
                {[1, 2, 3, 4, 5].map((s) => <button key={s} className="feedback-star-btn">☆</button>)}
              </div>
              <textarea className="feedback-textarea" placeholder="有什么想说的？（选填）" rows={3} />
              <button className="btn btn-primary btn-block">提交反馈</button>
            </div>
          </>
        )}

      </div>
    </div>
  );
}
