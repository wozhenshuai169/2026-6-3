import { HashRouter, Routes, Route, useLocation } from 'react-router-dom';
import { useEffect, useState, useRef } from 'react';
import Home from './pages/Home';
import JoinRoom from './pages/visitor/JoinRoom';
import PublicRoom from './pages/visitor/PublicRoom';
import PrivateAssistant from './pages/visitor/PrivateAssistant';
import ControlPanel from './pages/leader/ControlPanel';
import KnowledgeBase from './pages/admin/KnowledgeBase';
import Dashboard from './pages/admin/Dashboard';

// Map each path to its preferred transition effect
const PAGE_EFFECTS: Record<string, string> = {
  '/': 'scale',
  '/visitor/join': 'slideLeft',
  '/visitor/room': 'fade',
  '/visitor/assistant': 'slideLeft',
  '/leader/control': 'slideLeft',
  '/admin/dashboard': 'slideLeft',
  '/admin/knowledge': 'slideLeft',
};

function AnimatedRoutes() {
  const location = useLocation();
  const [displayLocation, setDisplayLocation] = useState(location);
  const [stage, setStage] = useState('enter');
  const prevPath = useRef(location.pathname);

  useEffect(() => {
    if (location.pathname !== prevPath.current) {
      setStage('exit');
      prevPath.current = location.pathname;
      const timer = setTimeout(() => {
        setDisplayLocation(location);
        setStage('enter');
      }, 180);
      return () => clearTimeout(timer);
    }
  }, [location]);

  // Get effect for current or incoming page
  const effect = PAGE_EFFECTS[displayLocation.pathname] || 'fade';

  return (
    <div className={`page-transition-wrap ${effect} ${stage}`}>
      <Routes location={displayLocation}>
        <Route path="/" element={<Home />} />
        <Route path="/visitor/join" element={<JoinRoom />} />
        <Route path="/visitor/room" element={<PublicRoom />} />
        <Route path="/visitor/assistant" element={<PrivateAssistant />} />
        <Route path="/leader/control" element={<ControlPanel />} />
        <Route path="/admin/dashboard" element={<Dashboard />} />
        <Route path="/admin/knowledge" element={<KnowledgeBase />} />
      </Routes>
    </div>
  );
}

export default function App() {
  return (
    <HashRouter>
      <AnimatedRoutes />
    </HashRouter>
  );
}
