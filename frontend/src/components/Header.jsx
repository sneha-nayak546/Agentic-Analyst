import React, { useState, useEffect, useRef } from 'react';
import {
  Sparkles, Moon, Sun, Bell, Lock, CheckCircle2, AlertCircle,
  User, ShieldCheck, ChevronDown, Check, RefreshCw, X, ExternalLink
} from 'lucide-react';
import UserAvatar from './UserAvatar';

const ROLES = ['Administrator', 'Data Analyst', 'Operations Lead', 'Executive'];

const SAMPLE_NOTIFICATIONS = [
  { id: 'notif-1', title: 'Karnataka Distributors Synced', desc: '49 active distributors updated with latest July-August wallet points.', time: '10m ago', unread: true },
  { id: 'notif-2', title: 'Database Optimization', desc: 'Query indexes validated across withdrawal_request and wallet_transaction.', time: '1h ago', unread: true },
  { id: 'notif-3', title: 'System Health Optimal', desc: 'MySQL connection latency: 1.42ms. All nodes operational.', time: '2h ago', unread: true },
];

const Header = ({
  activeTab,
  isPrivate,
  setIsPrivate,
  userRole = 'Administrator',
  setUserRole,
  onNewSession,
  theme,
  toggleTheme
}) => {
  const [healthStatus, setHealthStatus] = useState({ online: true, loading: false, latency: 1.8 });
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [notifications, setNotifications] = useState(SAMPLE_NOTIFICATIONS);

  const notifRef = useRef(null);
  const profileRef = useRef(null);

  const unreadCount = notifications.filter(n => n.unread).length;

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (notifRef.current && !notifRef.current.contains(e.target)) {
        setShowNotifications(false);
      }
      if (profileRef.current && !profileRef.current.contains(e.target)) {
        setShowProfileMenu(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const checkHealth = async () => {
    setHealthStatus(prev => ({ ...prev, loading: true }));
    const t0 = performance.now();
    try {
      const res = await fetch('/health');
      const t1 = performance.now();
      const latency = Math.round(t1 - t0);
      if (res.ok) {
        const data = await res.json();
        setHealthStatus({ online: data.status === 'online' || data.database_connected, loading: false, latency });
      } else {
        setHealthStatus({ online: false, loading: false, latency });
      }
    } catch {
      setHealthStatus({ online: false, loading: false, latency: 0 });
    }
  };

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const markAllRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, unread: false })));
  };

  return (
    <header className="app-header">
      {/* ── Left Title ── */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <h1 className="header-title">
          {activeTab === 'chat' ? 'AI Command Center' : 
           activeTab === 'dashboard' ? 'Business Overview' :
           activeTab === 'reports' ? 'Reports & Exports' :
           activeTab === 'schema' ? 'Database Architecture' :
           activeTab === 'history' ? 'Query History' :
           activeTab === 'saved' ? 'Saved Queries' :
           activeTab === 'settings' ? 'System Settings' :
           activeTab === 'health' ? 'System Health' : 'JGH Intelligence'}
        </h1>
        {isPrivate && (
          <span className="status-badge status-warning">
            <Lock size={12} />
            Private Session
          </span>
        )}
      </div>

      {/* ── Right Status & Controls ── */}
      <div className="header-actions">
        {/* System Operational Badge */}
        <div
          onClick={checkHealth}
          className={`status-pill ${healthStatus.online ? 'operational' : ''}`}
          title={`Click to refresh system health (Latency: ${healthStatus.latency}ms)`}
          style={{ cursor: 'pointer' }}
        >
          {healthStatus.online ? 'System Operational' : 'Offline'}
          {healthStatus.loading && <RefreshCw size={12} className="animate-spin" />}
        </div>

        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className="btn-icon"
          title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}
          style={{ borderRadius: '50%' }}
        >
          {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
        </button>

        {/* Notifications Bell */}
        <div ref={notifRef} style={{ position: 'relative' }}>
          <button
            onClick={() => {
              setShowNotifications(!showNotifications);
              setShowProfileMenu(false);
            }}
            className="btn-icon"
            style={{ borderRadius: '50%', position: 'relative' }}
          >
            <Bell size={18} />
            {unreadCount > 0 && (
              <span style={{
                position: 'absolute', top: '-4px', right: '-4px',
                width: '18px', height: '18px', borderRadius: '50%',
                background: 'var(--error)', color: '#FFF',
                fontSize: '10px', fontWeight: 'bold',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                border: '2px solid var(--bg-surface)'
              }}>
                {unreadCount}
              </span>
            )}
          </button>

          {/* Notifications Dropdown Modal */}
          {showNotifications && (
            <div className="premium-card animate-slide-up" style={{
              position: 'absolute', top: '120%', right: '0',
              width: '320px', padding: '0', zIndex: 100
            }}>
              <div style={{ padding: '1rem', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--bg-surface-subtle)' }}>
                <span style={{ fontWeight: 600 }}>Notifications</span>
                {unreadCount > 0 && (
                  <button onClick={markAllRead} style={{ color: 'var(--primary)', fontSize: '0.8125rem', fontWeight: 500 }}>
                    Mark all read
                  </button>
                )}
              </div>
              <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                {notifications.map(n => (
                  <div key={n.id} style={{
                    padding: '1rem', borderBottom: '1px solid var(--border-color)',
                    background: n.unread ? 'var(--bg-hover)' : 'var(--bg-surface)',
                    display: 'flex', flexDirection: 'column', gap: '4px'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ fontWeight: 600, fontSize: '0.875rem' }}>{n.title}</span>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{n.time}</span>
                    </div>
                    <span style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>{n.desc}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* User Profile Avatar with Dropdown */}
        <div ref={profileRef} style={{ position: 'relative' }}>
          <div
            onClick={() => {
              setShowProfileMenu(!showProfileMenu);
              setShowNotifications(false);
            }}
            style={{ cursor: 'pointer' }}
          >
            <UserAvatar size={40} showOnline={true} name={userRole} />
          </div>

          {/* Profile Menu Dropdown */}
          {showProfileMenu && (
            <div className="premium-card animate-slide-up" style={{
              position: 'absolute', top: '120%', right: '0',
              width: '240px', padding: '0.5rem', zIndex: 100,
              display: 'flex', flexDirection: 'column', gap: '4px'
            }}>
              <div style={{ padding: '0.75rem', borderBottom: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <UserAvatar size={36} showOnline={false} />
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                  <span style={{ fontWeight: 600, fontSize: '0.9375rem' }}>{userRole}</span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>admin@jgh.com</span>
                </div>
              </div>

              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', padding: '0.5rem 0.75rem 0.25rem' }}>
                Switch Access Role
              </span>

              {ROLES.map(role => (
                <button
                  key={role}
                  onClick={() => {
                    if (setUserRole) setUserRole(role);
                    setShowProfileMenu(false);
                  }}
                  style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    padding: '0.5rem 0.75rem', borderRadius: 'var(--radius-sm)',
                    background: userRole === role ? 'var(--bg-hover)' : 'transparent',
                    color: userRole === role ? 'var(--primary)' : 'var(--text-primary)',
                    fontWeight: userRole === role ? 600 : 500,
                    fontSize: '0.875rem'
                  }}
                >
                  <span>{role}</span>
                  {userRole === role && <Check size={16} />}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;
