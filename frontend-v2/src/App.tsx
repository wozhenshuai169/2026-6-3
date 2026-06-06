import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { AnimatePresence } from 'motion/react'
import { ErrorBoundary } from './components/shared/ErrorBoundary'
import { useUserStore } from './stores/userStore'
import Home from './pages/Home'
import Tour from './pages/Tour'
import PrivateAssistant from './pages/PrivateAssistant'
import GuideHome from './pages/guide/GuideHome'
import GuideRoom from './pages/guide/GuideRoom'
import GuideRoutes from './pages/guide/GuideRoutes'
import AdminDashboard from './pages/admin/AdminDashboard'
import AdminKnowledge from './pages/admin/AdminKnowledge'
import AdminAvatar from './pages/admin/AdminAvatar'
import AdminReports from './pages/admin/AdminReports'

function NotFound() {
  return (
    <div className="h-full flex flex-col items-center justify-center gap-4 px-8 text-center">
      <span className="text-6xl">🧭</span>
      <h2 className="text-lg font-semibold">页面不存在</h2>
      <p className="text-text-secondary text-sm">你似乎来到了景区外的未知区域</p>
      <a href="/" className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-primary to-accent text-white text-sm font-medium">
        返回首页
      </a>
    </div>
  )
}

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const user = useUserStore((s) => s.user)
  if (!user) return <Navigate to="/" replace />
  return <>{children}</>
}

/** 根据路由判断容器宽度：游客端手机宽，管理后台全宽 */
function AppShell({ children }: { children: React.ReactNode }) {
  const loc = useLocation()
  const isAdmin = loc.pathname.startsWith('/admin')
  const isGuide = loc.pathname.startsWith('/guide')

  return (
    <ErrorBoundary>
      <div className={`h-full w-full mx-auto relative overflow-hidden bg-[#0a0a1a] ${
        isAdmin ? '' : isGuide ? 'max-w-2xl' : 'max-w-lg'
      }`}>
        {children}
      </div>
    </ErrorBoundary>
  )
}

export default function App() {
  return (
    <AppShell>
      <AnimatePresence mode="wait">
        <Routes>
          {/* 游客端 */}
          <Route path="/" element={<Home />} />
          <Route path="/tour/:roomId" element={<ProtectedRoute><Tour /></ProtectedRoute>} />
          <Route path="/private/:roomId" element={<ProtectedRoute><PrivateAssistant /></ProtectedRoute>} />

          {/* 团长端 */}
          <Route path="/guide" element={<ProtectedRoute><GuideHome /></ProtectedRoute>} />
          <Route path="/guide/:roomId" element={<ProtectedRoute><GuideRoom /></ProtectedRoute>} />
          <Route path="/guide/routes" element={<ProtectedRoute><GuideRoutes /></ProtectedRoute>} />

          {/* 管理后台 — 含侧边导航 */}
          <Route path="/admin" element={<ProtectedRoute><AdminLayout><AdminDashboard /></AdminLayout></ProtectedRoute>} />
          <Route path="/admin/knowledge" element={<ProtectedRoute><AdminLayout><AdminKnowledge /></AdminLayout></ProtectedRoute>} />
          <Route path="/admin/avatar" element={<ProtectedRoute><AdminLayout><AdminAvatar /></AdminLayout></ProtectedRoute>} />
          <Route path="/admin/reports" element={<ProtectedRoute><AdminLayout><AdminReports /></AdminLayout></ProtectedRoute>} />

          <Route path="*" element={<NotFound />} />
        </Routes>
      </AnimatePresence>
    </AppShell>
  )
}

/** 管理后台侧边导航布局 */
function AdminLayout({ children }: { children: React.ReactNode }) {
  const loc = useLocation()

  const navItems = [
    { path: '/admin', icon: '📊', label: '数据大屏' },
    { path: '/admin/knowledge', icon: '📚', label: '知识库' },
    { path: '/admin/avatar', icon: '🎭', label: '数字人' },
    { path: '/admin/reports', icon: '📋', label: '游客报告' },
  ]

  return (
    <div className="h-full flex">
      {/* 侧边栏 */}
      <aside className="w-48 flex-shrink-0 glass-strong flex flex-col py-4 hidden lg:flex">
        <div className="px-4 mb-6">
          <h1 className="text-sm font-bold text-gradient">灵境同行</h1>
          <p className="text-[10px] text-text-muted mt-0.5">管理后台</p>
        </div>
        <nav className="flex-1 space-y-1 px-2">
          {navItems.map((item) => {
            const active = loc.pathname === item.path || (item.path !== '/admin' && loc.pathname.startsWith(item.path))
            return (
              <a
                key={item.path}
                href={item.path}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all ${
                  active
                    ? 'bg-primary/15 text-white font-medium'
                    : 'text-text-secondary hover:text-white hover:bg-white/5'
                }`}
              >
                <span>{item.icon}</span>
                <span>{item.label}</span>
              </a>
            )
          })}
        </nav>
        <div className="px-4 pt-4 border-t border-white/5">
          <a href="/" className="text-xs text-text-muted hover:text-text-secondary transition-colors">← 返回首页</a>
        </div>
      </aside>

      {/* 移动端顶部导航 */}
      <div className="lg:hidden glass-strong w-full flex items-center gap-1 px-2 py-2 overflow-x-auto">
        {navItems.map((item) => {
          const active = loc.pathname === item.path || (item.path !== '/admin' && loc.pathname.startsWith(item.path))
          return (
            <a
              key={item.path}
              href={item.path}
              className={`flex-shrink-0 px-3 py-1.5 rounded-lg text-xs whitespace-nowrap transition-all ${
                active ? 'bg-primary/15 text-white' : 'text-text-muted hover:text-text-secondary'
              }`}
            >
              {item.icon} {item.label}
            </a>
          )
        })}
      </div>

      {/* 主内容区 */}
      <div className="flex-1 overflow-hidden">
        {children}
      </div>
    </div>
  )
}
