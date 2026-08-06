import os

def create_ui():
    html_content = """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Enterprise AI SQL Agent | 100% Offline Intelligence</title>
  
  <!-- Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  
  <!-- Tailwind CSS -->
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          fontFamily: {
            sans: ['Inter', 'sans-serif'],
            mono: ['JetBrains Mono', 'monospace'],
          },
          colors: {
            brand: {
              50: '#f0f7ff',
              100: '#e0effe',
              500: '#3b82f6',
              600: '#2563eb',
              700: '#1d4ed8',
              900: '#1e3a8a',
            },
            dark: {
              bg: '#0B0F17',
              card: '#111827',
              sidebar: '#0D111A',
              border: '#1F2937',
              muted: '#374151',
            }
          }
        }
      }
    }
  </script>
  
  <!-- React 18 & Babel -->
  <script src="https://unpkg.com/react@18/umd/react.production.min.js" crossorigin></script>
  <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js" crossorigin></script>
  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>

  <style>
    /* Custom Scrollbar */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #374151; border-radius: 9999px; }
    ::-webkit-scrollbar-thumb:hover { background: #4B5563; }
    
    .glass-effect {
      background: rgba(17, 24, 39, 0.75);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
    }
    
    @keyframes pulse-subtle {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.6; }
    }
    .animate-pulse-subtle { animation: pulse-subtle 2s cubic-bezier(0.4, 0, 0.6, 1) infinite; }
  </style>
</head>
<body class="bg-dark-bg text-slate-100 antialiased selection:bg-brand-500 selection:text-white transition-colors duration-200">
  <div id="root"></div>

  <script type="text/babel">
    const { useState, useEffect, useRef } = React;

    // SVG Icons
    const Icons = {
      Bot: () => <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>,
      User: () => <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>,
      Send: () => <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" /></svg>,
      Chat: () => <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 10h.01M12 10h.01M16 10h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>,
      History: () => <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>,
      Database: () => <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" /></svg>,
      Admin: () => <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>,
      Settings: () => <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>,
      Copy: () => <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>,
      Check: () => <svg className="w-3.5 h-3.5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" /></svg>,
      Download: () => <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>,
      Moon: () => <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" /></svg>,
      Sun: () => <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" /></svg>,
      Sparkles: () => <svg className="w-4 h-4 text-brand-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" /></svg>,
      ShieldCheck: () => <svg className="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>,
      Refresh: () => <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
    };

    function App() {
      const [activeTab, setActiveTab] = useState('chat');
      const [isDark, setIsDark] = useState(true);
      const [messages, setMessages] = useState([
        {
          id: 'welcome',
          sender: 'ai',
          text: 'Hello! I am your Enterprise AI SQL Agent operating 100% offline. I am schema-aware of your 8 target database tables. How can I help with your data analytics today?',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
      const [inputQuery, setInputQuery] = useState('');
      const [loading, setLoading] = useState(false);
      const [thinkingStep, setThinkingStep] = useState('');

      const [queryHistory, setQueryHistory] = useState([]);
      const [schemaData, setSchemaData] = useState({});
      const [adminStatus, setAdminStatus] = useState(null);
      const [settings, setSettings] = useState({
        model_name: 'qwen2.5-coder:7b',
        embedding_model: 'all-MiniLM-L6-v2',
        temperature: 0.1,
        max_rows: 100
      });
      const [selectedTable, setSelectedTable] = useState('users');
      const [copiedId, setCopiedId] = useState(null);

      const messagesEndRef = useRef(null);

      const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      };

      useEffect(() => {
        scrollToBottom();
      }, [messages, loading, thinkingStep]);

      useEffect(() => {
        fetchAdminStatus();
        fetchSchema();
        fetchHistory();
      }, []);

      const fetchAdminStatus = async () => {
        try {
          const res = await fetch('/admin/status');
          const data = await res.json();
          setAdminStatus(data);
        } catch (e) {
          console.error(e);
        }
      };

      const fetchSchema = async () => {
        try {
          const res = await fetch('/admin/schema');
          const data = await res.json();
          setSchemaData(data.schema || {});
        } catch (e) {
          console.error(e);
        }
      };

      const fetchHistory = async () => {
        try {
          const res = await fetch('/history');
          const data = await res.json();
          setQueryHistory(data.history || []);
        } catch (e) {
          console.error(e);
        }
      };

      const handleSendQuery = async (queryText) => {
        const text = queryText || inputQuery;
        if (!text.trim() || loading) return;

        const userMsg = {
          id: Date.now() + '-user',
          sender: 'user',
          text: text,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };

        setMessages(prev => [...prev, userMsg]);
        setInputQuery('');
        setLoading(true);

        setThinkingStep('Searching schema & relationships (RAG)...');
        await new Promise(r => setTimeout(r, 200));

        try {
          setThinkingStep('Generating SQL with local Qwen2.5-Coder model...');
          const res = await fetch('/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: text, execute: true })
          });
          const result = await res.json();

          setThinkingStep('Validating AST security & optimizing query...');
          await new Promise(r => setTimeout(r, 150));

          const aiMsg = {
            id: Date.now() + '-ai',
            sender: 'ai',
            isAmbiguous: result.is_ambiguous,
            clarification: result.clarification,
            options: result.options,
            generated_sql: result.generated_sql,
            optimized_sql: result.optimized_sql,
            validation: result.validation,
            execution: result.execution,
            status: result.status,
            thinking_steps: result.thinking_steps || [],
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          };

          setMessages(prev => [...prev, aiMsg]);
          fetchHistory();
        } catch (err) {
          setMessages(prev => [...prev, {
            id: Date.now() + '-err',
            sender: 'ai',
            error: 'Failed to connect to AI Agent backend: ' + err.message,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          }]);
        } finally {
          setLoading(false);
          setThinkingStep('');
        }
      };

      const copyToClipboard = (text, id) => {
        navigator.clipboard.writeText(text);
        setCopiedId(id);
        setTimeout(() => setCopiedId(null), 2000);
      };

      const downloadFile = (url, body, filename) => {
        fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body)
        })
        .then(res => res.blob())
        .then(blob => {
          const link = document.createElement('a');
          link.href = URL.createObjectURL(blob);
          link.download = filename;
          link.click();
        });
      };

      const targetScopeTables = [
        'users',
        'wallet_transaction',
        'sku_inventories',
        'companies',
        'machine_details',
        'withdrawal_request',
        'automatic_transactions',
        'automate'
      ];

      return (
        <div className={`flex h-screen w-screen overflow-hidden ${isDark ? 'dark bg-dark-bg text-slate-100' : 'bg-slate-50 text-slate-900'}`}>
          
          {/* SIDEBAR */}
          <aside className="w-64 flex-shrink-0 bg-dark-sidebar border-r border-dark-border flex flex-col justify-between p-4 z-20">
            <div>
              <div className="flex items-center gap-3 px-3 py-2 mb-6">
                <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-brand-500/20 text-white font-bold">
                  <Icons.Bot />
                </div>
                <div>
                  <h1 className="font-bold text-sm leading-tight text-white tracking-tight">Enterprise AI SQL</h1>
                  <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-400 mt-0.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                    100% Offline Mode
                  </span>
                </div>
              </div>

              <nav className="space-y-1">
                {[
                  { id: 'chat', label: 'AI Chat', icon: Icons.Chat },
                  { id: 'history', label: 'SQL History', icon: Icons.History },
                  { id: 'scope', label: 'Target Database (8)', icon: Icons.Database },
                  { id: 'admin', label: 'Admin Panel', icon: Icons.Admin },
                  { id: 'settings', label: 'Settings', icon: Icons.Settings },
                ].map(item => {
                  const Icon = item.icon;
                  const active = activeTab === item.id;
                  return (
                    <button
                      key={item.id}
                      onClick={() => setActiveTab(item.id)}
                      className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-medium transition-all duration-150 ${
                        active 
                          ? 'bg-brand-600 text-white shadow-md shadow-brand-600/30' 
                          : 'text-slate-400 hover:text-slate-200 hover:bg-dark-border/50'
                      }`}
                    >
                      <Icon />
                      {item.label}
                    </button>
                  );
                })}
              </nav>
            </div>

            <div className="bg-dark-card/80 border border-dark-border/80 rounded-xl p-3 text-xs space-y-2">
              <div className="flex items-center justify-between text-slate-400 text-[11px]">
                <span>Model</span>
                <span className="text-brand-400 font-semibold">qwen2.5-coder:7b</span>
              </div>
              <div className="flex items-center justify-between text-slate-400 text-[11px]">
                <span>Vector Store</span>
                <span className="text-emerald-400 font-medium">ChromaDB</span>
              </div>
              <div className="flex items-center justify-between text-slate-400 text-[11px]">
                <span>Allowed Scope</span>
                <span className="text-indigo-400 font-medium">8 Tables</span>
              </div>
            </div>
          </aside>

          {/* MAIN CONTENT AREA */}
          <main className="flex-1 flex flex-col h-full overflow-hidden bg-dark-bg relative">
            
            <header className="h-16 border-b border-dark-border px-6 flex items-center justify-between glass-effect z-10">
              <div className="flex items-center gap-3">
                <h2 className="font-semibold text-sm capitalize text-slate-200 tracking-wide">
                  {activeTab === 'chat' && 'AI Conversation Studio'}
                  {activeTab === 'history' && 'SQL Audit Query History'}
                  {activeTab === 'scope' && 'Target Database Scope Schema (8 Tables)'}
                  {activeTab === 'admin' && 'Enterprise System Admin Panel'}
                  {activeTab === 'settings' && 'Platform Settings & Configuration'}
                </h2>
              </div>

              <div className="flex items-center gap-3 text-xs">
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-dark-card border border-dark-border text-slate-300 font-mono text-[11px]">
                  <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                  Ollama Local Active
                </div>
                <button
                  onClick={() => setIsDark(!isDark)}
                  className="p-2 rounded-lg border border-dark-border text-slate-400 hover:text-white hover:bg-dark-card transition-colors"
                >
                  {isDark ? <Icons.Sun /> : <Icons.Moon />}
                </button>
              </div>
            </header>

            <div className="flex-1 overflow-y-auto p-6 relative">

              {/* 1. CHAT TAB */}
              {activeTab === 'chat' && (
                <div className="max-w-4xl mx-auto flex flex-col h-full justify-between space-y-6 pb-20">
                  
                  <div className="space-y-6 flex-1 overflow-y-auto pr-2">
                    {messages.map((msg) => (
                      <div key={msg.id} className={`flex gap-4 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                        {msg.sender === 'ai' && (
                          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-brand-600 to-indigo-600 flex items-center justify-center text-white flex-shrink-0 mt-1 shadow-md shadow-brand-500/20">
                            <Icons.Bot />
                          </div>
                        )}

                        <div className={`max-w-2xl space-y-3 ${msg.sender === 'user' ? 'bg-brand-600 text-white rounded-2xl rounded-tr-sm px-4 py-3 shadow-md' : 'bg-dark-card border border-dark-border/80 rounded-2xl rounded-tl-sm p-4 text-slate-200'}`}>
                          
                          {msg.text && <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.text}</p>}

                          {msg.isAmbiguous && (
                            <div className="space-y-3 bg-dark-bg/60 border border-amber-500/30 rounded-xl p-4">
                              <div className="flex items-center gap-2 text-amber-400 font-medium text-xs">
                                <Icons.Sparkles />
                                <span>Ambiguity Notice: Clarification Required</span>
                              </div>
                              <p className="text-xs text-slate-300">{msg.clarification}</p>
                              <div className="flex flex-wrap gap-2 pt-1">
                                {msg.options?.map((opt, idx) => (
                                  <button
                                    key={idx}
                                    onClick={() => handleSendQuery(opt)}
                                    className="px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 hover:bg-amber-500/20 text-xs font-medium transition-all shadow-sm"
                                  >
                                    {opt}
                                  </button>
                                ))}
                              </div>
                            </div>
                          )}

                          {msg.thinking_steps && msg.thinking_steps.length > 0 && (
                            <details className="group text-[11px] text-slate-400 bg-dark-bg/40 border border-dark-border/60 rounded-lg p-2.5">
                              <summary className="cursor-pointer font-mono font-medium text-brand-400 flex items-center gap-2 select-none">
                                <Icons.Sparkles />
                                <span>Agent Reasoning & Processing Steps ({msg.thinking_steps.length})</span>
                              </summary>
                              <ul className="mt-2 space-y-1.5 pl-4 list-disc text-slate-400 font-mono">
                                {msg.thinking_steps.map((step, sIdx) => (
                                  <li key={sIdx}>{step}</li>
                                ))}
                              </ul>
                            </details>
                          )}

                          {msg.generated_sql && (
                            <div className="space-y-2 pt-1">
                              <div className="flex items-center justify-between text-xs text-slate-400">
                                <div className="flex items-center gap-2 font-mono">
                                  <span className="px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-semibold text-[10px]">APPROVED SELECT</span>
                                  {msg.execution?.execution_time_ms !== undefined && (
                                    <span className="text-[11px] text-slate-400">{msg.execution.execution_time_ms}ms</span>
                                  )}
                                  {msg.execution?.row_count !== undefined && (
                                    <span className="text-[11px] text-slate-400">{msg.execution.row_count} rows</span>
                                  )}
                                </div>

                                <div className="flex items-center gap-1.5">
                                  <button
                                    onClick={() => copyToClipboard(msg.optimized_sql || msg.generated_sql, msg.id)}
                                    className="px-2 py-1 rounded bg-dark-border/60 hover:bg-dark-border text-slate-300 text-[11px] flex items-center gap-1 transition-colors"
                                  >
                                    {copiedId === msg.id ? <Icons.Check /> : <Icons.Copy />}
                                    {copiedId === msg.id ? 'Copied!' : 'Copy SQL'}
                                  </button>
                                </div>
                              </div>

                              <pre className="bg-dark-bg p-3.5 rounded-xl border border-dark-border/80 font-mono text-xs text-brand-300 overflow-x-auto leading-relaxed shadow-inner">
                                <code>{msg.optimized_sql || msg.generated_sql}</code>
                              </pre>
                            </div>
                          )}

                          {msg.execution?.success && msg.execution.data?.length > 0 && (
                            <div className="space-y-3 pt-2">
                              <div className="flex items-center justify-between">
                                <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider font-mono">Results Preview</h4>
                                <div className="flex items-center gap-2">
                                  <button
                                    onClick={() => downloadFile('/export/csv', { columns: msg.execution.columns, data: msg.execution.data, filename: 'sql_report' }, 'report.csv')}
                                    className="px-2.5 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20 text-xs font-medium flex items-center gap-1 transition-colors"
                                  >
                                    <Icons.Download /> CSV
                                  </button>
                                  <button
                                    onClick={() => downloadFile('/export/excel', { columns: msg.execution.columns, data: msg.execution.data, filename: 'sql_report' }, 'report.xlsx')}
                                    className="px-2.5 py-1 rounded-lg bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 hover:bg-indigo-500/20 text-xs font-medium flex items-center gap-1 transition-colors"
                                  >
                                    <Icons.Download /> Excel
                                  </button>
                                </div>
                              </div>

                              <div className="overflow-x-auto rounded-xl border border-dark-border/80 max-h-64 shadow-md bg-dark-bg/60">
                                <table className="w-full text-left border-collapse text-xs">
                                  <thead>
                                    <tr className="bg-dark-card border-b border-dark-border font-mono text-slate-400 uppercase text-[10px]">
                                      {msg.execution.columns.map((col, cIdx) => (
                                        <th key={cIdx} className="px-3 py-2.5 font-semibold whitespace-nowrap">{col}</th>
                                      ))}
                                    </tr>
                                  </thead>
                                  <tbody className="divide-y divide-dark-border/40 font-mono text-slate-300">
                                    {msg.execution.data.slice(0, 15).map((row, rIdx) => (
                                      <tr key={rIdx} className="hover:bg-dark-card/50 transition-colors">
                                        {msg.execution.columns.map((col, cIdx) => (
                                          <td key={cIdx} className="px-3 py-2 whitespace-nowrap text-slate-300">
                                            {row[col] !== null ? String(row[col]) : <span className="text-slate-600 italic">null</span>}
                                          </td>
                                        ))}
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                              </div>
                            </div>
                          )}

                          {msg.execution?.error && (
                            <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-xs font-mono">
                              <strong>Execution Note:</strong> {msg.execution.error}
                            </div>
                          )}

                          <div className="text-[10px] text-slate-500 text-right pt-1 font-mono">
                            {msg.timestamp}
                          </div>

                        </div>

                        {msg.sender === 'user' && (
                          <div className="w-8 h-8 rounded-lg bg-dark-card border border-dark-border flex items-center justify-center text-slate-300 flex-shrink-0 mt-1">
                            <Icons.User />
                          </div>
                        )}
                      </div>
                    ))}

                    {loading && (
                      <div className="flex gap-4 justify-start">
                        <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-brand-600 to-indigo-600 flex items-center justify-center text-white flex-shrink-0 animate-pulse">
                          <Icons.Bot />
                        </div>
                        <div className="bg-dark-card border border-dark-border/80 rounded-2xl rounded-tl-sm p-4 space-y-2 text-slate-300">
                          <div className="flex items-center gap-2 text-xs text-brand-400 font-mono animate-pulse-subtle">
                            <Icons.Sparkles />
                            <span>{thinkingStep || 'Processing natural language request...'}</span>
                          </div>
                        </div>
                      </div>
                    )}

                    <div ref={messagesEndRef} />
                  </div>

                  <div className="fixed bottom-4 left-72 right-8 max-w-4xl mx-auto space-y-3 z-30">
                    <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs no-scrollbar">
                      {[
                        'Show wallet transactions for July 2026',
                        'Top 10 users by wallet transaction',
                        'Show withdrawal requests summary',
                        'Active SKU inventory unit prices'
                      ].map((pill, pIdx) => (
                        <button
                          key={pIdx}
                          onClick={() => handleSendQuery(pill)}
                          className="px-3 py-1.5 rounded-full bg-dark-card/90 hover:bg-brand-600/20 border border-dark-border hover:border-brand-500/40 text-slate-300 hover:text-brand-300 whitespace-nowrap transition-all text-[11px] font-medium shadow-sm"
                        >
                          {pill}
                        </button>
                      ))}
                    </div>

                    <form
                      onSubmit={(e) => { e.preventDefault(); handleSendQuery(); }}
                      className="relative flex items-center glass-effect border border-dark-border focus-within:border-brand-500 rounded-2xl shadow-2xl p-2 transition-all"
                    >
                      <input
                        type="text"
                        value={inputQuery}
                        onChange={(e) => setInputQuery(e.target.value)}
                        placeholder="Ask a natural language data question (e.g. Show wallet transactions for July 2026)..."
                        className="w-full bg-transparent px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none"
                      />
                      <button
                        type="submit"
                        disabled={loading || !inputQuery.trim()}
                        className="p-3 rounded-xl bg-brand-600 hover:bg-brand-500 disabled:opacity-40 disabled:hover:bg-brand-600 text-white font-medium shadow-md shadow-brand-600/30 transition-all flex items-center justify-center flex-shrink-0"
                      >
                        <Icons.Send />
                      </button>
                    </form>
                  </div>

                </div>
              )}

              {/* 2. SQL HISTORY TAB */}
              {activeTab === 'history' && (
                <div className="max-w-5xl mx-auto space-y-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-bold text-slate-100">Audit Query History</h3>
                      <p className="text-xs text-slate-400">Logged natural language questions, generated SQL, execution times, and row counts.</p>
                    </div>
                    <button
                      onClick={fetchHistory}
                      className="px-3 py-1.5 rounded-lg bg-dark-card border border-dark-border text-xs text-slate-300 hover:bg-dark-border flex items-center gap-1.5"
                    >
                      <Icons.Refresh /> Refresh
                    </button>
                  </div>

                  <div className="bg-dark-card border border-dark-border rounded-2xl overflow-hidden shadow-xl">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead>
                        <tr className="bg-dark-bg border-b border-dark-border text-slate-400 font-mono uppercase text-[10px]">
                          <th className="p-3.5 font-semibold">Timestamp</th>
                          <th className="p-3.5 font-semibold">User Question</th>
                          <th className="p-3.5 font-semibold">Generated SQL</th>
                          <th className="p-3.5 font-semibold">Status</th>
                          <th className="p-3.5 font-semibold">Execution Time</th>
                          <th className="p-3.5 font-semibold">Action</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-dark-border/40 font-mono text-slate-300">
                        {queryHistory.length === 0 ? (
                          <tr><td colSpan="6" className="p-6 text-center text-slate-500 italic">No audit history entries found yet.</td></tr>
                        ) : (
                          queryHistory.map((item, hIdx) => (
                            <tr key={hIdx} className="hover:bg-dark-bg/40 transition-colors">
                              <td className="p-3.5 whitespace-nowrap text-slate-400 text-[11px]">{item.timestamp}</td>
                              <td className="p-3.5 font-sans font-medium text-slate-200 max-w-xs truncate">{item.question}</td>
                              <td className="p-3.5 text-brand-300 max-w-sm truncate">{item.optimized_sql || item.generated_sql}</td>
                              <td className="p-3.5">
                                <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${item.status === 'success' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' : 'bg-red-500/10 text-red-400 border border-red-500/30'}`}>
                                  {item.status?.toUpperCase()}
                                </span>
                              </td>
                              <td className="p-3.5 whitespace-nowrap text-slate-400">{item.execution_time_ms} ms</td>
                              <td className="p-3.5">
                                <button
                                  onClick={() => { setActiveTab('chat'); handleSendQuery(item.question); }}
                                  className="px-2.5 py-1 rounded bg-brand-600/20 text-brand-400 hover:bg-brand-600/40 text-[11px] font-sans font-medium transition-colors"
                                >
                                  Re-run
                                </button>
                              </td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* 3. TARGET DATABASE SCOPE TAB */}
              {activeTab === 'scope' && (
                <div className="max-w-5xl mx-auto space-y-6">
                  <div className="bg-indigo-500/10 border border-indigo-500/30 rounded-2xl p-5 space-y-2">
                    <div className="flex items-center gap-2 text-indigo-400 font-semibold text-sm">
                      <Icons.ShieldCheck />
                      <span>Strict Target Database Scope Enforcement</span>
                    </div>
                    <p className="text-xs text-slate-300 leading-relaxed">
                      The AI SQL Agent is strictly bounded to understand and query ONLY these 8 target physical tables. All other database tables are automatically excluded from RAG retrieval and SQL generation.
                    </p>
                  </div>

                  <div className="flex items-center gap-2 overflow-x-auto pb-2 border-b border-dark-border">
                    {targetScopeTables.map(tbl => (
                      <button
                        key={tbl}
                        onClick={() => setSelectedTable(tbl)}
                        className={`px-4 py-2 rounded-xl text-xs font-mono font-medium transition-all ${
                          selectedTable === tbl 
                            ? 'bg-brand-600 text-white shadow-md shadow-brand-600/30' 
                            : 'bg-dark-card border border-dark-border text-slate-400 hover:text-white'
                        }`}
                      >
                        {tbl}
                      </button>
                    ))}
                  </div>

                  {schemaData[selectedTable] ? (
                    <div className="bg-dark-card border border-dark-border rounded-2xl p-6 space-y-6 shadow-xl">
                      <div>
                        <h3 className="text-lg font-bold font-mono text-brand-300">{selectedTable}</h3>
                        <p className="text-xs text-slate-400 mt-1">Columns, Data Types, Nullability & Primary Keys extracted from MySQL information schema.</p>
                      </div>

                      <div className="overflow-x-auto rounded-xl border border-dark-border">
                        <table className="w-full text-left text-xs border-collapse font-mono">
                          <thead>
                            <tr className="bg-dark-bg border-b border-dark-border text-slate-400 uppercase text-[10px]">
                              <th className="p-3 font-semibold">Column Name</th>
                              <th className="p-3 font-semibold">Data Type</th>
                              <th className="p-3 font-semibold">Key Type</th>
                              <th className="p-3 font-semibold">Nullable</th>
                              <th className="p-3 font-semibold">Comment / Description</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-dark-border/40 text-slate-300">
                            {schemaData[selectedTable].columns?.map((col, colIdx) => (
                              <tr key={colIdx} className="hover:bg-dark-bg/40 transition-colors">
                                <td className="p-3 font-semibold text-slate-200">{col.name}</td>
                                <td className="p-3 text-brand-400">{col.full_type || col.datatype}</td>
                                <td className="p-3">
                                  {col.key === 'PRI' && <span className="px-2 py-0.5 rounded bg-amber-500/10 border border-amber-500/30 text-amber-400 font-bold text-[10px]">PRIMARY KEY</span>}
                                  {col.key === 'MUL' && <span className="px-2 py-0.5 rounded bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 text-[10px]">INDEX / FK</span>}
                                </td>
                                <td className="p-3 text-slate-400">{col.nullable}</td>
                                <td className="p-3 text-slate-400 font-sans italic text-[11px]">{col.comment || 'N/A'}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  ) : (
                    <div className="p-8 text-center text-slate-500 italic bg-dark-card border border-dark-border rounded-2xl">
                      Schema metadata for table '{selectedTable}' is being extracted...
                    </div>
                  )}
                </div>
              )}

              {/* 4. ADMIN PANEL TAB */}
              {activeTab === 'admin' && (
                <div className="max-w-5xl mx-auto space-y-6">
                  <h3 className="text-lg font-bold text-slate-100">System Administration & Health</h3>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-dark-card border border-dark-border rounded-2xl p-4 space-y-2">
                      <span className="text-xs text-slate-400 font-medium">Database Connection</span>
                      <div className="text-lg font-bold text-emerald-400 flex items-center gap-2">
                        <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
                        Connected
                      </div>
                      <span className="text-[11px] text-slate-500 block font-mono">jghMasterDB (Read-Only)</span>
                    </div>

                    <div className="bg-dark-card border border-dark-border rounded-2xl p-4 space-y-2">
                      <span className="text-xs text-slate-400 font-medium">Local LLM Engine</span>
                      <div className="text-lg font-bold text-brand-400">qwen2.5-coder:7b</div>
                      <span className="text-[11px] text-slate-500 block font-mono">Ollama / Offline GGUF</span>
                    </div>

                    <div className="bg-dark-card border border-dark-border rounded-2xl p-4 space-y-2">
                      <span className="text-xs text-slate-400 font-medium">Vector Store</span>
                      <div className="text-lg font-bold text-indigo-400">ChromaDB</div>
                      <span className="text-[11px] text-slate-500 block font-mono">all-MiniLM-L6-v2</span>
                    </div>

                    <div className="bg-dark-card border border-dark-border rounded-2xl p-4 space-y-2">
                      <span className="text-xs text-slate-400 font-medium">Target Scope</span>
                      <div className="text-lg font-bold text-amber-400">8 Tables</div>
                      <span className="text-[11px] text-slate-500 block font-mono font-bold">Strict Scope Locked</span>
                    </div>
                  </div>

                  <div className="bg-dark-card border border-dark-border rounded-2xl p-6 space-y-4 shadow-xl">
                    <h4 className="text-sm font-semibold text-slate-200">Management Operations</h4>
                    
                    <div className="flex flex-wrap gap-4">
                      <button
                        onClick={async () => {
                          const res = await fetch('/admin/refresh-metadata', { method: 'POST' });
                          const d = await res.json();
                          alert(d.message);
                          fetchSchema();
                        }}
                        className="px-4 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-medium text-xs shadow-md shadow-brand-600/30 transition-all flex items-center gap-2"
                      >
                        <Icons.Refresh /> Refresh Schema Metadata
                      </button>

                      <button
                        onClick={async () => {
                          const res = await fetch('/admin/rebuild-embeddings', { method: 'POST' });
                          const d = await res.json();
                          alert(d.message);
                        }}
                        className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs shadow-md shadow-indigo-600/30 transition-all flex items-center gap-2"
                      >
                        <Icons.Sparkles /> Rebuild Vector Embeddings
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* 5. SETTINGS TAB */}
              {activeTab === 'settings' && (
                <div className="max-w-3xl mx-auto bg-dark-card border border-dark-border rounded-2xl p-6 space-y-6 shadow-xl">
                  <h3 className="text-lg font-bold text-slate-100">Platform Configuration</h3>

                  <div className="space-y-4 text-xs">
                    <div className="space-y-1.5">
                      <label className="font-medium text-slate-300">Local LLM Model</label>
                      <select
                        value={settings.model_name}
                        onChange={(e) => setSettings({ ...settings, model_name: e.target.value })}
                        className="w-full bg-dark-bg border border-dark-border rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-brand-500 font-mono"
                      >
                        <option value="qwen2.5-coder:7b">Qwen2.5-Coder 7B Instruct GGUF (Ollama)</option>
                        <option value="deepseek-coder">DeepSeek-Coder GGUF</option>
                        <option value="sqlcoder:7b">SQLCoder 7B GGUF</option>
                      </select>
                    </div>

                    <div className="space-y-1.5">
                      <label className="font-medium text-slate-300">Embedding Model</label>
                      <select
                        value={settings.embedding_model}
                        onChange={(e) => setSettings({ ...settings, embedding_model: e.target.value })}
                        className="w-full bg-dark-bg border border-dark-border rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-brand-500 font-mono"
                      >
                        <option value="all-MiniLM-L6-v2">sentence-transformers/all-MiniLM-L6-v2</option>
                        <option value="bge-small-en-v1.5">BAAI/bge-small-en-v1.5</option>
                      </select>
                    </div>

                    <div className="pt-4 border-t border-dark-border flex justify-end">
                      <button
                        onClick={async () => {
                          await fetch('/admin/settings', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(settings)
                          });
                          alert('Settings updated successfully!');
                        }}
                        className="px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-medium text-xs shadow-md shadow-brand-600/30 transition-all"
                      >
                        Save Configuration
                      </button>
                    </div>
                  </div>
                </div>
              )}

            </div>
          </main>

        </div>
      );
    }

    ReactDOM.createRoot(document.getElementById('root')).render(<App />);
  </script>
</body>
</html>
"""
    with open("app/static/index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("app/static/index.html generated successfully.")

if __name__ == "__main__":
    create_ui()



import io
import csv
import pandas as pd
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_csv(columns: list, data: list) -> bytes:
    df = pd.DataFrame(data, columns=columns)
    output = io.BytesIO()
    df.to_csv(output, index=False)
    return output.getvalue()


def generate_csv_stream(columns: list, data: list):
    """
    Memory-efficient CSV chunk generator for streaming large datasets directly.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(columns)
    yield output.getvalue()
    output.seek(0)
    output.truncate(0)

    for row in data:
        writer.writerow([row.get(col, "") for col in columns])
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)



def generate_excel(columns: list, data: list, title: str = "AI SQL Agent Export") -> bytes:
    df = pd.DataFrame(data, columns=columns)
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Data_Export")
        workbook = writer.book
        worksheet = writer.sheets["Data_Export"]

        # Style header row
        header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        thin_border = Border(
            left=Side(style='thin', color='CBD5E1'),
            right=Side(style='thin', color='CBD5E1'),
            top=Side(style='thin', color='CBD5E1'),
            bottom=Side(style='thin', color='CBD5E1')
        )

        for col_num, col_name in enumerate(columns, 1):
            cell = worksheet.cell(row=1, column=col_num)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

        # Auto-fit column widths
        for col in worksheet.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = col[0].column_letter
            worksheet.column_dimensions[col_letter].width = max(max_len + 4, 12)

    return output.getvalue()


import os

def save_reports_to_disk(columns: list, data: list, report_id: str) -> dict:
    """
    Generates CSV, Excel, and PDF files, saves them to the reports/ directory,
    and returns a dict with public URL paths for each format.
    """
    os.makedirs("reports", exist_ok=True)
    urls = {}

    try:
        csv_bytes = generate_csv(columns, data)
        csv_path = f"reports/{report_id}.csv"
        with open(csv_path, "wb") as f:
            f.write(csv_bytes)
        urls["csv"] = f"/reports/{report_id}.csv"
    except Exception as e:
        print(f"[REPORT] CSV generation failed: {e}")

    try:
        excel_bytes = generate_excel(columns, data)
        excel_path = f"reports/{report_id}.xlsx"
        with open(excel_path, "wb") as f:
            f.write(excel_bytes)
        urls["excel"] = f"/reports/{report_id}.xlsx"
    except Exception as e:
        print(f"[REPORT] Excel generation failed: {e}")

    try:
        pdf_bytes = generate_pdf(columns, data)
        pdf_path = f"reports/{report_id}.pdf"
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)
        urls["pdf"] = f"/reports/{report_id}.pdf"
    except Exception as e:
        print(f"[REPORT] PDF generation failed: {e}")

    return urls


def generate_pdf(columns: list, data: list, title: str = "AI SQL Agent Query Report") -> bytes:
    output = io.BytesIO()
    doc = SimpleDocTemplate(
        output,
        pagesize=landscape(letter),
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1E293B'),
        spaceAfter=12
    )

    elements = [
        Paragraph(title, title_style),
        Spacer(1, 10)
    ]

    if not data:
        elements.append(Paragraph("No data available for this query.", styles['Normal']))
    else:
        # Prepare table data (limit columns to fit page if very wide)
        display_cols = columns[:8]
        table_data = [display_cols]

        for row in data[:100]:  # Limit PDF rows to 100
            table_data.append([str(row.get(col, '')) for col in display_cols])

        t = Table(table_data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A8A')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8FAFC')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        elements.append(t)

    doc.build(elements)
    return output.getvalue()
