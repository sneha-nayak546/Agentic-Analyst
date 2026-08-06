import React, { useState, useRef, useEffect } from 'react';
import CenterChat from './components/CenterChat';
import DatabaseSchemaPanel from './components/DatabaseSchemaPanel';
import AdminPanel from './components/AdminPanel';
import HistoryView from './components/HistoryView';
import Settings from './components/Settings';
import './index.css';

// ── Icons ──────────────────────────────────────────────────────
const IconDB  = () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>;
const IconMsg = () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>;
const IconHist= () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>;
const IconSet = () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>;
const IconAdm = () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>;
const IconPlus= () => <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>;

// ── Nav items ──────────────────────────────────────────────────
const NAV_ITEMS = [
  { id: 'chat',     label: 'Query Interface',  Icon: IconMsg  },
  { id: 'history',  label: 'History & Audit',  Icon: IconHist },
  { id: 'admin',    label: 'Schema Admin',      Icon: IconAdm  },
  { id: 'settings', label: 'Settings',          Icon: IconSet  },
];

// ── App ────────────────────────────────────────────────────────
function App() {
  const [activeTab, setActiveTab]     = useState('chat');
  const [messages,   setMessages]     = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [historyInput, setHistoryInput] = useState('');

  // ── Send Message handler ──────────────────────────────────────
  const handleSend = async (question) => {
    if (!question?.trim()) return;

    // 1. Add user message
    const userMsg = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: question,
    };
    setMessages(prev => [...prev, userMsg]);
    setIsProcessing(true);

    try {
      // 2. POST to /query
      const response = await fetch('http://localhost:8000/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, execute: true }),
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      // ── ROOT CAUSE FIX ─────────────────────────────────────────
      // The backend now returns a flat, standardized object with
      // these keys: question, sql_query, execution_time,
      // rows_returned, status, summary, results, columns,
      // report_urls, schema.
      // We store the entire parsed object as msg.data so the
      // AiResponseCard in CenterChat.jsx can read it directly.
      // ──────────────────────────────────────────────────────────
      const data = await response.json();

      const aiMsg = {
        id: `ai-${Date.now()}`,
        role: 'ai',
        content: data.summary || data.message || data.status,
        data,       // ← full standardized response object
        error: data.status === 'error' && !data.sql_query,
      };

      setMessages(prev => [...prev, aiMsg]);

    } catch (err) {
      setMessages(prev => [...prev, {
        id: `err-${Date.now()}`,
        role: 'ai',
        content: `Failed to connect to backend: ${err.message}`,
        data: null,
        error: true,
      }]);
    } finally {
      setIsProcessing(false);
    }
  };

  // History re-run helper
  const handleHistoryReRun = (question) => {
    setActiveTab('chat');
    handleSend(question);
  };

  return (
    <div className="app-shell">
      {/* ── Sidebar ─────────────────────────────────────────── */}
      <aside className="app-sidebar">
        {/* Logo */}
        <div className="sidebar-logo">
          <div className="sidebar-logo-icon"><IconDB /></div>
          <span>Agentic Analyst</span>
        </div>

        {/* New Query */}
        <div className="sidebar-new-btn-wrap">
          <button
            className="sidebar-new-btn"
            onClick={() => { setMessages([]); setActiveTab('chat'); }}
          >
            <IconPlus /> New Query
          </button>
        </div>

        {/* Nav */}
        <nav className="sidebar-nav">
          {NAV_ITEMS.map(({ id, label, Icon }) => (
            <button
              key={id}
              className={`sidebar-nav-item ${activeTab === id ? 'active' : ''}`}
              onClick={() => setActiveTab(id)}
            >
              <Icon />
              <span>{label}</span>
            </button>
          ))}
        </nav>

        {/* Footer status */}
        <div className="sidebar-footer-status">
          <div className="sidebar-status-dot online" />
          <span>Backend Connected</span>
        </div>
      </aside>

      {/* ── Main Area ─────────────────────────────────────── */}
      <div className="app-main">
        {activeTab === 'settings' && (
          <div className="panel-page"><Settings /></div>
        )}
        {activeTab === 'history' && (
          <div className="panel-page"><HistoryView onReRun={handleHistoryReRun} /></div>
        )}
        {activeTab === 'admin' && (
          <div className="panel-page"><AdminPanel /></div>
        )}
        {activeTab === 'chat' && (
          <div className="chat-layout">
            {/* Center Chat */}
            <CenterChat
              messages={messages}
              onSendMessage={handleSend}
              isProcessing={isProcessing}
            />
            {/* Right: Database Schema Panel */}
            <DatabaseSchemaPanel />
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
