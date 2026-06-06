import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiGetDashboard } from '../../api/mock';
import type { DashboardSummary } from '../../api/types';

export default function Dashboard() {
  const navigate = useNavigate();
  const [data, setData] = useState<DashboardSummary | null>(null);

  useEffect(() => {
    apiGetDashboard().then(setData);
    const interval = setInterval(() => apiGetDashboard().then(setData), 5000);
    return () => clearInterval(interval);
  }, []);

  if (!data) {
    return (
      <div className="page" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <p className="text-secondary">加载中...</p>
      </div>
    );
  }

  return (
    <>
      <div className="page">
        <div className="page-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
            <button onClick={() => navigate('/')} style={{ background: 'none', border: 'none', fontSize: 20, cursor: 'pointer', padding: '4px 6px', borderRadius: 8 }}>← 返回</button>
          </div>
          <div className="flex-between">
            <div>
              <h1>📊 运营数据大屏</h1>
              <p className="subtitle">A5 景区导览 AI 数字人系统</p>
            </div>
            <span className="ai-status explaining"><span className="status-dot pulse" />实时</span>
          </div>
        </div>

        <div className="stat-grid" style={{ marginTop: 12 }}>
          <div className="stat-card"><div className="stat-value">{data.todayQuestions}</div><div className="stat-label">今日问答次数</div></div>
          <div className="stat-card"><div className="stat-value">{data.onlineRooms}</div><div className="stat-label">当前在线房间</div></div>
          <div className="stat-card"><div className="stat-value">{data.publicQuestions}</div><div className="stat-label">公共问题数</div></div>
          <div className="stat-card"><div className="stat-value">{data.privateQuestions}</div><div className="stat-label">私人问题数</div></div>
          <div className="stat-card"><div className="stat-value">{(data.knowledgeHitRate * 100).toFixed(0)}%</div><div className="stat-label">知识库命中率</div></div>
          <div className="stat-card"><div className="stat-value">{data.onlineUsers}</div><div className="stat-label">当前在线游客</div></div>
          <div className="stat-card wide" style={{ textAlign: 'left' }}>
            <div className="card-title">⭐ 平均满意度</div>
            <div style={{ fontSize: 32, fontWeight: 700, color: 'var(--warning)' }}>
              {'★'.repeat(Math.round(data.avgSatisfaction))}{'☆'.repeat(5 - Math.round(data.avgSatisfaction))}
              <span style={{ fontSize: 16, marginLeft: 8, color: 'var(--text)' }}>{data.avgSatisfaction}/5</span>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-title">🔥 热门问题 Top 5</div>
          <ul className="top-list">
            {data.topQuestions.map((item, i) => (
              <li key={i}><span><span className="rank">{i + 1}.</span>{item.question}</span><span className="count">{item.count} 次</span></li>
            ))}
          </ul>
        </div>

        <div className="card">
          <div className="card-title">📈 问答渠道分布</div>
          <div style={{ display: 'flex', gap: 16, marginTop: 8 }}>
            <div style={{ flex: 1, textAlign: 'center' }}>
              <div style={{ height: 8, background: '#e5e7eb', borderRadius: 4, overflow: 'hidden' }}>
                <div style={{ width: `${(data.publicQuestions / data.todayQuestions) * 100}%`, height: '100%', background: 'var(--primary)', borderRadius: 4 }} />
              </div>
              <p style={{ fontSize: 13, marginTop: 4 }}>公共频道 {data.publicQuestions} 次</p>
            </div>
            <div style={{ flex: 1, textAlign: 'center' }}>
              <div style={{ height: 8, background: '#e5e7eb', borderRadius: 4, overflow: 'hidden' }}>
                <div style={{ width: `${(data.privateQuestions / data.todayQuestions) * 100}%`, height: '100%', background: 'var(--warning)', borderRadius: 4 }} />
              </div>
              <p style={{ fontSize: 13, marginTop: 4 }}>私人频道 {data.privateQuestions} 次</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-title">🧩 API 接口状态</div>
          <ul className="top-list">
            {[
              { label: 'POST /api/auth/register', ok: true },
              { label: 'POST /api/rooms', ok: true },
              { label: 'GET /api/rooms/{roomId}/avatar-state', ok: true },
              { label: 'POST /api/ai/public-question', ok: true },
              { label: 'POST /api/audio/asr & tts', ok: true },
              { label: 'POST /api/vision/recognize', ok: true },
              { label: 'POST /api/recommend/route', ok: true },
            ].map((m) => (
              <li key={m.label}><span style={{ fontSize: 13 }}>{m.label}</span>
                <span style={{ color: m.ok ? 'var(--success)' : 'var(--danger)', fontSize: 12 }}>{m.ok ? '✅ 正常' : '❌ 异常'}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </>
  );
}
