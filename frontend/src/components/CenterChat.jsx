import React, { useState, useRef, useEffect, useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import {
  Search, Send, Mic, MicOff, Bookmark, Download, FileSpreadsheet,
  FileText, Code2, BarChart3, Table2, Sparkles, SlidersHorizontal,
  ArrowRight, Lightbulb, CheckCircle2, TrendingUp, ShieldCheck,
  Database, HelpCircle, Layers, ArrowUpRight, Copy, Check,
  ChevronDown, RefreshCw, User, Users, Bot, Pencil, X
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell
} from 'recharts';
import DataGrid from './DataGrid';
import AutoChart from './AutoChart';
import StepProgressLoader from './StepProgressLoader';
import './CenterChat.css';

const STARTER_PROMPTS = [
  { icon: TrendingUp, title: 'Earnings', desc: 'Revenue & transaction insights', query: 'Compare Karnataka and Kerala distributor earnings' },
  { icon: Users, title: 'Distributors', desc: 'User growth and activity', query: 'List top 10 distributors' },
  { icon: ArrowUpRight, title: 'Withdrawals', desc: 'Pending & approved requests', query: 'Show pending withdrawal requests' },
  { icon: Layers, title: 'Inventory', desc: 'Stock and supply metrics', query: 'Show inventory levels' },
  { icon: BarChart3, title: 'Performance', desc: 'Overall business growth', query: 'What was the percentage change in approved payouts?' },
  { icon: FileSpreadsheet, title: 'Payouts', desc: 'Financial disbursements', query: 'Show approved payouts for August' }
];

/* ── User Message Bubble with Edit ── */
const UserBubble = ({ content, onEdit }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editText, setEditText] = useState(content);
  const editRef = useRef(null);

  useEffect(() => {
    if (isEditing && editRef.current) {
      editRef.current.focus();
      editRef.current.select();
    }
  }, [isEditing]);

  const handleSave = () => {
    if (editText.trim() && editText.trim() !== content) {
      onEdit(editText.trim());
    }
    setIsEditing(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSave(); }
    if (e.key === 'Escape') { setEditText(content); setIsEditing(false); }
  };

  return (
    <div className="chat-user-bubble">
      {isEditing ? (
        <div className="user-edit-wrap">
          <textarea
            ref={editRef}
            className="user-edit-textarea"
            value={editText}
            onChange={e => setEditText(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={2}
          />
          <div className="user-edit-actions">
            <button className="user-edit-cancel" onClick={() => { setEditText(content); setIsEditing(false); }}>
              <X size={13} /> Cancel
            </button>
            <button className="user-edit-save" onClick={handleSave}>
              <Send size={13} /> Send
            </button>
          </div>
        </div>
      ) : (
        <div className="user-bubble-inner">
          <button
            className="user-edit-btn"
            onClick={() => setIsEditing(true)}
            title="Edit this message"
          >
            <Pencil size={13} />
          </button>
          <div className="user-bubble-text">{content}</div>
        </div>
      )}
      <div className="chat-user-icon">
        <User size={16} />
      </div>
    </div>
  );
};

/* ── Individual AI Response Card ── */
const AiResponseCard = ({ message, userQuery, onActionClick, onBookmark, isBookmarked }) => {
  const [activeTab, setActiveTab] = useState(() => {
    const q = (userQuery || '').toLowerCase();
    return (q.includes('table') || q.includes('list') || q.includes('grid')) ? 'table' : 'overview';
  });
  const [copied, setCopied] = useState(false);
  const [showExport, setShowExport] = useState(false);

  const rawData = message?.data || {};
  const results = rawData.results || [];
  const summary = rawData.summary || message?.content || '';
  const sqlQuery = rawData.sql_query || rawData.sql || '';
  const columns = rawData.columns || Object.keys(results[0] || {});
  const isError = message?.error;

  // Build KPI cards from results
  const kpiCards = useMemo(() => {
    if (!results.length) return [];
    const row = results[0];
    const cards = [];

    if (row.percentage_change !== undefined || row.july_2026_payouts !== undefined) {
      const v1 = Number(row.july_2026_payouts ?? row.july_2026_earnings ?? 0);
      const v2 = Number(row.august_2026_payouts ?? row.august_2026_earnings ?? 0);
      const diff = v2 - v1;
      const pct = row.percentage_change ?? (v1 > 0 ? +((v2 - v1) / v1 * 100).toFixed(2) : 0);
      cards.push(
        { label: 'July 2026', value: `₹${v1.toLocaleString()}`, trend: null, color: '#10B981' },
        { label: 'August 2026', value: `₹${v2.toLocaleString()}`, trend: null, color: '#2563EB' },
        { label: 'Net Change', value: `${diff < 0 ? '-' : '+'}₹${Math.abs(diff).toLocaleString()}`, trend: diff < 0 ? 'down' : 'up', color: diff < 0 ? '#EF4444' : '#10B981' },
        { label: '% Change', value: `${pct > 0 ? '+' : ''}${pct}%`, trend: pct < 0 ? 'down' : 'up', color: pct < 0 ? '#EF4444' : '#10B981' }
      );
    } else if (row.state_name !== undefined && results.length >= 2) {
      results.slice(0, 2).forEach(r => {
        cards.push({ label: r.state_name, value: `₹${Number(r.total_earnings || 0).toLocaleString()}`, sub: `${r.total_users || 0} distributors`, trend: null, color: '#2563EB' });
        cards.push({ label: `${r.state_name} Avg/Dist`, value: `₹${Number(r.avg_earnings_per_user || 0).toLocaleString()}`, trend: null, color: '#8B5CF6' });
      });
    } else if (results.length === 1) {
      const r = results[0];
      if (r.total_earnings !== undefined) cards.push({ label: 'Total Earnings', value: `₹${Number(r.total_earnings).toLocaleString()}`, trend: null, color: '#10B981' });
      if (r.name) cards.push({ label: 'Name', value: r.name, trend: null, color: '#2563EB' });
      if (r.city) cards.push({ label: 'Location', value: r.city, trend: null, color: '#8B5CF6' });
      if (r.user_id || r.id) cards.push({ label: 'User ID', value: String(r.user_id || r.id), trend: null, color: '#D97706' });
    } else if (results.length > 1) {
      const total = results.reduce((s, r) => s + Number(r.total_earnings || r.amount || 0), 0);
      if (total > 0) cards.push({ label: 'Total Value', value: `₹${total.toLocaleString()}`, trend: null, color: '#10B981' });
      cards.push({ label: 'Records', value: `${results.length}`, trend: null, color: '#2563EB' });
    }
    return cards;
  }, [results]);

  // Chart data
  const chartData = useMemo(() => {
    if (!results.length) return [];
    if (results[0].state_name) return results.map(r => ({ name: r.state_name, value: Number(r.total_earnings || 0) }));
    if (results[0].july_2026_payouts !== undefined) {
      const r = results[0];
      return [
        { name: 'July 2026', value: Number(r.july_2026_payouts ?? r.july_2026_earnings ?? 0) },
        { name: 'August 2026', value: Number(r.august_2026_payouts ?? r.august_2026_earnings ?? 0) }
      ];
    }
    return results.slice(0, 8).map(r => ({
      name: r.name || r.city || `ID ${r.user_id || r.id}`,
      value: Number(r.total_earnings || r.wallet_balance || r.amount || 0)
    })).filter(d => d.value > 0);
  }, [results]);

  const handleCopy = () => {
    navigator.clipboard.writeText(summary).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  const handleExport = async (format) => {
    setShowExport(false);
    const data = results.length > 0 ? results : [{ Status: 'Verified Analytics' }];
    const filename = `jgh_export_${Date.now()}`;
    try {
      const res = await fetch(`/export/${format}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data, columns: columns.length > 0 ? columns : Object.keys(data[0]), filename })
      });
      if (!res.ok) throw new Error();
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = `${filename}.${format === 'excel' ? 'xlsx' : format}`; a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      if (format === 'csv') {
        const header = columns.join(',');
        const rows = data.map(r => columns.map(c => JSON.stringify(r[c] ?? '')).join(','));
        const blob = new Blob([[header, ...rows].join('\n')], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a'); a.href = url; a.download = `${filename}.csv`; a.click();
        URL.revokeObjectURL(url);
      }
    }
  };

  if (isError) {
    return (
      <div className="chat-ai-bubble error-bubble">
        <div className="bubble-bot-icon">
          <Bot size={18} />
        </div>
        <div className="bubble-content-col">
          <div className="error-text">{summary || 'Something went wrong. Please try again.'}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="chat-ai-bubble">
      <div className="bubble-bot-icon">
        <Sparkles size={16} />
      </div>
      <div className="bubble-content-col">
        <div className="bubble-card">
          {/* Tab Panels */}
          {activeTab === 'overview' && (
            <div className="bubble-overview-panel">
              {/* KPI Cards Row */}
              {kpiCards.length > 0 && (
                <div className="bubble-kpi-row">
                  {kpiCards.slice(0, 4).map((kpi, i) => (
                    <div key={i} className="kpi-card">
                      <span className="kpi-card-label">{kpi.label}</span>
                      <span className="kpi-card-value" style={{ color: kpi.color }}>{kpi.value}</span>
                      {kpi.sub && <span className="kpi-card-sub">{kpi.sub}</span>}
                      {kpi.trend === 'down' && <span className="kpi-trend down">▼ Decrease</span>}
                      {kpi.trend === 'up' && <span className="kpi-trend up">▲ Increase</span>}
                    </div>
                  ))}
                </div>
              )}

              {/* Inline Chart (if enough data) */}
              {chartData.length >= 2 && (
                <div className="bubble-inline-chart">
                  <ResponsiveContainer width="100%" height={180}>
                    <BarChart data={chartData} margin={{ top: 15, right: 10, left: -15, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border-color)" />
                      <XAxis dataKey="name" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} axisLine={false} tickLine={false} />
                      <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 10 }} axisLine={false} tickLine={false}
                        tickFormatter={v => v >= 100000 ? `₹${(v / 100000).toFixed(0)}L` : `₹${v}`} />
                      <Tooltip
                        contentStyle={{ background: '#FFFFFF', border: '1px solid var(--border-color)', borderRadius: '8px', color: 'var(--text-primary)', fontSize: '0.78rem', boxShadow: 'var(--shadow-md)' }}
                        formatter={v => [`₹${Number(v).toLocaleString()}`, 'Amount']}
                      />
                      <Bar dataKey="value" radius={[6, 6, 0, 0]} barSize={36}>
                        {chartData.map((_, i) => (
                          <Cell key={i} fill={['#1677FF', '#10B981', '#8B5CF6', '#F59E0B'][i % 4]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}

              {/* Text Summary */}
              {summary && (
                <div className="bubble-summary-text">
                  {chartData.length > 0 || kpiCards.length > 0 ? (
                    <div className="summary-label">What this means</div>
                  ) : null}
                  <ReactMarkdown
                    components={{
                      p: ({ children }) => <p style={{ margin: '0 0 0.75rem 0', lineHeight: 1.7, fontSize: '0.9375rem', color: 'var(--text-primary)' }}>{children}</p>,
                      strong: ({ children }) => <strong style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{children}</strong>,
                      h1: ({ children }) => <h3 style={{ fontSize: '1.125rem', fontWeight: 600, margin: '1rem 0 0.5rem', color: 'var(--text-primary)', fontFamily: 'var(--font-display)' }}>{children}</h3>,
                      h2: ({ children }) => <h4 style={{ fontSize: '1rem', fontWeight: 600, margin: '0.75rem 0 0.5rem', color: 'var(--text-primary)', fontFamily: 'var(--font-display)' }}>{children}</h4>,
                      h3: ({ children }) => <h5 style={{ fontSize: '0.9375rem', fontWeight: 600, margin: '0.75rem 0 0.5rem', color: 'var(--text-primary)', fontFamily: 'var(--font-display)' }}>{children}</h5>,
                      ul: ({ children }) => <ul style={{ margin: '0.3rem 0', paddingLeft: '1.25rem' }}>{children}</ul>,
                      li: ({ children }) => <li style={{ marginBottom: '0.2rem', lineHeight: 1.55 }}>{children}</li>,
                      code: ({ children }) => <code style={{ background: 'var(--bg-surface-subtle)', padding: '2px 6px', borderRadius: '4px', fontSize: '0.85em', fontFamily: 'monospace' }}>{children}</code>,
                    }}
                  >{summary}</ReactMarkdown>
                </div>
              )}
            </div>
          )}

          {activeTab === 'chart' && chartData.length >= 2 && (
            <div className="bubble-tab-panel">
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={chartData} margin={{ top: 15, right: 10, left: -15, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border-color)" />
                  <XAxis dataKey="name" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 10 }} axisLine={false} tickLine={false}
                    tickFormatter={v => v >= 100000 ? `₹${(v / 100000).toFixed(0)}L` : `₹${v}`} />
                  <Tooltip
                    contentStyle={{ background: '#FFFFFF', border: '1px solid var(--border-color)', borderRadius: '8px', color: 'var(--text-primary)', fontSize: '0.78rem', boxShadow: 'var(--shadow-md)' }}
                    formatter={v => [`₹${Number(v).toLocaleString()}`, 'Amount']}
                  />
                  <Bar dataKey="value" radius={[6, 6, 0, 0]} barSize={44}>
                    {chartData.map((_, i) => (
                      <Cell key={i} fill={['#1677FF', '#10B981', '#8B5CF6', '#F59E0B'][i % 4]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {activeTab === 'table' && results.length > 0 && (
            <div className="bubble-tab-panel">
              <DataGrid columns={columns} data={results} />
            </div>
          )}

          {activeTab === 'sql' && sqlQuery && (
            <div className="bubble-tab-panel">
              <pre className="bubble-sql-block"><code>{sqlQuery}</code></pre>
            </div>
          )}

          {/* Tab Bar at the Bottom */}
          {(results.length > 0 || sqlQuery) && (
            <div className="bubble-tabs-wrap">
              <div className="bubble-tabs-bar">
                <button className={`bubble-tab ${activeTab === 'overview' ? 'active' : ''}`} onClick={() => setActiveTab('overview')}>
                  ✨ Executive Brief
                </button>
                {results.length > 0 && (
                  <button className={`bubble-tab ${activeTab === 'table' ? 'active' : ''}`} onClick={() => setActiveTab('table')}>
                    📊 Data {results.length > 0 && <span className="tab-count">{results.length}</span>}
                  </button>
                )}
                {chartData.length >= 2 && (
                  <button className={`bubble-tab ${activeTab === 'chart' ? 'active' : ''}`} onClick={() => setActiveTab('chart')}>
                    📈 Chart
                  </button>
                )}
                {sqlQuery && (
                  <button className={`bubble-tab ${activeTab === 'sql' ? 'active' : ''}`} onClick={() => setActiveTab('sql')}>
                    Code <Code2 size={13} style={{marginLeft: '4px'}}/>
                  </button>
                )}
              </div>
            </div>
          )}

        {/* Action Buttons Row */}
        <div className="bubble-actions-row">
          <button className="bubble-action-btn" onClick={handleCopy} title="Copy response">
            {copied ? <Check size={13} /> : <Copy size={13} />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>

          <div style={{ position: 'relative' }}>
            <button className="bubble-action-btn" onClick={() => setShowExport(!showExport)} title="Export data">
              <Download size={13} />
              <span>Export</span>
              <ChevronDown size={11} />
            </button>
            {showExport && (
              <div className="bubble-export-menu">
                <button onClick={() => handleExport('csv')}><FileText size={12} color="#0284C7" /> CSV</button>
                <button onClick={() => handleExport('excel')}><FileSpreadsheet size={12} color="#10B981" /> Excel</button>
                <button onClick={() => handleExport('pdf')}><FileText size={12} color="#EF4444" /> PDF</button>
              </div>
            )}
          </div>

          <button
            className={`bubble-action-btn ${isBookmarked ? 'bookmarked' : ''}`}
            onClick={() => onBookmark(userQuery, sqlQuery)}
            title="Save query"
          >
            <Bookmark size={13} />
            <span>{isBookmarked ? 'Saved' : 'Save'}</span>
          </button>

          <div className="bubble-meta">
            <CheckCircle2 size={12} color="#10B981" />
            <span>Verified SQL · {rawData.execution_time ? `${rawData.execution_time} ms` : ''} · {results.length} rows</span>
          </div>
        </div>
        </div>
      </div>
    </div>
  );
};

/* ── Main CenterChat Component ── */
const CenterChat = ({
  messages = [],
  onSendMessage,
  isProcessing = false,
  isPrivate = false,
  onBookmarkQuery,
  isQueryBookmarked = () => false
}) => {
  const [inputText, setInputText] = useState('');
  const [isListening, setIsListening] = useState(false);
  const scrollRef = useRef(null);
  const inputRef = useRef(null);
  const recognitionRef = useRef(null);

  const hasMessages = messages.length > 0;

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isProcessing]);

  // Voice recognition setup
  useEffect(() => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SR) {
      const r = new SR();
      r.continuous = false; r.interimResults = false; r.lang = 'en-IN';
      r.onresult = e => { setInputText(e.results[0][0].transcript); setIsListening(false); };
      r.onerror = r.onend = () => setIsListening(false);
      recognitionRef.current = r;
    }
  }, []);

  const toggleVoice = () => {
    if (!recognitionRef.current) return;
    if (isListening) { recognitionRef.current.stop(); setIsListening(false); }
    else { recognitionRef.current.start(); setIsListening(true); }
  };

  const handleSubmit = (e) => {
    e?.preventDefault();
    const q = inputText.trim();
    if (!q || isProcessing) return;
    onSendMessage(q);
    setInputText('');
  };

  const handleQuickAsk = (q) => {
    if (isProcessing) return;
    onSendMessage(q);
  };

  // Build message pairs for rendering
  const renderedPairs = useMemo(() => {
    const pairs = [];
    for (let i = 0; i < messages.length; i++) {
      if (messages[i].role === 'user') {
        pairs.push({ user: messages[i], ai: messages[i + 1]?.role === 'ai' ? messages[i + 1] : null });
        if (messages[i + 1]?.role === 'ai') i++;
      }
    }
    return pairs;
  }, [messages]);

  return (
    <div className="chat-container">
      {/* ── Scrollable Chat Area ── */}
      <div className="chat-scroll-area" ref={scrollRef}>
          <div className="chat-workspace-grid">
            <div className="chat-main-column">
              {/* Empty / Landing State */}
              {!hasMessages && !isProcessing && (
                <div className="chat-landing-content">
                  <div className="landing-header-row">
                    <div className="landing-badge">
                      <Sparkles size={14} className="primary-sparkle" />
                      <span>JGH Intelligence</span>
                    </div>
                  </div>
                  
                  <h2 className="landing-title">Ask your business data anything</h2>
                  <p className="landing-subtitle">Get verified insights, reports and answers from your business data using natural language.</p>
                  
                  {/* Landing Input Area */}
                  <div className="landing-input-container">
                    <form onSubmit={handleSubmit} className="landing-input-form hover-3d">
                      <div className="landing-input-box">
                        <Search size={22} className="landing-search-icon" />
                        <textarea
                          ref={inputRef}
                          className="landing-textarea"
                          value={inputText}
                          onChange={e => setInputText(e.target.value)}
                          onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSubmit(); } }}
                          placeholder="Ask anything about your business data..."
                          rows={1}
                        />
                        <div className="landing-input-actions">
                          <button
                            type="button"
                            className={`input-icon-btn ${isListening ? 'listening' : ''}`}
                            onClick={toggleVoice}
                            title="Voice input"
                          >
                            {isListening ? <MicOff size={20} color="var(--error)" /> : <Mic size={20} />}
                          </button>
                          <button
                            type="submit"
                            className={`landing-ask-btn ${inputText.trim() ? 'ready' : ''}`}
                            disabled={!inputText.trim() || isProcessing}
                          >
                            <span>Ask JGH</span> <ArrowRight size={18} />
                          </button>
                        </div>
                      </div>
                    </form>
                  </div>
                </div>
              )}

              {/* Conversation Messages */}
              {(hasMessages || isProcessing) && (
                <div className="chat-messages-full">
                  {renderedPairs.map((pair, idx) => (
                    <div key={idx} className="chat-pair">
                      {/* User Bubble with Edit Button */}
                      <UserBubble
                        content={pair.user.content}
                        onEdit={(newText) => {
                          if (newText.trim()) handleQuickAsk(newText.trim());
                        }}
                      />

                      {/* AI Response */}
                      {pair.ai && (
                        <AiResponseCard
                          message={pair.ai}
                          userQuery={pair.user.content}
                          onActionClick={handleQuickAsk}
                          onBookmark={onBookmarkQuery}
                          isBookmarked={isQueryBookmarked(pair.user.content)}
                        />
                      )}
                    </div>
                  ))}

                  {/* Loading indicator */}
                  {isProcessing && (
                    <div className="chat-pair">
                      <div className="chat-ai-bubble">
                        <div className="bubble-bot-icon">
                          <Sparkles size={16} />
                        </div>
                        <div className="bubble-content-col">
                          <StepProgressLoader isProcessing={true} />
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Right Side Column (3D Visualization & Insights) */}
            <div className="chat-side-column">
              <div className="ai-visualization-panel">
                <div className="ai-orb-container-side">
                  <div className="ai-orb"></div>
                  <div className="ai-orb-ring"></div>
                  <div className="ai-orb-glow"></div>
                </div>
                <div className="ai-status-overlay">
                  <div className="status-dot"></div>
                  <span>AI Engine Ready</span>
                </div>
              </div>

              <div className="side-insights-panel">
                <h4 className="side-insights-title">
                  <Lightbulb size={16} color="var(--warning)" />
                  Suggested Insights
                </h4>
                <div className="side-suggested-list">
                  {STARTER_PROMPTS.map((prompt, i) => (
                    <button key={i} className="side-action-card hover-3d" onClick={() => handleQuickAsk(prompt.query)}>
                      <div className="side-icon-wrap">
                        <prompt.icon size={16} />
                      </div>
                      <div className="side-card-content">
                        <span className="side-card-title">{prompt.title}</span>
                        <span className="side-card-desc">{prompt.desc}</span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
      </div>

      {/* ── Fixed Bottom Input Bar (Only visible when chatting) ── */}
      {(hasMessages || isProcessing) && (
        <div className="chat-input-area-full">
          <div className="chat-input-area-inner">
            {/* Suggested Follow-ups */}
            {hasMessages && !isProcessing && (
              <div className="followup-chips-strip">
                <Lightbulb size={13} color="#E5A93C" />
                <button className="followup-chip" onClick={() => handleQuickAsk('Show details for top record')}>Show top record details</button>
                <button className="followup-chip" onClick={() => handleQuickAsk('Compare with last month')}>Compare last month</button>
                <button className="followup-chip" onClick={() => handleQuickAsk('Show full list as table')}>Show full data table</button>
              </div>
            )}

            {/* Main Input Form */}
            <form onSubmit={handleSubmit} className="chat-input-form-full">
              <div className="chat-input-box-full">
                <textarea
                  ref={inputRef}
                  className="chat-textarea-full"
                  value={inputText}
                  onChange={e => setInputText(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSubmit(); } }}
                  placeholder="Ask a follow-up question..."
                  rows={1}
                />
                <div className="chat-input-actions-full">
                  <button
                    type="button"
                    className={`input-icon-btn ${isListening ? 'listening' : ''}`}
                    onClick={toggleVoice}
                    title="Voice input"
                  >
                    {isListening ? <MicOff size={17} color="#EF4444" /> : <Mic size={17} />}
                  </button>
                  <button
                    type="submit"
                    className={`chat-send-btn ${inputText.trim() ? 'ready' : ''}`}
                    disabled={!inputText.trim() || isProcessing}
                    title="Send"
                  >
                    <Send size={16} strokeWidth={2.5} />
                  </button>
                </div>
              </div>
            </form>
            <p className="chat-disclaimer">AI Copilot may make mistakes. Always verify critical data before action.</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default CenterChat;
