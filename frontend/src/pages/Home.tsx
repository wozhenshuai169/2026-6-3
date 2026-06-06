import { useNavigate } from 'react-router-dom';

const ROLES = [
  {
    key: 'visitor',
    title: '游客端',
    desc: '加入导览房间 · 公共问答 · 私人助手',
    icon: '🧑‍🤝‍🧑',
    path: '/visitor/join',
    color: '#1a73e8',
  },
  {
    key: 'leader',
    title: '团长端',
    desc: '创建房间 · 控制讲解 · 处理游客请求',
    icon: '🎛️',
    path: '/leader/control',
    color: '#0d904f',
  },
  {
    key: 'admin',
    title: '后台管理端',
    desc: '知识库管理 · 数据大屏 · 运营分析',
    icon: '📊',
    path: '/admin/dashboard',
    color: '#7c3aed',
  },
];

export default function Home() {
  const navigate = useNavigate();

  return (
    <div className="page" style={{ paddingTop: 40, paddingBottom: 40 }}>
      <div style={{ textAlign: 'center', marginBottom: 32 }}>
        <div style={{ fontSize: 56, marginBottom: 12 }}>🏯</div>
        <h1 style={{ fontSize: 24, fontWeight: 700 }}>灵境同行</h1>
        <p className="text-secondary" style={{ marginTop: 4 }}>
          A5 群组导览 AI 数字人系统 · V0.1
        </p>
      </div>

      <p className="section-title" style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>
        选择演示端
      </p>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {ROLES.map((role) => (
          <button
            key={role.key}
            className="card"
            onClick={() => navigate(role.path)}
            style={{
              border: 'none',
              cursor: 'pointer',
              textAlign: 'left',
              display: 'flex',
              alignItems: 'center',
              gap: 14,
              padding: 18,
              borderLeft: `4px solid ${role.color}`,
            }}
          >
            <span style={{ fontSize: 32 }}>{role.icon}</span>
            <div>
              <div style={{ fontSize: 16, fontWeight: 600 }}>{role.title}</div>
              <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{role.desc}</div>
            </div>
            <span style={{ marginLeft: 'auto', color: 'var(--text-secondary)' }}>→</span>
          </button>
        ))}
      </div>

      <div className="card" style={{ marginTop: 20, textAlign: 'center', background: '#eff6ff' }}>
        <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
          🚀 演示流程：团长创建房间 → 游客加入 → 公共问答 → 私人问答 → 后台查看数据
        </p>
      </div>
    </div>
  );
}
