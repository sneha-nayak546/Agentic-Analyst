import React from 'react';
import { Database, Plus, MessageSquare, Archive, Settings, HardDrive, ShieldCheck } from 'lucide-react';
import './Sidebar.css';

const Sidebar = ({ activeView, setActiveView }) => {
  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <div className="logo-container">
          <div className="logo-icon">
            <Database size={20} className="text-accent" />
          </div>
          <span className="logo-text">AI Data Analyst</span>
        </div>
      </div>

      <button className={`new-chat-btn ${activeView === 'chat' ? 'active' : ''}`} onClick={() => setActiveView('chat')}>
        <Plus size={16} />
        New Chat
      </button>

      <div className="sidebar-nav">
        <div className="nav-section">
          <span className="nav-title">History</span>
          <button className={`nav-item ${activeView === 'history' ? 'active' : ''}`} onClick={() => setActiveView('history')}>
            <MessageSquare size={16} />
            Recent Queries
          </button>
        </div>
        <div className="nav-section">
          <span className="nav-title">System</span>
          <button className={`nav-item ${activeView === 'admin' ? 'active' : ''}`} onClick={() => setActiveView('admin')}>
            <Archive size={16} />
            Observability
          </button>
        </div>
      </div>

      <div className="sidebar-footer">
        <div className="nav-section">
          <button className={`nav-item ${activeView === 'settings' ? 'active' : ''}`} onClick={() => setActiveView('settings')}>
            <Settings size={16} />
            Settings
          </button>
        </div>
        
        <div className="connection-status">
          <div className="status-row">
            <HardDrive size={14} className="text-secondary" />
            <span className="db-name">Production DB</span>
            <div className="status-indicator online"></div>
          </div>
          <div className="badge-row">
            <ShieldCheck size={12} className="text-green" />
            <span className="badge-text">Read Only Mode</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
