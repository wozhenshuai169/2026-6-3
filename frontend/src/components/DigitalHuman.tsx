import type { AIStatus } from '../api/types';

interface Props {
  aiStatus: AIStatus;
  spotName: string;
  onlineUsers: number;
  isMuted: boolean;
  isTextMode: boolean;
  isRecording: boolean;
  onToggleMute: () => void;
  onToggleMode: () => void;
  onVoiceRecord: () => void;
}

const STATUS_LABELS: Record<AIStatus, string> = {
  idle: '待命中', listening: '聆听中', speaking: '讲解中', thinking: '思考中',
  paused: '已暂停', resuming: '恢复讲解',
};

export default function DigitalHuman({
  aiStatus, spotName, onlineUsers, isMuted, isTextMode,
  isRecording, onToggleMute, onToggleMode, onVoiceRecord,
}: Props) {
  const isSpeaking = aiStatus === 'speaking' || aiStatus === 'resuming';

  return (
    <div className="digital-human-panel">
      {/* Top info */}
      <div className="dh-top">
        <span className="dh-spot">📍 {spotName}</span>
        <span className="dh-online">👥 {onlineUsers} 人在线</span>
      </div>

      {/* Avatar */}
      <div className="dh-avatar-container">
        <div className={`dh-ring ${isSpeaking && !isMuted ? 'speaking' : ''}`}>
          <div className="dh-ring-inner">
            <div className="dh-face">
              <div className="dh-eyes">
                <div className={`dh-eye left ${isSpeaking ? 'attentive' : ''}`}>
                  <div className="dh-pupil" />
                </div>
                <div className={`dh-eye right ${isSpeaking ? 'attentive' : ''}`}>
                  <div className="dh-pupil" />
                </div>
              </div>
              <div className={`dh-mouth ${isSpeaking && !isMuted ? 'speaking' : ''}`}>
                <div className="dh-mouth-inner" />
              </div>
              <div className="dh-blush left" />
              <div className="dh-blush right" />
            </div>
          </div>
        </div>

        {isSpeaking && !isMuted && (
          <div className="dh-audio-waves">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="dh-wave-bar" style={{ animationDelay: `${i * 0.15}s` }} />
            ))}
          </div>
        )}
      </div>

      {/* Name & Status */}
      <div className="dh-info">
        <h2 className="dh-name">小灵</h2>
        <span className={`dh-status ${isSpeaking ? 'active' : ''}`}>
          <span className={`dh-status-dot${isSpeaking ? ' pulse' : ''}`} />
          {isMuted ? '已静音' : STATUS_LABELS[aiStatus] || aiStatus}
        </span>
      </div>

      {/* Controls */}
      <div className="dh-controls">
        <button
          className={`dh-ctrl-btn ${isMuted ? 'off' : ''}`}
          onClick={onToggleMute}
          title={isMuted ? '打开播报' : '关闭播报'}
        >
          <span className="dh-ctrl-icon">{isMuted ? '🔇' : '🔊'}</span>
          <span className="dh-ctrl-label">{isMuted ? '已静音' : '播报中'}</span>
        </button>

        <button
          className={`dh-ctrl-btn mic ${isRecording ? 'active' : ''}`}
          onMouseDown={onVoiceRecord}
          title="按住说话"
        >
          <span className="dh-ctrl-icon">🎤</span>
          <span className="dh-ctrl-label">{isRecording ? '录音中' : '按住说'}</span>
        </button>

        <button
          className={`dh-ctrl-btn ${isTextMode ? 'active' : ''}`}
          onClick={onToggleMode}
          title={isTextMode ? '切换数字人模式' : '切换文字模式'}
        >
          <span className="dh-ctrl-icon">{isTextMode ? '👤' : '💬'}</span>
          <span className="dh-ctrl-label">{isTextMode ? '数字人' : '文字'}</span>
        </button>
      </div>
    </div>
  );
}
