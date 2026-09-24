import React, { useState } from 'react';
import {
  FileText, Download, FileSpreadsheet, CheckCircle2, Clock, Calendar,
  Search, ShieldCheck, Database, HardDrive
} from 'lucide-react';

const RECENT_REPORTS = [
  { id: 'rep-01', title: 'Karnataka Distributors Performance Report', format: 'Excel (.xlsx)', size: '142 KB', date: '17 Aug 2026', type: 'excel', rows: 248 },
  { id: 'rep-02', title: 'July 2026 Executive Earnings Summary', format: 'PDF Document', size: '2.1 MB', date: '17 Aug 2026', type: 'pdf', rows: 1284 },
  { id: 'rep-03', title: 'Wallet Transactions & Withdrawals Dump', format: 'CSV Data File', size: '3.4 MB', date: '16 Aug 2026', type: 'csv', rows: 4520 },
  { id: 'rep-04', title: 'Approved Retailers in Lucknow Region', format: 'Excel (.xlsx)', size: '88 KB', date: '16 Aug 2026', type: 'excel', rows: 95 },
  { id: 'rep-05', title: 'SKU Inventory Movements and Depletion', format: 'CSV Data File', size: '1.8 MB', date: '15 Aug 2026', type: 'csv', rows: 2150 }
];

export const ReportsPage = ({ onToast }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [downloadingId, setDownloadingId] = useState(null);

  const handleDownload = async (report) => {
    setDownloadingId(report.id);
    try {
      // Direct sample payload download
      const sampleData = [
        { Report: report.title, GeneratedDate: report.date, Records: report.rows, Status: 'Verified Production' }
      ];
      const res = await fetch(`/export/${report.type}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          data: sampleData,
          columns: ['Report', 'GeneratedDate', 'Records', 'Status'],
          filename: report.title.replace(/\s+/g, '_')
        })
      });
      if (!res.ok) throw new Error('Download failed');
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const ext = report.type === 'excel' ? 'xlsx' : report.type;
      a.download = `${report.title.replace(/\s+/g, '_')}.${ext}`;
      a.click();
      window.URL.revokeObjectURL(url);
      if (onToast) onToast({ type: 'success', message: `Downloaded "${report.title}"` });
    } catch (e) {
      if (onToast) onToast({ type: 'error', message: 'Failed to download report.' });
    } finally {
      setDownloadingId(null);
    }
  };

  const filteredReports = RECENT_REPORTS.filter(r =>
    r.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    r.format.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="dark-scroll" style={{ flex: 1, overflowY: 'auto', padding: '2rem' }}>
      <div style={{ maxWidth: '1000px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
        
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
              Report Center & Export Hub
            </h2>
            <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
              Download enterprise compliance, revenue, and transactional audit reports
            </span>
          </div>

          <div style={{ position: 'relative', width: '280px' }}>
            <Search size={14} style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <input
              type="text"
              className="input-base"
              placeholder="Search reports..."
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              style={{ paddingLeft: '2.25rem', height: '36px', fontSize: '0.8125rem' }}
            />
          </div>
        </div>

        {/* Security / Compliance Banner */}
        <div style={{
          padding: '1rem 1.25rem',
          background: 'var(--bg-surface)',
          border: '1px solid var(--border-color)',
          borderRadius: 'var(--radius-xl)',
          display: 'flex',
          alignItems: 'center',
          gap: '1rem'
        }}>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: 'var(--radius-lg)',
            background: 'var(--success-bg)',
            border: '1px solid var(--success-border)',
            color: 'var(--success-text)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0
          }}>
            <ShieldCheck size={22} />
          </div>
          <div>
            <div style={{ fontWeight: 700, fontSize: '0.9375rem', color: 'var(--text-primary)' }}>
              100% On-Premises & Enterprise Data Compliance
            </div>
            <div style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', lineHeight: 1.4 }}>
              All exported files are generated directly by the secure backend engine. No external data transmission occurs.
            </div>
          </div>
        </div>

        {/* Reports Table Card */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">
              <FileText size={16} style={{ color: 'var(--accent-gold-600)' }} />
              Generated Business Reports
            </span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              {filteredReports.length} available files
            </span>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'separate', borderSpacing: 0 }}>
              <thead>
                <tr>
                  <th style={{ padding: '0.75rem 1.25rem', fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', background: '#FAFAFC', borderBottom: '1px solid var(--border-color)', textAlign: 'left' }}>
                    Report Title
                  </th>
                  <th style={{ padding: '0.75rem 1.25rem', fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', background: '#FAFAFC', borderBottom: '1px solid var(--border-color)', textAlign: 'left' }}>
                    Format
                  </th>
                  <th style={{ padding: '0.75rem 1.25rem', fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', background: '#FAFAFC', borderBottom: '1px solid var(--border-color)', textAlign: 'left' }}>
                    Size / Rows
                  </th>
                  <th style={{ padding: '0.75rem 1.25rem', fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', background: '#FAFAFC', borderBottom: '1px solid var(--border-color)', textAlign: 'left' }}>
                    Generated Date
                  </th>
                  <th style={{ padding: '0.75rem 1.25rem', fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', background: '#FAFAFC', borderBottom: '1px solid var(--border-color)', textAlign: 'right' }}>
                    Action
                  </th>
                </tr>
              </thead>
              <tbody>
                {filteredReports.map((report) => (
                  <tr key={report.id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                    <td style={{ padding: '0.875rem 1.25rem', fontSize: '0.84375rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        {report.type === 'excel' ? (
                          <FileSpreadsheet size={16} style={{ color: '#10B981' }} />
                        ) : report.type === 'pdf' ? (
                          <FileText size={16} style={{ color: '#EF4444' }} />
                        ) : (
                          <FileText size={16} style={{ color: '#2563EB' }} />
                        )}
                        <span>{report.title}</span>
                      </div>
                    </td>
                    <td style={{ padding: '0.875rem 1.25rem', fontSize: '0.78rem' }}>
                      <span className="badge badge-neutral">{report.format}</span>
                    </td>
                    <td style={{ padding: '0.875rem 1.25rem', fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
                      {report.size} • {report.rows} records
                    </td>
                    <td style={{ padding: '0.875rem 1.25rem', fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
                      {report.date}
                    </td>
                    <td style={{ padding: '0.875rem 1.25rem', textAlign: 'right' }}>
                      <button
                        className="btn btn-secondary"
                        style={{ padding: '0.3rem 0.75rem', fontSize: '0.75rem' }}
                        onClick={() => handleDownload(report)}
                        disabled={downloadingId === report.id}
                      >
                        <Download size={12} />
                        <span>{downloadingId === report.id ? 'Exporting...' : 'Download'}</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </div>
  );
};

export default ReportsPage;
