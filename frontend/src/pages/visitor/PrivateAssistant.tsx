import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiGetPrivateMessages, apiSendPrivateQuestion, apiNotifyLeader } from '../../api/mock';
import type { ChatMessage } from '../../api/types';

export default function PrivateAssistant() {
  const navigate = useNavigate();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [showNotifyBtn, setShowNotifyBtn] = useState<string | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const userId = 'user_001';
  const nickname = '游客A';

  useEffect(() => {
    apiGetPrivateMessages(userId).then((msgs) => {
      if (msgs.length === 0) {
        setMessages([{
          msgId: 'welcome', roomId: 'room_001', userId: 'ai', nickname: 'AI 导览',
          channel: 'private', role: 'ai',
          text: '你好！我是你的私人导览助理。你可以随时问我卫生间位置、休息区、路线调整等问题，也可以请我讲慢一点或推荐少走路的路线。你的问题不会被公开到公共频道。',
          createdAt: new Date().toISOString(),
        }]);
      } else {
        setMessages(msgs);
      }
    });
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || sending) return;
    setSending(true);
    const question = input.trim();
    setInput('');

    const response = await apiSendPrivateQuestion(question, userId, nickname);
    const updatedMessages = await apiGetPrivateMessages(userId);
    setMessages(updatedMessages);

    if (response.needLeaderConfirm) {
      setShowNotifyBtn(response.suggestedLeaderMessage);
    }
    setSending(false);
  };

  const handleNotify = async () => {
    await apiNotifyLeader('pr_001');
    setShowNotifyBtn(null);
    setMessages((prev) => [...prev, {
      msgId: 'sys_' + Date.now(), roomId: 'room_001', userId: 'system', nickname: '',
      channel: 'private', role: 'system',
      text: '✅ 已通知团长 POST /api/rooms/{roomId}/notify-leader',
      createdAt: new Date().toISOString(),
    }]);
  };

  return (
    <>
      <div className="page" style={{ padding: 0, display: 'flex', flexDirection: 'column', height: '100dvh' }}>
        <div className="page-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
            <button
              onClick={() => navigate('/visitor/join')}
              style={{ background: 'none', border: 'none', fontSize: 20, cursor: 'pointer', padding: '4px 6px', borderRadius: 8 }}
            >← 退出</button>
          </div>
          <div className="flex-between">
            <div>
              <h1>💬 私人导览助理</h1>
              <p className="subtitle">你的专属 AI 助手 · 对话保密</p>
            </div>
          </div>
        </div>

        <div style={{ flex: 1, overflow: 'auto', padding: '12px 16px' }}>
          <div className="chat-container">
            {messages.map((msg) => (
              <div key={msg.msgId} className={`message ${msg.role === 'user' ? 'user' : msg.role === 'system' ? 'system' : 'ai'}`}>
                {msg.role !== 'system' && <span className="msg-sender">{msg.nickname}</span>}
                <div className="msg-bubble">{msg.text}</div>
                <span className="msg-time">
                  {new Date(msg.createdAt).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
            ))}

            {showNotifyBtn && (
              <div style={{ marginTop: 8, padding: 12, background: '#fffbeb', borderRadius: 10, border: '1px solid #fde68a' }}>
                <p style={{ fontSize: 13, marginBottom: 8 }}>⚠️ {showNotifyBtn}</p>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button className="btn btn-warning btn-sm" onClick={handleNotify}>通知团长</button>
                  <button className="btn btn-outline btn-sm" onClick={() => setShowNotifyBtn(null)}>暂不通知</button>
                </div>
              </div>
            )}

            <div ref={chatEndRef} />
          </div>
        </div>

        <div style={{ padding: '8px 16px', display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {['厕所在哪里？', '我有点累，附近能休息吗？', '老人走不动了，能少走一点吗？', '我没听懂，能再讲慢一点吗？', '我想提前离队自己走'].map((q) => (
            <button key={q} className="btn btn-outline btn-sm" onClick={() => setInput(q)} style={{ fontSize: 12 }}>{q}</button>
          ))}
        </div>

        <div className="chat-input-area">
          <input
            className="input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder={sending ? 'AI 正在回答...' : '私密提问，不会公开到群聊...'}
            disabled={sending}
          />
          <button className="btn btn-primary btn-sm" onClick={handleSend} disabled={sending || !input.trim()}>发送</button>
        </div>
      </div>
    </>
  );
}
