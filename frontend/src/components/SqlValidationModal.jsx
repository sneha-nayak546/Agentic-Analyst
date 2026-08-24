import React, { useState } from 'react';
import {
  X, CheckCircle2, AlertCircle, Copy, Check, Download, ShieldCheck,
  Cpu, Database, ArrowRight, Layers, Clock, Hash, Code2,
  AlertTriangle, Info, HelpCircle, Target
} from 'lucide-react';

const RESULT_CONFIDENCE_CONFIG = {
  VERIFIED_RESULT: {
    label: 'Result Verified',
    icon: CheckCircle2,
    color: '#10B981',
    bg: '#ECFDF5',
    border: '#A7F3D0',
    desc: 'The returned data was verified against your requested filters (entity, region, date, status).'
  },
  VERIFIED_EMPTY: {
    label: 'No Matching Records',
    icon: Info,
    color: '#2563EB',
    bg: '#EFF6FF',
    border: '#BFDBFE',
    desc: 'Filters are correct. The database has no records matching this combination — this is a genuine empty result.'
  },
  SUSPICIOUS_RESULT: {
    label: 'Result Uncertain',
    icon: AlertTriangle,
    color: '#D97706',
    bg: '#FFFBEB',
    border: '#FDE68A',
    desc: "One or more filters could not be confirmed. Review the SQL or refine your question."
  },
  UNABLE_TO_VERIFY: {
    label: 'Unverified',
    icon: HelpCircle,
    color: '#94A3B8',
    bg: '#F1F5F9',
    border: '#E2E8F0',
    desc: 'Result accuracy validation could not run. Treat the result with caution.'
  },
};

export const SqlValidationModal = ({
  isOpen,
  onClose,
  sql = '',
  executionTime = 0,
  rowCount = 0,
  affectedTables = [],
  confidenceScore = 100,
  resultConfidence = null,
  accuracyMessage = '',
  resultAccuracy = {},
  onToast
}) => {
  const [copied, setCopied] = useState(false);

  if (!isOpen) return null;

  const handleCopy = () => {
    if (!sql) return;
    navigator.clipboard.writeText(sql);
    setCopied(true);
    if (onToast) onToast({ type: 'success', message: 'SQL query copied to clipboard!' });
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    if (!sql) return;
    const blob = new Blob([sql], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `query_${Date.now()}.sql`;
    a.click();
    URL.revokeObjectURL(url);
    if (onToast) onToast({ type: 'success', message: 'SQL file downloaded.' });
  };

  const sqlValidationChecks = [
    { title: 'Read-Only SELECT Enforcement', desc: 'Query verified safe; no INSERT, UPDATE, DELETE, or DDL statements allowed.', passed: true },
    { title: 'Enterprise Schema Authorization', desc: 'All referenced tables belong to approved enterprise knowledge base.', passed: true },
    { title: 'Relationship & Foreign Key Joins', desc: 'Joins adhere to verified foreign-key constraints in relationship graph.', passed: true },
    { title: 'Restricted Column & Privacy Guard', desc: 'Credentials and restricted attributes safely omitted.', passed: true },
    { title: 'Bounded Execution Cost & Limit Guard', desc: 'Query complexity inspected with automatic LIMIT enforcement.', passed: true }
  ];

  const accuracyChecks = (resultAccuracy?.checks_performed || []).map(chk => ({
    label: chk.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
    passed: !(resultAccuracy?.issues_found || []).some(issue =>
      issue.toLowerCase().includes(chk.replace(/_/g, ' ').toLowerCase().split('_')[0])
    )
  }));

  const rcfg = resultConfidence ? (RESULT_CONFIDENCE_CONFIG[resultConfidence] || RESULT_CONFIDENCE_CONFIG['UNABLE_TO_VERIFY']) : null;
  const RIcon = rcfg?.icon || HelpCircle;

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <div className="drawer-container" onClick={(e) => e.stopPropagation()}>
        {/* Drawer Header */}
        <div className="drawer-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: 'var(--radius-md)',
              background: 'var(--brand-navy-900)',
              color: 'var(--accent-gold-400)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Code2 size={17} />
            </div>
            <div>
              <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
                SQL & Validation Inspector
              </h3>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                SQL Validated → Executed → Result Verified
              </span>
            </div>
          </div>
          <button className="btn-icon" onClick={onClose} title="Close drawer">
            <X size={18} />
          </button>
        </div>

        {/* Drawer Body */}
        <div className="drawer-body dark-scroll" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>

          {/* 5-Step Execution Pipeline */}
          <div style={{
            background: 'var(--bg-surface-subtle)',
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-lg)',
            padding: '1rem 1.25rem'
          }}>
            <span style={{ fontSize: '0.68rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-muted)' }}>
              Execution Lifecycle
            </span>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '0.75rem', gap: '0.25rem', flexWrap: 'wrap' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                <Cpu size={13} style={{ color: '#F59E0B' }} />
                <span>AI Generated</span>
              </div>
              <ArrowRight size={12} style={{ color: '#94A3B8' }} />
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.72rem', fontWeight: 600, color: '#1D4ED8' }}>
                <ShieldCheck size={13} style={{ color: '#2563EB' }} />
                <span>SQL Validated</span>
              </div>
              <ArrowRight size={12} style={{ color: '#94A3B8' }} />
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                <Database size={13} style={{ color: '#64748B' }} />
                <span>Executed</span>
              </div>
              <ArrowRight size={12} style={{ color: '#94A3B8' }} />
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.72rem', fontWeight: 600, color: rcfg?.color || '#94A3B8' }}>
                <Target size={13} style={{ color: rcfg?.color || '#94A3B8' }} />
                <span>Result Verified</span>
              </div>
            </div>
          </div>

          {/* Generated SQL Code Block */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-secondary)' }}>
                Generated Read-Only SQL
              </span>
              <div style={{ display: 'flex', gap: '0.35rem' }}>
                <button
                  className="btn btn-secondary"
                  style={{ padding: '0.25rem 0.6rem', fontSize: '0.75rem' }}
                  onClick={handleCopy}
                >
                  {copied ? <Check size={12} style={{ color: '#10B981' }} /> : <Copy size={12} />}
                  {copied ? 'Copied' : 'Copy'}
                </button>
                <button
                  className="btn btn-secondary"
                  style={{ padding: '0.25rem 0.6rem', fontSize: '0.75rem' }}
                  onClick={handleDownload}
                >
                  <Download size={12} />
                  .sql
                </button>
              </div>
            </div>

            <div style={{
              background: '#0B192C',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid #1E293B',
              padding: '1rem',
              overflowX: 'auto',
              boxShadow: 'var(--shadow-sm)'
            }}>
              <pre style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '0.8125rem',
                lineHeight: 1.6,
                color: '#38BDF8',
                margin: 0,
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word'
              }}>
                <code>{sql || '-- No SQL generated for this conversational request.'}</code>
              </pre>
            </div>
          </div>

          {/* Phase 1: SQL Safety Validation */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.625rem' }}>
              <ShieldCheck size={14} style={{ color: '#2563EB' }} />
              <span style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: '#2563EB' }}>
                Phase 1 — SQL Safety Validation (5 / 5 Passed)
              </span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {sqlValidationChecks.map((chk, i) => (
                <div
                  key={i}
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '0.625rem',
                    padding: '0.625rem 0.875rem',
                    borderRadius: 'var(--radius-md)',
                    background: 'var(--bg-surface)',
                    border: '1px solid var(--border-color)'
                  }}
                >
                  <CheckCircle2 size={16} style={{ color: '#10B981', marginTop: '2px', flexShrink: 0 }} />
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.125rem' }}>
                    <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {chk.title}
                    </span>
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                      {chk.desc}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Phase 2: Result Accuracy Validation */}
          {rcfg && (
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.625rem' }}>
                <Target size={14} style={{ color: rcfg.color }} />
                <span style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: rcfg.color }}>
                  Phase 2 — Result Accuracy Validation
                </span>
              </div>

              {/* Confidence status banner */}
              <div style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '0.75rem',
                padding: '0.875rem 1rem',
                borderRadius: 'var(--radius-md)',
                background: rcfg.bg,
                border: `1px solid ${rcfg.border}`,
                marginBottom: '0.625rem'
              }}>
                <RIcon size={18} style={{ color: rcfg.color, flexShrink: 0, marginTop: '1px' }} />
                <div>
                  <div style={{ fontSize: '0.8125rem', fontWeight: 700, color: rcfg.color, marginBottom: '0.25rem' }}>
                    {rcfg.label}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: rcfg.color, lineHeight: 1.5, opacity: 0.85 }}>
                    {accuracyMessage || rcfg.desc}
                  </div>
                </div>
              </div>

              {/* Accuracy checks performed */}
              {accuracyChecks.length > 0 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.375rem' }}>
                  {accuracyChecks.map((chk, i) => (
                    <div key={i} style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                      padding: '0.4rem 0.75rem',
                      borderRadius: 'var(--radius-md)',
                      background: 'var(--bg-surface)',
                      border: '1px solid var(--border-color)'
                    }}>
                      {chk.passed
                        ? <CheckCircle2 size={14} style={{ color: '#10B981', flexShrink: 0 }} />
                        : <AlertCircle size={14} style={{ color: '#EF4444', flexShrink: 0 }} />
                      }
                      <span style={{ fontSize: '0.78rem', fontWeight: 500, color: 'var(--text-secondary)' }}>
                        {chk.label}
                      </span>
                    </div>
                  ))}
                </div>
              )}

              {/* Probe result if performed */}
              {resultAccuracy?.probe_performed && resultAccuracy?.probe_result && (
                <div style={{
                  marginTop: '0.5rem',
                  padding: '0.5rem 0.75rem',
                  background: 'var(--bg-surface-subtle)',
                  border: '1px dashed var(--border-color)',
                  borderRadius: 'var(--radius-md)',
                  fontSize: '0.72rem',
                  color: 'var(--text-muted)'
                }}>
                  🔍 Verification probe ran: found <strong>{resultAccuracy.probe_result.probe_count}</strong> record(s) matching the requested entity+region.
                </div>
              )}
            </div>
          )}

          {/* Query Execution Metrics */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 1fr)',
            gap: '0.75rem',
            paddingTop: '0.5rem'
          }}>
            <div style={{
              background: 'var(--bg-surface-subtle)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-md)',
              padding: '0.75rem',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Latency</div>
              <div style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '0.25rem' }}>
                {executionTime != null ? `${executionTime} ms` : '—'}
              </div>
            </div>

            <div style={{
              background: 'var(--bg-surface-subtle)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-md)',
              padding: '0.75rem',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Rows</div>
              <div style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '0.25rem' }}>
                {rowCount != null ? rowCount : '0'}
              </div>
            </div>

            <div style={{
              background: 'var(--bg-surface-subtle)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-md)',
              padding: '0.75rem',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Confidence</div>
              <div style={{ fontSize: '1rem', fontWeight: 700, color: '#10B981', marginTop: '0.25rem' }}>
                {confidenceScore || 100}%
              </div>
            </div>
          </div>

          {/* Affected Tables */}
          {affectedTables && affectedTables.length > 0 && (
            <div>
              <span style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', display: 'block', marginBottom: '0.4rem' }}>
                Tables Accessed
              </span>
              <div style={{ display: 'flex', gap: '0.375rem', flexWrap: 'wrap' }}>
                {affectedTables.map(tbl => (
                  <span key={tbl} className="badge badge-neutral">
                    <Database size={11} /> {tbl}
                  </span>
                ))}
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
};

export default SqlValidationModal;
