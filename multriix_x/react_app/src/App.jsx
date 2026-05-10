import React, { useState, useEffect } from 'react';
import LiveBrain from './components/LiveBrain';
import ChatPanel from './components/ChatPanel';
import SystemStats from './components/SystemStats';
import './styles/tron.css';

function App() {
  const [stats, setStats] = useState(null);

  return (
    <div className="dashboard">
      <header>
        <h1>MULTRIIX X ◈ ZEROX</h1>
        <div className="mono">
          CPU: {stats?.cpu_percent}% | RAM: {(stats?.ram?.used / 1024**3).toFixed(1)}GB
        </div>
      </header>

      <main className="main-content">
        <div className="brain-view">
          <LiveBrain />
        </div>
        <ChatPanel />
      </main>

      <aside className="side-panel">
        <SystemStats onStatsUpdate={setStats} />
      </aside>
      
      <nav className="footer-nav">
        <button>CONFIG</button>
        <button>CONTROL</button>
        <button>MEMORY</button>
      </nav>
    </div>
  );
}

export default App;
