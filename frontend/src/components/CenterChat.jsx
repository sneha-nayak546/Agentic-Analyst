import React, { useState, useRef, useEffect } from 'react';
import {
  Send, Bot, User, Copy, Check, Download, Table2, FileText,
  FileSpreadsheet, Clock, Hash, AlertCircle, CheckCircle2,
  ChevronRight, Loader2, Sparkles, Code2
} from 'lucide-react';
import DataGrid from './DataGrid';
import AutoChart from './AutoChart';
import './CenterChat.css';

/* ─── Section Header ─── */
const SectionHeader = ({ label }) => (
  <div className="response-section-header">
    <span className="response-section-label">{label}</span>
  </div>
);

/* ─── SQL Code Block ─── */
const SqlBlock = ({ sql }) => {
  const [copied, setCopied] = useState(false);
  if (!sql) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(sql);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="sql-code-block">
      <div className="sql-code-header">
        <div className="sql-code-label">
          <Code2 size={13} />
          <span>SQL</span>
        </div>
        <button className="sql-copy-btn" onClick={handleCopy}>
          {copied ? <Check size={13} /> : <Copy size={13} />}
          {copied ? 'Copied!' : 'Copy'}
        </button>
      </div>
      <pre className="sql-code-body"><code>{sql}</code></pre>
    </div>
  );
};

/* ─── Execution Status ─── */
const ExecutionStatus = ({ execTime, rowCount, status }) => {
  const isSuccess = status === 'success';
  return (
    <div className={`exec-status-card ${isSuccess ? 'success' : 'error'}`}>
      <div className="exec-status-main">
        {isSuccess
          ? <CheckCircle2 size={16} className="exec-icon success" />
          : <AlertCircle size={16} className="exec-icon error" />
        }
        <span className="exec-status-text">
          {isSuccess ? 'SQL Executed Successfully' : 'Execution Failed'}
        </span>
      </div>
      {isSuccess && (
        <div className="exec-meta">
          <div className="exec-meta-item">
            <Clock size={12} />
            <span>Execution Time: <strong>{execTime != null ? `${execTime} ms` : '—'}</strong></span>
          </div>
          <div className="exec-meta-item">
            <Hash size={12} />
            <span>Rows Returned: <strong>{rowCount != null ? rowCount : '—'}</strong></span>
          </div>
        </div>
      )}
    </div>
  );
};

/* ─── Download Buttons ─── */
const DownloadButtons = ({ reportUrls, columns, data }) => {
  const handleDirectDownload = (url) => {
    if (!url) return;
    const a = document.createElement('a');
    a.href = `http://localhost:8000${url}`;
    a.download = url.split('/').pop();
    a.click();
  };

  const handleExportFallback = async (type) => {
    try {
      const payload = { data, columns, filename: `report_${Date.now()}` };
      const res = await fetch(`http://localhost:8000/export/${type}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const ext = type === 'excel' ? 'xlsx' : type;
      a.download = `report_${Date.now()}.${ext}`;
      a.click();
    } catch (err) {
      console.error('Download error:', err);
    }
  };

  const hasUrls = reportUrls && Object.keys(reportUrls).length > 0;

  return (
    <div className="download-section">
      <div className="download-label">
        <Download size={13} />
        <span>Download Report</span>
      </div>
      <div className="download-btns">
        <button
          className="dl-btn csv"
          onClick={() => hasUrls && reportUrls.csv ? handleDirectDownload(reportUrls.csv) : handleExportFallback('csv')}
        >
          <FileText size={13} />
          CSV
        </button>
        <button
          className="dl-btn excel"
          onClick={() => hasUrls && reportUrls.excel ? handleDirectDownload(reportUrls.excel) : handleExportFallback('excel')}
        >
          <FileSpreadsheet size={13} />
          Excel (.xlsx)
        </button>
        <button
          className="dl-btn pdf"
          onClick={() => hasUrls && reportUrls.pdf ? handleDirectDownload(reportUrls.pdf) : handleExportFallback('pdf')}
        >
          <FileText size={13} />
          PDF
        </button>
      </div>
    </div>
  );
};

/* ─── AI Response Card (7 sections) ─── */
const AiResponseCard = ({ msg }) => {
  const d = msg.data; // parsed backend response object

  if (msg.error) {
    return (
      <div className="ai-card error-card">
        <AlertCircle size={15} className="error-icon" />
        <span>{msg.content}</span>
      </div>
    );
  }

  if (!d) {
    return <div className="ai-card"><span style={{ color: 'var(--text-secondary)' }}>{msg.content}</span></div>;
  }

  // Ambiguous query
  if (d.status === 'ambiguous') {
    return (
      <div className="ai-card">
        <div className="ambiguous-section">
          <Sparkles size={15} className="ambiguous-icon" />
          <p className="ambiguous-text">{d.summary || d.clarification}</p>
          {d.options?.length > 0 && (
            <div className="ambiguous-options">
              {d.options.map((opt, i) => (
                <button key={i} className="ambiguous-opt-btn">
                  <ChevronRight size={13} /> {opt}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  const isError = d.status === 'error';
  const hasResults = Array.isArray(d.results) && d.results.length > 0;
  const cols = d.columns || (hasResults ? Object.keys(d.results[0]) : []);

  return (
    <div className="ai-card">

      {/* ── Section 1: Question ── */}
      <SectionHeader label="Question" />
      <div className="response-question">{d.question}</div>

      {/* ── Section 2: Generated SQL ── */}
      <SectionHeader label="Generated SQL" />
      {d.sql_query
        ? <SqlBlock sql={d.sql_query} />
        : <div className="response-empty">No SQL generated.</div>
      }

      {/* ── Section 3: Execution Status ── */}
      <SectionHeader label="Execution Status" />
      <ExecutionStatus
        execTime={d.execution_time}
        rowCount={d.rows_returned}
        status={d.status}
      />

      {/* Error message */}
      {isError && d.message && (
        <div className="response-error-msg">
          <AlertCircle size={14} /> {d.message}
        </div>
      )}

      {/* ── Section 4: Results ── */}
      {!isError && (
        <>
          <SectionHeader label="Results" />
          {hasResults ? (
            <div className="response-table-wrap">
              <DataGrid columns={cols} data={d.results} />
            </div>
          ) : (
            <div className="response-empty">
              <Table2 size={16} />
              <span>No rows returned.</span>
            </div>
          )}
        </>
      )}

      {/* ── Section 5: Summary ── */}
      {!isError && d.summary && (
        <>
          <SectionHeader label="Summary" />
          <div className="response-summary">
            <Sparkles size={14} className="summary-icon" />
            <p>{d.summary}</p>
          </div>
        </>
      )}

      {/* ── Section 6: Download Report ── */}
      {!isError && hasResults && (
        <>
          <SectionHeader label="Download Report" />
          <DownloadButtons reportUrls={d.report_urls || {}} columns={cols} data={d.results} />
        </>
      )}

      {/* ── Section 7: Charts ── */}
      {!isError && hasResults && (
        <>
          <SectionHeader label="Charts" />
          <AutoChart columns={cols} data={d.results} />
        </>
      )}

    </div>
  );
};

/* ─── User Message Bubble ─── */
const UserBubble = ({ content }) => (
  <div className="user-bubble-wrap">
    <div className="user-bubble">{content}</div>
    <div className="user-avatar"><User size={15} /></div>
  </div>
);

/* ─── Thinking Indicator ─── */
const ThinkingIndicator = () => (
  <div className="ai-message-row">
    <div className="ai-avatar-wrap">
      <Bot size={16} />
    </div>
    <div className="ai-card thinking-card">
      <div className="thinking-dots">
        <span /><span /><span />
      </div>
      <span className="thinking-text">Analyzing and generating SQL...</span>
    </div>
  </div>
);

/* ─── Main CenterChat ─── */
const CenterChat = ({ messages, onSendMessage, isProcessing }) => {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isProcessing]);

  const handleSend = () => {
    const text = input.trim();
    if (text && !isProcessing) {
      onSendMessage(text);
      setInput('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="center-chat">
      {/* ── Messages Area ── */}
      <div className="chat-feed">
        {messages.length === 0 && (
          <div className="chat-empty-state">
            <div className="chat-empty-icon">
              <Bot size={32} />
            </div>
            <h2>AI Data Analyst</h2>
            <p>Ask questions about your business data in plain English.</p>
            <div className="chat-suggestions">
              {[
                'Show wallet transactions of January 2026',
                'Which company has the highest wallet balance?',
                'Show top 10 customers by transaction count',
              ].map((q, i) => (
                <button key={i} className="suggestion-chip" onClick={() => onSendMessage(q)}>
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id} className={msg.role === 'user' ? 'user-msg-row' : 'ai-message-row'}>
            {msg.role === 'user' ? (
              <UserBubble content={msg.content} />
            ) : (
              <>
                <div className="ai-avatar-wrap"><Bot size={16} /></div>
                <AiResponseCard msg={msg} />
              </>
            )}
          </div>
        ))}

        {isProcessing && <ThinkingIndicator />}
        <div ref={messagesEndRef} />
      </div>

      {/* ── Input Area ── */}
      <div className="chat-input-zone">
        <div className="chat-input-inner">
          <textarea
            className="chat-main-input"
            placeholder="Ask a question about your business data..."
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={1}
            disabled={isProcessing}
          />
          <button
            className={`chat-send-btn ${input.trim() ? 'enabled' : ''}`}
            onClick={handleSend}
            disabled={!input.trim() || isProcessing}
          >
            {isProcessing ? <Loader2 size={18} className="spin-anim" /> : <Send size={18} />}
          </button>
        </div>
        <p className="chat-footer-note">AI can make mistakes. Always verify important reports.</p>
      </div>
    </div>
  );
};

export default CenterChat;
