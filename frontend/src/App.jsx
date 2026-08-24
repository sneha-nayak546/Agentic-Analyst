import React, { useState, useEffect, useCallback } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import CenterChat from './components/CenterChat';
import DashboardPage from './components/DashboardPage';
import HistoryView from './components/HistoryView';
import ReportsPage from './components/ReportsPage';
import DatabaseSchemaPanel from './components/DatabaseSchemaPanel';
import SavedQueriesView from './components/SavedQueriesView';
import AdminPanel from './components/AdminPanel';
import ArchitectureView from './components/ArchitectureView';
import Settings from './components/Settings';
import ToastContainer from './components/ToastContainer';
import Login from './components/Login';
import './index.css';

export function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [activeTab, setActiveTab] = useState('chat');
  const [messages, setMessages] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isPrivate, setIsPrivate] = useState(false);
  const [userRole, setUserRole] = useState('Administrator');
  const [toasts, setToasts] = useState([]);
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('jgh_theme') || 'dark';
  });
  const [savedQueries, setSavedQueries] = useState(() => {
    try {
      const stored = localStorage.getItem('jgh_saved_queries');
      return stored ? JSON.parse(stored) : [
        { question: 'Show Karnataka distributors', sql: 'SELECT * FROM distributors WHERE region = \'Karnataka\';' },
        { question: 'What were the total earnings last month?', sql: 'SELECT SUM(earning_amount) AS total_earnings FROM distributor_earnings WHERE month = \'July 2026\';' }
      ];
    } catch {
      return [];
    }
  });

  // Save bookmarks to localStorage
  useEffect(() => {
    try {
      localStorage.setItem('jgh_saved_queries', JSON.stringify(savedQueries));
    } catch (e) {
      console.error(e);
    }
  }, [savedQueries]);

  // Save theme to localStorage
  useEffect(() => {
    localStorage.setItem('jgh_theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  };

  // Toast notification helper
  const addToast = useCallback(({ type = 'info', message, title }) => {
    const id = `toast-${Date.now()}-${Math.random().toString(36).substr(2, 4)}`;
    setToasts(prev => [...prev, { id, type, message, title }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 4500);
  }, []);

  const handleDismissToast = (id) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  };

  // ── Bookmark / Save Query ──
  const handleBookmarkQuery = (question, sql) => {
    if (!question) return;
    const exists = savedQueries.some(q => q.question === question);
    if (exists) {
      setSavedQueries(prev => prev.filter(q => q.question !== question));
      addToast({ type: 'info', message: 'Query removed from bookmarks.' });
    } else {
      setSavedQueries(prev => [...prev, { question, sql: sql || '', savedAt: new Date().toISOString() }]);
      addToast({ type: 'success', message: 'Query pinned to Saved Queries!' });
    }
  };

  const handleRemoveBookmark = (question) => {
    setSavedQueries(prev => prev.filter(q => q.question !== question));
    addToast({ type: 'info', message: 'Query removed from bookmarks.' });
  };

  // ── Send Message to AI Engine ──
  const handleSendMessage = async (question) => {
    if (!question?.trim()) return;

    const userMsg = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: question,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMsg]);
    setIsProcessing(true);

    try {
      const response = await fetch('/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Incognito-Mode': isPrivate ? 'true' : 'false'
        },
        body: JSON.stringify({
          question,
          execute: true,
          is_private: isPrivate,
          session_id: isPrivate ? `private_${Date.now()}` : 'default_session',
          user_id: userRole.toLowerCase().replace(/\s+/g, '_')
        })
      });

      if (!response.ok) {
        throw new Error(`Server returned HTTP ${response.status}`);
      }

      const data = await response.json();

      const aiMsg = {
        id: `ai-${Date.now()}`,
        role: 'ai',
        content: data.summary || data.message || data.status,
        data,
        error: data.status === 'error' && !data.sql_query,
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, aiMsg]);

      if (data.status === 'success') {
        addToast({
          type: 'success',
          message: `Query verified & executed in ${data.execution_time || 0} ms (${data.rows_returned || 0} rows).`
        });
      }

    } catch (err) {
      console.error('Query execution error:', err);
      setMessages(prev => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          role: 'ai',
          content: `Unable to connect to AI engine: ${err.message}`,
          data: { status: 'error', message: err.message },
          error: true,
          timestamp: new Date().toISOString()
        }
      ]);
      addToast({
        type: 'error',
        title: 'Connection Error',
        message: 'Could not communicate with the backend server. Please verify the API is running.'
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleReRunQuery = (question) => {
    setActiveTab('chat');
    handleSendMessage(question);
  };

  const handleNewChat = () => {
    setMessages([]);
    addToast({ type: 'info', message: 'Started fresh query session.' });
  };

  if (!isAuthenticated) {
    return <Login onLogin={() => setIsAuthenticated(true)} />;
  }

  return (
    <div className={`app-shell ${theme === 'light' ? 'light-mode' : 'dark-mode'}`}>
      {/* ── Left Collapsible Sidebar ── */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onNewChat={handleNewChat}
        userRole={userRole}
        savedCount={savedQueries.length}
      />

      {/* ── Main Layout ── */}
      <div className="app-main-layout">
        {/* Top Header */}
        <Header
          activeTab={activeTab}
          isPrivate={isPrivate}
          setIsPrivate={setIsPrivate}
          userRole={userRole}
          setUserRole={setUserRole}
          onNewSession={handleNewChat}
          theme={theme}
          toggleTheme={toggleTheme}
        />

        {/* ── View Router ── */}
        <main className="app-content-view">
          {activeTab === 'chat' && (
            <CenterChat
              messages={messages}
              onSendMessage={handleSendMessage}
              isProcessing={isProcessing}
              isPrivate={isPrivate}
              savedQueries={savedQueries}
              onBookmarkQuery={handleBookmarkQuery}
              isQueryBookmarked={(q) => savedQueries.some(s => s.question === q)}
              onToast={addToast}
            />
          )}

          {activeTab === 'dashboard' && (
            <DashboardPage onToast={addToast} />
          )}

          {activeTab === 'architecture' && (
            <ArchitectureView onToast={addToast} />
          )}

          {activeTab === 'history' && (
            <HistoryView
              onReRun={handleReRunQuery}
              onToast={addToast}
            />
          )}

          {activeTab === 'reports' && (
            <ReportsPage onToast={addToast} />
          )}

          {activeTab === 'schema' && (
            <DatabaseSchemaPanel onToast={addToast} />
          )}

          {activeTab === 'saved' && (
            <SavedQueriesView
              savedQueries={savedQueries}
              onReRun={handleReRunQuery}
              onRemoveBookmark={handleRemoveBookmark}
              onToast={addToast}
            />
          )}

          {activeTab === 'settings' && (
            <Settings onToast={addToast} />
          )}

          {activeTab === 'admin' && (
            <AdminPanel onToast={addToast} />
          )}

          {activeTab === 'health' && (
            <AdminPanel onToast={addToast} />
          )}

          {activeTab === 'alerts' && (
            <DashboardPage onToast={addToast} />
          )}

          {activeTab === 'copilot' && (
            <CenterChat
              messages={messages}
              onSendMessage={handleSendMessage}
              isProcessing={isProcessing}
              isPrivate={isPrivate}
              savedQueries={savedQueries}
              onBookmarkQuery={handleBookmarkQuery}
              isQueryBookmarked={(q) => savedQueries.some(s => s.question === q)}
              onToast={addToast}
            />
          )}
        </main>
      </div>

      {/* ── Global Toast Notifications ── */}
      <ToastContainer toasts={toasts} onDismiss={handleDismissToast} />
    </div>
  );
}

export default App;
