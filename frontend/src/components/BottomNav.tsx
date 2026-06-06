import { useLocation, useNavigate } from 'react-router-dom';

interface Props {
  role: 'visitor' | 'leader' | 'admin';
  pendingRequests?: number;
}

export default function BottomNav({ role, pendingRequests = 0 }: Props) {
  const location = useLocation();
  const navigate = useNavigate();

  if (role === 'visitor') {
    const tabs = [
      { path: '/visitor/join', icon: '🏠', label: '加入' },
      { path: '/visitor/room', icon: '🎯', label: '公共导览' },
      { path: '/visitor/assistant', icon: '💬', label: '私人助手' },
    ];
    return (
      <nav className="bottom-nav">
        {tabs.map((t) => (
          <button
            key={t.path}
            className={`nav-item${location.pathname === t.path ? ' active' : ''}`}
            onClick={() => navigate(t.path)}
          >
            <span className="nav-icon">{t.icon}</span>
            {t.label}
          </button>
        ))}
      </nav>
    );
  }

  if (role === 'leader') {
    const tabs = [{ path: '/leader/control', icon: '🎛️', label: '控制台' }];
    return (
      <nav className="bottom-nav">
        {tabs.map((t) => (
          <button
            key={t.path}
            className={`nav-item${location.pathname === t.path ? ' active' : ''}`}
            onClick={() => navigate(t.path)}
          >
            <div className="nav-item-wrapper">
              <span className="nav-icon">{t.icon}</span>
              {pendingRequests > 0 && <span className="badge">{pendingRequests}</span>}
            </div>
            {t.label}
          </button>
        ))}
      </nav>
    );
  }

  // admin
  const tabs = [
    { path: '/admin/dashboard', icon: '📊', label: '数据大屏' },
    { path: '/admin/knowledge', icon: '📚', label: '知识库' },
  ];
  return (
    <nav className="bottom-nav">
      {tabs.map((t) => (
        <button
          key={t.path}
          className={`nav-item${location.pathname === t.path ? ' active' : ''}`}
          onClick={() => navigate(t.path)}
        >
          <span className="nav-icon">{t.icon}</span>
          {t.label}
        </button>
      ))}
    </nav>
  );
}
