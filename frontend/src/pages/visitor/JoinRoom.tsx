import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiRegister, apiJoinRoom, apiRoomHasPassword, apiVerifyRoomPassword } from '../../api/mock';

export default function JoinRoom() {
  const navigate = useNavigate();
  const [userName, setUserName] = useState('游客A');
  const [roomId, setRoomId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Password dialog
  const [showPassword, setShowPassword] = useState(false);
  const [password, setPassword] = useState('');
  const [pwdError, setPwdError] = useState('');

  const handleJoin = async () => {
    if (!userName.trim()) { setError('请输入昵称'); return; }
    if (!roomId.trim()) { setError('请输入房间号'); return; }
    setError('');
    setLoading(true);

    // Register user
    await apiRegister(userName, '123456');

    // Check if room has password
    const hasPwd = await apiRoomHasPassword();
    if (hasPwd) {
      setShowPassword(true);
      setLoading(false);
      return;
    }

    // No password, join directly
    await apiJoinRoom();
    setLoading(false);
    navigate('/visitor/room');
  };

  const handlePasswordSubmit = async () => {
    const ok = await apiVerifyRoomPassword(password);
    if (!ok) {
      setPwdError('密码错误，请重新输入');
      setPassword('');
      return;
    }
    setShowPassword(false);
    await apiJoinRoom();
    navigate('/visitor/room');
  };

  return (
    <>
      <div className="page join-room">
        <div style={{ position: 'absolute', top: 16, left: 16 }}>
          <button
            onClick={() => navigate('/')}
            style={{ background: 'none', border: 'none', fontSize: 20, cursor: 'pointer', padding: '4px 8px' }}
          >← 返回</button>
        </div>
        <div className="logo">🏯</div>
        <h2>灵境同行</h2>
        <p className="text-secondary">A5 群组导览 AI 数字人系统</p>

        <div className="join-card" style={{ marginTop: 24 }}>
          <div className="input-group">
            <label>昵称</label>
            <input className="input" value={userName} onChange={(e) => { setUserName(e.target.value); setError(''); }}
              placeholder="输入你的昵称" />
          </div>
          <div className="input-group">
            <label>房间号</label>
            <input className="input" value={roomId} onChange={(e) => { setRoomId(e.target.value); setError(''); }}
              placeholder="输入团长分享的房间号" />
          </div>
          {error && <p style={{ color: 'var(--danger)', fontSize: 13, marginBottom: 8 }}>{error}</p>}
          <button className="btn btn-primary btn-block" onClick={handleJoin} disabled={loading}>
            {loading ? '加入中...' : '加入导览房间'}
          </button>
        </div>
      </div>

      {/* Password Dialog */}
      {showPassword && (
        <div className="dialog-overlay">
          <div className="dialog-box">
            <div style={{ fontSize: 40, marginBottom: 8 }}>🔒</div>
            <h3 style={{ marginBottom: 4 }}>房间已加密</h3>
            <p className="text-secondary" style={{ marginBottom: 16 }}>请输入团长设置的房间密码</p>
            <input
              className="input"
              type="password"
              value={password}
              onChange={(e) => { setPassword(e.target.value); setPwdError(''); }}
              placeholder="输入房间密码"
              autoFocus
              onKeyDown={(e) => e.key === 'Enter' && handlePasswordSubmit()}
            />
            {pwdError && <p style={{ color: 'var(--danger)', fontSize: 13, marginTop: 8 }}>{pwdError}</p>}
            <div style={{ display: 'flex', gap: 10, marginTop: 16 }}>
              <button className="btn btn-outline btn-block"
                onClick={() => { setShowPassword(false); setPassword(''); setPwdError(''); }}>取消</button>
              <button className="btn btn-primary btn-block" onClick={handlePasswordSubmit}>确认</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
