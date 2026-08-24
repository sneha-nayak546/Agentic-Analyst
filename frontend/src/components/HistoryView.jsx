import React, { useState, useEffect } from 'react';
import {
  Search, Clock, Database, CheckCircle2, XCircle, Star, Trash2,
  Play, Lock
} from 'lucide-react';

export const HistoryView = ({ onReRun, onToast }) => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all'); // 'all' | 'success' | 'error' | 'favorites'

  const fetchHistory = async () => {
    try {
      setLoading(true);
      const res = await fetch('/history?limit=100');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setHistory(data.history || []);
    } catch (e) {
      console.error('Error fetching history:', e);
      if (onToast) onToast({ type: 'error', message: 'Failed to load query history.' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleFavorite = async (timestamp) => {
    try {
      await fetch('/history/favorite', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ timestamp })
      });
      if (onToast) onToast({ type: 'success', message: 'Toggled favorite query.' });
      fetchHistory();
    } catch (e) {
      console.error(e);
    }
  };

  const handleDelete = async (timestamp) => {
    try {
      await fetch('/history/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ timestamp })
      });
      if (onToast) onToast({ type: 'info', message: 'History record deleted.' });
      fetchHistory();
    } catch (e) {
      console.error(e);
    }
  };

  const filteredHistory = history.filter(item => {
    const matchesSearch = item.question?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (item.optimized_sql || item.generated_sql || '').toLowerCase().includes(searchTerm.toLowerCase());
    
    if (!matchesSearch) return false;
    if (statusFilter === 'success') return item.status === 'success';
    if (statusFilter === 'error') return item.status !== 'success';
    if (statusFilter === 'favorites') return item.favorite;
    return true;
  });

  return (
    <div className="dark-scroll" style={{ flex: 1, overflowY: 'auto', padding: '2rem' }}>
      <div style={{ maxWidth: '1000px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        
        {/* Header Bar */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
              Query History & Audit Log
            </h2>
            <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
              Verified execution history and performance benchmarks
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
            {/* Search Input */}
            <div style={{ position: 'relative', width: '260px' }}>
              <Search size={14} style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input
                type="text"
                className="input-base"
                placeholder="Search history & SQL..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                style={{ paddingLeft: '2.25rem', height: '36px', fontSize: '0.8125rem' }}
              />
            </div>

            {/* Filter Tabs */}
            <div style={{ display: 'flex', background: 'var(--bg-surface)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)', padding: '2px' }}>
              {[
                { id: 'all', label: 'All' },
                { id: 'success', label: 'Success' },
                { id: 'favorites', label: '★ Pinned' },
                { id: 'error', label: 'Errors' }
              ].map(f => (
                <button
                  key={f.id}
                  onClick={() => setStatusFilter(f.id)}
                  style={{
                    padding: '0.3rem 0.65rem',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: '0.75rem',
                    fontWeight: statusFilter === f.id ? 700 : 500,
                    background: statusFilter === f.id ? 'var(--brand-navy-900)' : 'transparent',
                    color: statusFilter === f.id ? '#FFFFFF' : 'var(--text-secondary)',
                    cursor: 'pointer',
                    transition: 'all var(--transition-fast)'
                  }}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Incognito Notice */}
        <div style={{
          padding: '0.75rem 1.25rem',
          background: 'var(--bg-surface)',
          border: '1px solid var(--border-color)',
          borderRadius: 'var(--radius-lg)',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          fontSize: '0.8125rem',
          color: 'var(--text-secondary)'
        }}>
          <Lock size={15} style={{ color: '#7C3AED', flexShrink: 0 }} />
          <span>
            <strong>Privacy Guarantee:</strong> Queries run during <em>Incognito / Private Mode</em> are processed in-memory and are never stored in this persistent history audit trail.
          </span>
        </div>

        {/* History List */}
        {loading ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            Loading execution history...
          </div>
        ) : filteredHistory.length === 0 ? (
          <div style={{
            padding: '3.5rem 2rem',
            textAlign: 'center',
            background: 'var(--bg-surface)',
            border: '1px dashed var(--border-strong)',
            borderRadius: 'var(--radius-xl)',
            color: 'var(--text-muted)'
          }}>
            <Database size={32} style={{ margin: '0 auto 0.75rem', opacity: 0.5 }} />
            <div style={{ fontWeight: 600, fontSize: '0.9375rem', color: 'var(--text-primary)' }}>No queries found</div>
            <div style={{ fontSize: '0.8125rem', marginTop: '0.25rem' }}>No history records match the selected filters.</div>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.875rem' }}>
            {filteredHistory.map((item, idx) => {
              const isSuccess = item.status === 'success';
              const sql = item.optimized_sql || item.generated_sql;

              return (
                <div
                  key={idx}
                  className="card"
                  style={{
                    padding: '1.25rem',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.875rem'
                  }}
                >
                  {/* Top Line: Question & Status */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
                      <span className={`badge ${isSuccess ? 'badge-success' : 'badge-error'}`}>
                        {isSuccess ? <CheckCircle2 size={12} /> : <XCircle size={12} />}
                        {item.status}
                      </span>
                      <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>
                        {item.question}
                      </h3>
                    </div>

                    {/* Actions */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                      <button
                        className="btn-icon"
                        onClick={() => handleFavorite(item.timestamp)}
                        title={item.favorite ? 'Unpin query' : 'Pin to favorites'}
                        style={{ color: item.favorite ? '#F59E0B' : 'var(--text-muted)' }}
                      >
                        <Star size={15} fill={item.favorite ? '#F59E0B' : 'none'} />
                      </button>

                      {onReRun && (
                        <button
                          className="btn btn-gold"
                          style={{ padding: '0.28rem 0.65rem', fontSize: '0.75rem' }}
                          onClick={() => onReRun(item.question)}
                          title="Re-run query in workspace"
                        >
                          <Play size={11} fill="#FFFFFF" /> Run Again
                        </button>
                      )}

                      <button
                        className="btn-icon"
                        onClick={() => handleDelete(item.timestamp)}
                        title="Delete record"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>

                  {/* SQL Code Preview */}
                  {sql && (
                    <div style={{
                      background: '#0B192C',
                      borderRadius: 'var(--radius-md)',
                      padding: '0.75rem 1rem',
                      overflowX: 'auto',
                      border: '1px solid #1E293B'
                    }}>
                      <code style={{
                        fontFamily: 'var(--font-mono)',
                        fontSize: '0.78rem',
                        color: '#38BDF8',
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-word'
                      }}>
                        {sql}
                      </code>
                    </div>
                  )}

                  {/* Metadata Footer */}
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    paddingTop: '0.625rem',
                    borderTop: '1px solid var(--border-subtle)',
                    fontSize: '0.75rem',
                    color: 'var(--text-muted)',
                    flexWrap: 'wrap',
                    gap: '0.5rem'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                        <Clock size={12} /> {item.execution_time_ms != null ? `${item.execution_time_ms} ms` : '—'}
                      </span>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                        <Database size={12} /> {item.row_count != null ? `${item.row_count} rows` : '0 rows'}
                      </span>
                      <span>
                        {item.timestamp ? new Date(item.timestamp).toLocaleString() : ''}
                      </span>
                    </div>

                    {item.affected_tables && item.affected_tables.length > 0 && (
                      <div style={{ display: 'flex', gap: '0.25rem' }}>
                        {item.affected_tables.map(tbl => (
                          <span key={tbl} className="badge badge-neutral" style={{ fontSize: '0.68rem', padding: '0.1rem 0.4rem' }}>
                            {tbl}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                </div>
              );
            })}
          </div>
        )}

      </div>
    </div>
  );
};

export default HistoryView;
