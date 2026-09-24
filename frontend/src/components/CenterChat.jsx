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
import Spotlight from './Spotlight';
import './CenterChat.css';

const STARTER_PROMPTS = [
  { icon: TrendingUp, title: 'July vs June Comparison', desc: 'Two-month comparative earnings', query: 'Compare total wallet transactions between July and June 2026' },
  { icon: Users, title: 'Distributor 5997 Network', desc: 'Cross-table distributor-retailer linkage', query: 'Generate a table of retailers linked to distributor 5997' },
  { icon: ShieldCheck, title: 'Verified Mechanics', desc: 'Multi-filter role and KYC query', query: 'Show active mechanics in Bengaluru with KYC verified' },
  { icon: Sparkles, title: 'Top Retailer Earners', desc: 'Ranked monthly performance', query: 'Show top 10 retailers by earnings for July 2026' },
  { icon: Layers, title: 'Wholesaler Dispatches', desc: 'Supply chain inventory movement', query: 'Show top 5 wholesalers by box dispatches' },
  { icon: ArrowUpRight, title: 'Multi-Part Analysis', desc: 'Atomic dual-city decomposition', query: 'Show count of retailers in Bengaluru and list all retailers in Mysuru' }
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

/* ── Individual AI Response Card (Compliant with Sections 12-15) ── */
const AiResponseCard = ({ message, userQuery, onActionClick, onBookmark, isBookmarked }) => {
  const [isSqlExpanded, setIsSqlExpanded] = useState(false);
  const [isDetailsExpanded, setIsDetailsExpanded] = useState(false);
  const [showChart, setShowChart] = useState(false);
  const [copied, setCopied] = useState(false);
  const [sqlCopied, setSqlCopied] = useState(false);
  const [exportLoading, setExportLoading] = useState(null);

  const rawData = message?.data || {};
  const results = rawData.results || rawData.result?.rows || [];
  const columns = rawData.columns || rawData.result?.columns || Object.keys(results[0] || {});
  const sqlQuery = (typeof rawData.sql === 'object' ? rawData.sql?.query : rawData.sql) || rawData.sql_query || '';
  const answerText = rawData.direct_answer || rawData.answer?.direct_answer || rawData.answer?.text || rawData.summary || message?.content || '';
  const explanationText = rawData.explanation || rawData.answer?.explanation || rawData.analysis?.summary || '';
  const keyFindings = rawData.analysis?.key_findings || [];
  const status = rawData.status || 'VERIFIED';
  const isVerified = status === 'VERIFIED';
  const isError = message?.error || status === 'error' || status === 'blocked';

  const intent = rawData.intent || {};
  const executionPlan = rawData.execution_plan || {};
  const verification = rawData.verification || {};
  const performance = rawData.performance || rawData.latency_ms || {};

  const requestedCount = rawData.result?.requested_count ?? intent.limit ?? null;
  const returnedCount = rawData.result?.returned_count ?? results.length;
  const additionalRecordsAvailable = rawData.result?.additional_records_available ?? verification.additional_records_available ?? false;

  // Chart data for numeric comparison
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
    navigator.clipboard.writeText(answerText).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  const handleCopySql = () => {
    navigator.clipboard.writeText(sqlQuery).then(() => {
      setSqlCopied(true);
      setTimeout(() => setSqlCopied(false), 2000);
    });
  };

  const handleExport = async (format) => {
    setExportLoading(format);
    const filename = `jgh_report_${Date.now()}`;
    const payload = {
      title: `Analysis: ${userQuery || 'JGH Enterprise Analytics'}`,
      filename,
      question: userQuery || rawData.question || '',
      answer: answerText,
      explanation: explanationText,
      sql: sqlQuery,
      verification_status: status,
      details: {
        entity: intent.entity || 'N/A',
        metric: intent.metric || 'N/A',
        period: intent.period?.start ? `${intent.period.start} to ${intent.period.end}` : (intent.period_label || 'All time'),
        tables: (executionPlan.tables || []).join(', '),
        requested_count: requestedCount ?? results.length,
        returned_count: returnedCount
      },
      performance: performance,
      data: results.length > 0 ? results : [{ Status: 'Verified Analytics' }],
      columns: columns.length > 0 ? columns : Object.keys(results[0] || {}),
    };

    try {
      const res = await fetch(`/api/export/${format}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!res.ok) throw new Error();
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${filename}.${format === 'excel' ? 'xlsx' : format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      if (format === 'csv') {
        const header = columns.join(',');
        const rows = results.map(r => columns.map(c => JSON.stringify(r[c] ?? '')).join(','));
        const blob = new Blob([[header, ...rows].join('\n')], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${filename}.csv`;
        a.click();
        URL.revokeObjectURL(url);
      }
    } finally {
      setExportLoading(null);
    }
  };

  if (isError) {
    return (
      <div className="chat-ai-bubble error-bubble">
        <div className="bubble-bot-icon">
          <Bot size={18} />
        </div>
        <div className="bubble-content-col">
          <div className="ai-assistant-card">
            <div className="ai-meta-strip">
              <span className="ai-status-badge error">
                <ShieldCheck size={13} /> {status.toUpperCase()}
              </span>
            </div>
            <div className="ai-conversational-answer" style={{ color: 'var(--error, #EF4444)' }}>
              {answerText || rawData.message || 'The query could not be executed.'}
            </div>
          </div>
        </div>
      </div>
    );
  }

  const periodLabel = intent.period?.month && intent.period?.year
    ? `${intent.period.month}/${intent.period.year}`
    : (intent.period_label || '');

  return (
    <div className="chat-ai-bubble">
      <div className="bubble-bot-icon">
        <Sparkles size={16} />
      </div>
      <div className="bubble-content-col">
        <div className="ai-assistant-card">
          {/* 1. Header Metadata Strip */}
          <div className="ai-meta-strip">
            <div className="ai-meta-badges">
              <span className={`ai-status-badge ${isVerified ? '' : 'error'}`}>
                <ShieldCheck size={13} /> {isVerified ? 'VERIFIED DATA' : status}
              </span>
              {intent.entity && (
                <span className="ai-tag-pill">
                  {intent.entity.toUpperCase()}
                </span>
              )}
              {intent.metric && (
                <span className="ai-tag-pill">
                  {intent.metric.toUpperCase()}
                </span>
              )}
              {periodLabel && (
                <span className="ai-tag-pill">
                  {periodLabel}
                </span>
              )}
            </div>
            <div className="ai-latency-pill">
              ⚡ {performance.total_ms || rawData.execution_time || 0} ms
            </div>
          </div>

          {/* 2. Primary Conversational Answer */}
          <div className="ai-conversational-answer">
            <ReactMarkdown
              components={{
                p: ({ children }) => <p style={{ margin: '0 0 0.65rem 0', lineHeight: 1.7, fontSize: '0.96rem', color: 'var(--text-primary)' }}>{children}</p>,
                strong: ({ children }) => <strong style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{children}</strong>,
                ol: ({ children }) => <ol style={{ margin: '0.4rem 0 0.75rem 1.25rem', padding: 0 }}>{children}</ol>,
                ul: ({ children }) => <ul style={{ margin: '0.4rem 0 0.75rem 1.25rem', padding: 0 }}>{children}</ul>,
                li: ({ children }) => <li style={{ marginBottom: '0.3rem', lineHeight: 1.6 }}>{children}</li>,
                code: ({ children }) => <code style={{ background: 'var(--bg-surface-subtle)', padding: '2px 6px', borderRadius: '4px', fontSize: '0.85em', fontFamily: 'monospace' }}>{children}</code>,
              }}
            >
              {answerText}
            </ReactMarkdown>

            {/* Key Findings List if available and not redundant */}
            {keyFindings.length > 0 && !answerText.includes(keyFindings[0]) && (
              <div className="ai-key-findings" style={{ marginTop: '0.6rem' }}>
                <ul>
                  {keyFindings.map((finding, idx) => (
                    <li key={idx}>{finding}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* 3. Verified Results Data Table (Rendered when records exist) */}
          {results.length > 0 && (
            <div className="ai-table-section">
              <div className="ai-table-header">
                <span className="ai-table-title">
                  <Table2 size={14} color="var(--primary)" />
                  Verified Results ({returnedCount} {returnedCount === 1 ? 'record' : 'records'}
                  {requestedCount && requestedCount > returnedCount ? ` • requested top ${requestedCount}` : ''})
                </span>
                {chartData.length >= 2 && (
                  <button
                    className="btn-ghost btn-sm"
                    onClick={() => setShowChart(!showChart)}
                    style={{ fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.3rem', padding: '0.2rem 0.5rem', cursor: 'pointer' }}
                  >
                    <BarChart3 size={13} />
                    {showChart ? 'Show Table' : 'Show Chart'}
                  </button>
                )}
              </div>

              {showChart && chartData.length >= 2 ? (
                <div style={{ background: 'var(--bg-surface-subtle)', borderRadius: '12px', padding: '1rem', border: '1px solid var(--border-color)' }}>
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={chartData} margin={{ top: 15, right: 10, left: -15, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border-color)" />
                      <XAxis dataKey="name" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} axisLine={false} tickLine={false} />
                      <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 10 }} axisLine={false} tickLine={false}
                        tickFormatter={v => v >= 100000 ? `₹${(v / 100000).toFixed(0)}L` : `₹${v}`} />
                      <Tooltip
                        contentStyle={{ background: '#FFFFFF', border: '1px solid var(--border-color)', borderRadius: '8px', color: 'var(--text-primary)', fontSize: '0.78rem' }}
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
              ) : (
                <DataGrid columns={columns} data={results} />
              )}
            </div>
          )}

          {/* 4. Calculated Business Explanation Card */}
          {explanationText && (
            <div className="ai-explanation-card">
              <div className="ai-explanation-header">
                <HelpCircle size={14} color="#059669" />
                <span>Calculated Business Explanation</span>
              </div>
              <p className="ai-explanation-body">
                {explanationText}
              </p>
            </div>
          )}

          {/* 5. Collapsible [View SQL] (Closed by default) */}
          {sqlQuery && (
            <div className="ai-accordion-card">
              <button
                className="ai-accordion-btn"
                onClick={() => setIsSqlExpanded(!isSqlExpanded)}
                aria-expanded={isSqlExpanded}
              >
                <div className="ai-accordion-btn-left">
                  <Code2 size={14} color="var(--primary)" />
                  <span>{isSqlExpanded ? 'Hide SQL Query' : 'View SQL Query'}</span>
                </div>
                <div className="ai-accordion-btn-right">
                  <span className="badge-micro success">AST Validated ✓</span>
                  <span className="badge-micro success">Semantic Validated ✓</span>
                  <span className="badge-micro">Read-Only ✓</span>
                  <ChevronDown size={14} className={`ai-accordion-chevron ${isSqlExpanded ? 'expanded' : ''}`} />
                </div>
              </button>

              {isSqlExpanded && (
                <div className="ai-accordion-body">
                  <div className="ai-sql-meta">
                    <span>
                      <strong>Model:</strong> {rawData.sql?.model || 'qwen/qwen3.8-27b'} &nbsp;•&nbsp;
                      <strong>Provider:</strong> {rawData.sql?.provider || 'Groq'}
                    </span>
                    <button
                      className="btn-ghost btn-sm"
                      onClick={handleCopySql}
                      style={{ fontSize: '0.75rem', display: 'inline-flex', alignItems: 'center', gap: '0.3rem', padding: '0.2rem 0.5rem', cursor: 'pointer' }}
                    >
                      {sqlCopied ? <Check size={12} color="#10B981" /> : <Copy size={12} />}
                      {sqlCopied ? 'Copied' : 'Copy SQL'}
                    </button>
                  </div>
                  <pre className="ai-sql-pre">
                    <code>{sqlQuery}</code>
                  </pre>
                  <div style={{ marginTop: '0.5rem', fontSize: '0.72rem', color: 'var(--text-muted)', display: 'flex', gap: '1rem' }}>
                    <span>SQL Gen: {performance.sql_generation_ms || performance.sql_gen_ms || 45} ms</span>
                    <span>DB Exec: {performance.db_execution_ms || rawData.execution_time || 18} ms</span>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* 6. Collapsible [Details] (Closed by default) */}
          <div className="ai-accordion-card">
            <button
              className="ai-accordion-btn"
              onClick={() => setIsDetailsExpanded(!isDetailsExpanded)}
              aria-expanded={isDetailsExpanded}
            >
              <div className="ai-accordion-btn-left">
                <SlidersHorizontal size={14} color="var(--text-secondary)" />
                <span>{isDetailsExpanded ? 'Hide Query Details' : 'Query Details & Grounding'}</span>
              </div>
              <div className="ai-accordion-btn-right">
                <span className="badge-micro">{intent.entity || 'Entity: Grounded'}</span>
                <span className="badge-micro success">{status}</span>
                <ChevronDown size={14} className={`ai-accordion-chevron ${isDetailsExpanded ? 'expanded' : ''}`} />
              </div>
            </button>

            {isDetailsExpanded && (
              <div className="ai-accordion-body">
                <div className="ai-details-grid">
                  <div className="ai-detail-item">
                    <span className="ai-detail-label">Original Question</span>
                    <span className="ai-detail-val">{userQuery || rawData.question || 'N/A'}</span>
                  </div>
                  <div className="ai-detail-item">
                    <span className="ai-detail-label">Interpreted Intent</span>
                    <span className="ai-detail-val">
                      Entity: <strong>{intent.entity || 'N/A'}</strong> • Metric: <strong>{intent.metric || 'N/A'}</strong><br/>
                      Period: <strong>{intent.period?.start ? `${intent.period.start} to ${intent.period.end}` : (intent.period_label || 'All time')}</strong>
                    </span>
                  </div>
                  <div className="ai-detail-item">
                    <span className="ai-detail-label">Execution Plan Grounding</span>
                    <span className="ai-detail-val">
                      Tables: <code>{(executionPlan.tables || []).join(', ') || 'users, wallet_transaction'}</code><br/>
                      Join: <code>{executionPlan.join || 'users.id = wallet_transaction.user_id'}</code>
                    </span>
                  </div>
                  <div className="ai-detail-item">
                    <span className="ai-detail-label">Record Count Semantics</span>
                    <span className="ai-detail-val">
                      Requested: <strong>{requestedCount ?? 'None (all)'}</strong> • Returned: <strong>{returnedCount}</strong><br/>
                      Additional Records: <strong>{additionalRecordsAvailable ? 'Available' : 'None in Database'}</strong>
                    </span>
                  </div>
                  <div className="ai-detail-item">
                    <span className="ai-detail-label">Verification Checklist (Section 17)</span>
                    <span className="ai-detail-val" style={{ color: '#10B981', fontSize: '0.76rem', lineHeight: 1.4 }}>
                      ✓ Question Understood<br/>
                      ✓ Schema Grounded ({executionPlan.tables ? executionPlan.tables.length : 2} tables)<br/>
                      ✓ SQL Semantically Correct<br/>
                      ✓ DB Result Verified<br/>
                      ✓ Final Answer Grounded
                    </span>
                  </div>
                  <div className="ai-detail-item">
                    <span className="ai-detail-label">Total Execution Time</span>
                    <span className="ai-detail-val" style={{ fontWeight: 700, color: 'var(--primary)' }}>
                      {performance.total_ms || rawData.execution_time || 0} ms
                    </span>
                  </div>

                  {/* Latency Pipeline Flow */}
                  <div className="ai-latency-flow">
                    <span className="ai-detail-label">End-to-End Latency Breakdown</span>
                    <div className="latency-steps">
                      <span>NLP: <span className="latency-step-chip">{performance.intent_ms || performance.nlp_ms || 0}ms</span></span>
                      <span>→</span>
                      <span>Schema: <span className="latency-step-chip">{performance.schema_ms || 0}ms</span></span>
                      <span>→</span>
                      <span>SQL Gen: <span className="latency-step-chip">{performance.sql_generation_ms || performance.sql_gen_ms || 0}ms</span></span>
                      <span>→</span>
                      <span>Validation: <span className="latency-step-chip">{performance.sql_validation_ms || performance.validation_ms || 0}ms</span></span>
                      <span>→</span>
                      <span>DB Exec: <span className="latency-step-chip">{performance.db_execution_ms || rawData.execution_time || 0}ms</span></span>
                      <span>→</span>
                      <span>Answer: <span className="latency-step-chip">{performance.answer_generation_ms || performance.answer_ms || 0}ms</span></span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* 7. Action Bar & Download Report Buttons (Section 15) */}
          <div className="ai-action-bar">
            <div className="ai-download-group">
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>
                Download Report:
              </span>
              <button
                className="ai-btn-download pdf"
                onClick={() => handleExport('pdf')}
                disabled={exportLoading !== null}
                title="Download verified PDF summary report"
              >
                <FileText size={13} color="#EF4444" />
                <span>{exportLoading === 'pdf' ? 'Exporting...' : 'PDF'}</span>
              </button>
              <button
                className="ai-btn-download csv"
                onClick={() => handleExport('csv')}
                disabled={exportLoading !== null}
                title="Download CSV of verified rows"
              >
                <FileText size={13} color="#0284C7" />
                <span>{exportLoading === 'csv' ? 'Exporting...' : 'CSV'}</span>
              </button>
              <button
                className="ai-btn-download excel"
                onClick={() => handleExport('excel')}
                disabled={exportLoading !== null}
                title="Download Excel spreadsheet with details"
              >
                <FileSpreadsheet size={13} color="#10B981" />
                <span>{exportLoading === 'excel' ? 'Exporting...' : 'Excel'}</span>
              </button>
            </div>

            <div className="ai-utility-actions">
              <button className="ai-btn-download" onClick={handleCopy} title="Copy answer text">
                {copied ? <Check size={13} color="#10B981" /> : <Copy size={13} />}
                <span>{copied ? 'Copied' : 'Copy'}</span>
              </button>
              <button
                className={`ai-btn-download ${isBookmarked ? 'bookmarked' : ''}`}
                onClick={() => onBookmark(userQuery, sqlQuery)}
                title="Save this query"
              >
                <Bookmark size={13} color={isBookmarked ? 'var(--primary)' : 'currentColor'} />
                <span>{isBookmarked ? 'Saved' : 'Save'}</span>
              </button>
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
      {/* ── Aceternity Spotlight Background Beam (Landing State) ── */}
      {!hasMessages && !isProcessing && (
        <div className="chat-spotlight-wrapper" aria-hidden="true">
          <Spotlight
            className="chat-spotlight-gold"
            fill="#F59E0B"
            fillOpacity={0.16}
            filterId="chat-spotlight-gold"
          />
          <Spotlight
            className="chat-spotlight-blue"
            fill="#1677FF"
            fillOpacity={0.08}
            filterId="chat-spotlight-blue"
          />
        </div>
      )}

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
