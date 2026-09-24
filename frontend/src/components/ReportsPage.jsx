import React, { useState, useEffect } from 'react';
import {
  FileText, Download, FileSpreadsheet, CheckCircle2, Clock, Calendar,
  Search, ShieldCheck, Database, HardDrive, Code2, ChevronDown, ChevronUp, RefreshCw
} from 'lucide-react';

export const ReportsPage = ({ onToast }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [downloadingId, setDownloadingId] = useState(null);
  const [expandedSqlId, setExpandedSqlId] = useState(null);
  const [catalog, setCatalog] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchCatalog = async () => {
    setIsLoading(true);
    try {
      const res = await fetch('/api/reports/catalog');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setCatalog(data.reports || []);
    } catch (err) {
      console.error('Failed to load report catalog:', err);
      if (onToast) onToast({ type: 'error', message: 'Failed to load live reports catalog.' });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCatalog();
  }, []);

  const handleLiveDownload = async (reportId, format = 'excel') => {
    const reportKey = `${reportId}-${format}`;
    setDownloadingId(reportKey);
    try {
      const res = await fetch('/api/reports/generate-live', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          report_id: reportId,
          format: format
        })
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `Server returned HTTP ${res.status}`);
      }

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const rep = catalog.find(r => r.id === reportId);
      const baseName = rep?.filename || 'Live_Database_Report';
      const ext = format === 'excel' ? 'xlsx' : 'csv';
      a.download = `${baseName}_${Date.now()}.${ext}`;
      a.click();
      window.URL.revokeObjectURL(url);

      if (onToast) {
        onToast({
          type: 'success',
          message: `Generated and downloaded live database report (${ext.toUpperCase()}).`
        });
      }
    } catch (err) {
      console.error('Download error:', err);
      if (onToast) {
        onToast({ type: 'error', message: `Report generation failed: ${err.message}` });
      }
    } finally {
      setDownloadingId(null);
    }
  };

  const filteredReports = catalog.filter(r =>
    r.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    r.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
    r.category.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="dark-scroll" style={{ flex: 1, overflowY: 'auto', padding: '2rem' }}>
      <div style={{ maxWidth: '1080px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
        
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
              <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                Live Database Report Center
              </h2>
              <span style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.35rem',
                fontSize: '0.72rem',
                fontWeight: 600,
                color: '#10B981',
                background: 'rgba(16, 185, 129, 0.1)',
                border: '1px solid rgba(16, 185, 129, 0.25)',
                padding: '0.2rem 0.55rem',
                borderRadius: '999px'
              }}>
                <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#10B981', display: 'inline-block' }} />
                Direct SQL Execution • MySQL 168.144.28.208
              </span>
            </div>
            <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
              All reports are generated directly from the live <code style={{ fontSize: '0.75rem', background: 'var(--bg-subtle)', padding: '0.1rem 0.3rem', borderRadius: '4px' }}>jghMasterDB</code> database. No mock data.
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div style={{ position: 'relative', width: '280px' }}>
              <Search size={14} style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input
                type="text"
                className="input-base"
                placeholder="Search live reports..."
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
                style={{ paddingLeft: '2.25rem', height: '36px', fontSize: '0.8125rem' }}
              />
            </div>
            <button
              className="btn btn-secondary"
              style={{ padding: '0.35rem 0.65rem', height: '36px', fontSize: '0.75rem' }}
              onClick={fetchCatalog}
              disabled={isLoading}
              title="Refresh report catalog"
            >
              <RefreshCw size={13} className={isLoading ? 'spin' : ''} />
            </button>
          </div>
        </div>

        {/* Security & Live DB Banner */}
        <div style={{
          padding: '1.25rem',
          background: 'var(--bg-surface)',
          border: '1px solid var(--border-color)',
          borderRadius: 'var(--radius-xl)',
          display: 'flex',
          alignItems: 'center',
          gap: '1.25rem'
        }}>
          <div style={{
            width: '44px',
            height: '44px',
            borderRadius: 'var(--radius-lg)',
            background: 'rgba(16, 185, 129, 0.1)',
            border: '1px solid rgba(16, 185, 129, 0.25)',
            color: '#10B981',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0
          }}>
            <Database size={24} />
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 700, fontSize: '0.9375rem', color: 'var(--text-primary)' }}>
              100% Production Database Grounding Guarantee
            </div>
            <div style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', lineHeight: 1.4 }}>
              Every export triggers an exact read-only AST-validated SQL query on MySQL <code>jghMasterDB</code>.
              Data is serialized directly from query result sets into your chosen format without intermediate tampering.
            </div>
          </div>
        </div>

        {/* Reports Catalog Grid */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {filteredReports.map((report) => {
            const isSqlExpanded = expandedSqlId === report.id;
            return (
              <div key={report.id} className="premium-card" style={{ padding: '1.25rem 1.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
                  <div style={{ flex: 1, minWidth: '300px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
                      <span className="badge badge-neutral" style={{ fontSize: '0.7rem' }}>
                        {report.category}
                      </span>
                      <span style={{ fontSize: '0.72rem', color: '#10B981', fontWeight: 600 }}>
                        ● Live Query Ready
                      </span>
                    </div>
                    <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                      {report.title}
                    </h3>
                    <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', margin: '0.35rem 0 0.5rem 0', lineHeight: 1.4 }}>
                      {report.description}
                    </p>

                    <button
                      onClick={() => setExpandedSqlId(isSqlExpanded ? null : report.id)}
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: 'var(--primary)',
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                        padding: 0,
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.25rem',
                        marginTop: '0.25rem'
                      }}
                    >
                      <Code2 size={12} />
                      <span>{isSqlExpanded ? 'Hide Under-the-Hood SQL' : 'View Underlying Database SQL'}</span>
                      {isSqlExpanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                    </button>
                  </div>

                  {/* Export Buttons */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <button
                      className="btn btn-secondary"
                      style={{ padding: '0.45rem 0.85rem', fontSize: '0.78rem' }}
                      onClick={() => handleLiveDownload(report.id, 'excel')}
                      disabled={downloadingId !== null}
                    >
                      <FileSpreadsheet size={14} style={{ color: '#10B981' }} />
                      <span>{downloadingId === `${report.id}-excel` ? 'Querying DB...' : 'Download Excel (.xlsx)'}</span>
                    </button>
                    <button
                      className="btn btn-secondary"
                      style={{ padding: '0.45rem 0.85rem', fontSize: '0.78rem' }}
                      onClick={() => handleLiveDownload(report.id, 'csv')}
                      disabled={downloadingId !== null}
                    >
                      <Download size={14} style={{ color: '#2563EB' }} />
                      <span>{downloadingId === `${report.id}-csv` ? 'Querying DB...' : 'Download CSV'}</span>
                    </button>
                  </div>
                </div>

                {/* Collapsible SQL Query View */}
                {isSqlExpanded && (
                  <div style={{
                    marginTop: '1rem',
                    padding: '0.85rem 1rem',
                    background: '#0F172A',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid #334155'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                      <span style={{ fontSize: '0.7rem', fontWeight: 600, color: '#94A3B8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                        Physical SQL Query Executed on 168.144.28.208
                      </span>
                    </div>
                    <pre style={{
                      margin: 0,
                      fontSize: '0.75rem',
                      fontFamily: 'monospace',
                      color: '#F8FAFC',
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-all',
                      lineHeight: 1.5
                    }}>
                      {report.sql}
                    </pre>
                  </div>
                )}
              </div>
            );
          })}
        </div>

      </div>
    </div>
  );
};

export default ReportsPage;
