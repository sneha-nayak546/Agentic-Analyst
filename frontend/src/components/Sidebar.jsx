import React, { useState } from 'react';
import {
  Sparkles, LayoutDashboard, Database, 
  History, Bookmark, FileText, 
  Settings, Activity, Users,
  ChevronLeft, ChevronRight, Plus
} from 'lucide-react';
import UserAvatar from './UserAvatar';
import './Sidebar.css';

const Sidebar = ({
  activeTab,
  setActiveTab,
  onNewChat,
  userRole = 'Administrator',
  savedCount = 0
}) => {
  const [isCollapsed, setIsCollapsed] = useState(false);

  const intelligenceNav = [
    { id: 'new_query', label: 'New Query', icon: Sparkles, isAction: true },
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'reports', label: 'Reports', icon: FileText },
    { id: 'schema', label: 'Database', icon: Database },
    { id: 'history', label: 'History', icon: History },
    { id: 'saved', label: 'Saved Queries', icon: Bookmark, badge: savedCount > 0 ? savedCount : null }
  ];

  const adminNav = [
    { id: 'settings', label: 'Settings', icon: Settings },
    { id: 'health', label: 'System Health', icon: Activity }
  ];

  const renderNavGroup = (title, items) => (
    <>
      {!isCollapsed && <div className="sidebar-group-title">{title}</div>}
      {items.map(({ id, label, icon: Icon, badge, isAction }) => {
        const isActive = activeTab === id || (isAction && activeTab === 'chat') || (id === 'chat' && activeTab === 'copilot');
        return (
          <button
            key={id}
            className={`sidebar-nav-item ${isActive ? 'active' : ''}`}
            onClick={() => {
              if (isAction) {
                if (onNewChat) onNewChat();
                setActiveTab('chat');
              } else {
                setActiveTab(id === 'copilot' ? 'chat' : id);
              }
            }}
            title={label}
          >
            <Icon size={18} className="nav-icon" />
            {!isCollapsed && <span>{label}</span>}
            {!isCollapsed && badge && <span style={{ marginLeft: 'auto', background: 'rgba(255,255,255,0.2)', padding: '2px 8px', borderRadius: '12px', fontSize: '10px', fontWeight: 'bold' }}>{badge}</span>}
          </button>
        );
      })}
    </>
  );

  return (
    <aside className={`app-sidebar ${isCollapsed ? 'collapsed' : ''}`} style={isCollapsed ? { width: '80px', minWidth: '80px' } : {}}>
      {/* ── Brand Header ── */}
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">
          <Sparkles size={20} />
        </div>
        {!isCollapsed && <span>JGH Intelligence</span>}
      </div>

      {/* ── New Chat Action (If collapsed we just show icon in nav) ── */}
      {!isCollapsed && (
        <div className="sidebar-new-btn-wrap">
          <button className="sidebar-new-btn" onClick={() => { if(onNewChat) onNewChat(); setActiveTab('chat'); }}>
            <Plus size={16} />
            <span>New Query</span>
          </button>
        </div>
      )}

      {/* ── Navigation Links ── */}
      <nav className="sidebar-nav">
        {renderNavGroup('AI Analytics', intelligenceNav)}
        <div style={{ margin: '8px 0', height: '1px', background: 'rgba(255,255,255,0.1)' }} />
        {renderNavGroup('Administration', adminNav)}
      </nav>

      {/* ── Collapse Toggle ── */}
      <div style={{ display: 'flex', justifyContent: 'center', padding: '10px' }}>
        <button 
          onClick={() => setIsCollapsed(!isCollapsed)}
          style={{ background: 'rgba(255,255,255,0.1)', color: 'white', border: 'none', borderRadius: '50%', width: '32px', height: '32px', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer' }}
        >
          {isCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>

      {/* ── User Profile ── */}
      <div className="sidebar-footer-profile">
        <div className="profile-avatar">
          AD
        </div>
        {!isCollapsed && (
          <div className="profile-info">
            <span className="profile-name">Admin User</span>
            <span className="profile-role">{userRole}</span>
          </div>
        )}
      </div>
    </aside>
  );
};

export default Sidebar;
