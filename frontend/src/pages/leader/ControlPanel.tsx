import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  apiCreateRoom, apiGetTourState, apiUpdateCurrentSpot, apiUpdateAIStatus,
  apiGetPrivateRequests, apiNotifyLeader, apiSetAvatarState,
} from '../../api/mock';
import type { TourState, PrivateRequest, AIStatus } from '../../api/types';

const SPOTS = [
  { id: 'main_hall', name: '主展厅' },
  { id: 'courtyard', name: '中心庭院' },
  { id: 'bell_tower', name: '钟楼' },
  { id: 'drum_tower', name: '鼓楼' },
  { id: 'stone_gallery', name: '石刻长廊' },
  { id: 'service_center', name: '游客服务中心' },
  { id: 'east_gate', name: '东门出口' },
];

export default function ControlPanel() {
  const navigate = useNavigate();
  const [roomCreated, setRoomCreated] = useState(false);
  const [roomName, setRoomName] = useState('主展厅导览团');
  const [roomPassword, setRoomPassword] = useState('');
  const [tourState, setTourState] = useState<TourState | null>(null);
  const [privateRequests, setPrivateRequests] = useState<PrivateRequest[]>([]);
  const [activeTab, setActiveTab] = useState<'control' | 'requests'>('control');
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    if (roomCreated) {
      apiGetTourState().then(setTourState);
      apiGetPrivateRequests().then(setPrivateRequests);
    }
  }, [roomCreated]);

  const handleCreateRoom = async () => {
    setCreating(true);
    await apiCreateRoom(roomName, roomPassword || undefined);
    // POST /api/rooms
    setRoomCreated(true);
    setCreating(false);
    apiGetTourState().then(setTourState);
    apiGetPrivateRequests().then(setPrivateRequests);
  };

  const handleUpdateSpot = async (spotId: string) => {
    // POST /api/rooms/{roomId}/current-spot
    await apiUpdateCurrentSpot(spotId);
    setTourState(await apiGetTourState());
  };

  const handleAIStatus = async (status: AIStatus) => {
    await apiUpdateAIStatus(status);
    await apiSetAvatarState({ aiStatus: status, action: status });
    setTourState(await apiGetTourState());
  };

  const handleResolveRequest = async (requestId: string) => {
    await apiNotifyLeader(requestId);
    setPrivateRequests(await apiGetPrivateRequests());
    setTourState(await apiGetTourState());
  };

  const pendingCount = privateRequests.filter((r) => r.status === 'pending').length;

  if (!roomCreated) {
    return (
      <>
        <div className="page join-room">
          <div style={{ position: 'absolute', top: 16, left: 16 }}>
            <button
              onClick={() => navigate('/')}
              style={{ background: 'none', border: 'none', fontSize: 20, cursor: 'pointer', padding: '4px 8px' }}
            >← 返回</button>
          </div>
          <div style={{ fontSize: 48, marginBottom: 16 }}>🎛️</div>
          <h2>团长控制台</h2>
          <p className="text-secondary">创建导览房间 POST /api/rooms</p>
          <div className="join-card" style={{ marginTop: 24 }}>
            <div className="input-group">
              <label>房间名称</label>
              <input className="input" value={roomName} onChange={(e) => setRoomName(e.target.value)} />
            </div>
            <div className="input-group">
              <label>房间密码（留空则不设密码）</label>
              <input className="input" type="password" value={roomPassword} onChange={(e) => setRoomPassword(e.target.value)}
                placeholder="可选，设置后游客需密码进入" />
            </div>
            <button className="btn btn-primary btn-block" onClick={handleCreateRoom} disabled={creating}>
              {creating ? '创建中...' : '创建导览房间'}
            </button>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <div className="page">
        <div className="page-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6, justifyContent: 'space-between' }}>
            <button onClick={() => navigate('/')} style={{ background: 'none', border: 'none', fontSize: 20, cursor: 'pointer', padding: '4px 6px', borderRadius: 8 }}>← 返回</button>
            {roomCreated && (
              <button className="btn btn-outline btn-sm" onClick={() => { setRoomCreated(false); }}>关闭房间</button>
            )}
          </div>
          <div className="flex-between">
            <div>
              <h1>🎛️ 团长控制台</h1>
              <p className="subtitle">{roomCreated ? `房间：${roomName} · room_001` : '未创建房间'}</p>
            </div>
          </div>
        </div>

        <div className="tab-bar" style={{ marginTop: 12 }}>
          <button className={activeTab === 'control' ? 'active' : ''} onClick={() => setActiveTab('control')}>导览控制</button>
          <button className={activeTab === 'requests' ? 'active' : ''} onClick={() => setActiveTab('requests')}>
            游客请求 {pendingCount > 0 && `(${pendingCount})`}
          </button>
        </div>

        {activeTab === 'control' && (
          <>
            <div className="card">
              <div className="card-title">📡 导览状态 &nbsp;<span style={{ fontSize: 10, color: 'var(--text-secondary)' }}>GET /api/rooms/{'{roomId}'}</span></div>
              <div style={{ fontSize: 14 }}>
                <p className="mb-2"><strong>当前景点：</strong>{tourState?.currentSpotName}</p>
                <p className="mb-2"><strong>AI 状态：</strong>
                  <span className={`ai-status ${tourState?.aiStatus || 'idle'}`}>
                    <span className={`status-dot${tourState?.aiStatus === 'speaking' ? ' pulse' : ''}`} />
                    {tourState?.aiStatus || '空闲'}
                  </span>
                </p>
                <p className="mb-2"><strong>在线游客：</strong>{tourState?.onlineUsers || 0} 人</p>
                <p className="mb-2"><strong>待处理请求：</strong>{pendingCount} 个</p>
              </div>
            </div>

            <div className="card">
              <div className="card-title">🤖 AI 控制</div>
              <div className="control-grid">
                <button className="control-btn primary" onClick={() => handleAIStatus('speaking')}>
                  <span className="ctrl-icon">▶️</span> 开始讲解
                </button>
                <button className="control-btn warning" onClick={() => handleAIStatus('paused')}>
                  <span className="ctrl-icon">⏸️</span> 暂停讲解
                </button>
                <button className="control-btn" onClick={() => handleAIStatus('resuming')}>
                  <span className="ctrl-icon">▶️</span> 恢复讲解
                </button>
              </div>
            </div>

            <div className="card">
              <div className="card-title">📍 切换景点 &nbsp;<span style={{ fontSize: 10, color: 'var(--text-secondary)' }}>POST /api/rooms/{'{roomId}'}/current-spot</span></div>
              <div className="spot-list">
                {SPOTS.map((spot) => (
                  <button key={spot.id} className={`spot-item${tourState?.currentSpotId === spot.id ? ' active' : ''}`}
                    onClick={() => handleUpdateSpot(spot.id)}>
                    {tourState?.currentSpotId === spot.id ? '📍 ' : ''}{spot.name}
                  </button>
                ))}
              </div>
            </div>

            <div className="card">
              <div className="card-title">📢 群发操作</div>
              <div className="control-grid">
                <button className="control-btn"><span className="ctrl-icon">📣</span> 集合提醒</button>
                <button className="control-btn"><span className="ctrl-icon">🚩</span> 路线变更</button>
                <button className="control-btn"><span className="ctrl-icon">⏰</span> 自由活动</button>
                <button className="control-btn danger"><span className="ctrl-icon">🏁</span> 结束导览</button>
              </div>
            </div>
          </>
        )}

        {activeTab === 'requests' && (
          <div className="card" style={{ minHeight: 200 }}>
            <div className="card-title">🔔 游客私人请求 ({pendingCount} 待处理)</div>
            {privateRequests.length === 0 ? (
              <div className="empty-state"><div className="empty-icon">✅</div><p>暂无游客请求</p></div>
            ) : (
              privateRequests.map((req) => (
                <div key={req.id} className="request-item">
                  <span className="req-user">👤 {req.nickname}</span>
                  <span className="req-content">提问：{req.content}</span>
                  <span className="text-secondary">AI 回复：{req.aiReply}</span>
                  <span className={`file-status ${req.status}`} style={{ display: 'inline-block', width: 'fit-content' }}>
                    {req.status === 'pending' ? '待处理' : req.status === 'notified' ? '已通知' : '已解决'}
                  </span>
                  {req.status === 'pending' && (
                    <div className="req-actions">
                      <button className="btn btn-primary btn-sm" onClick={() => handleResolveRequest(req.id)}>确认处理</button>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </>
  );
}
