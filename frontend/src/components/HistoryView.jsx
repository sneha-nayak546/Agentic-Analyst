import React, { useState, useEffect } from 'react';
import { Search, Clock, Database, CheckCircle, XCircle, Star, Trash2, Play } from 'lucide-react';

const HistoryView = ({ onReRun }) => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      const res = await fetch('http://localhost:8000/history?limit=100');
      const data = await res.json();
      setHistory(data.history || []);
    } catch (e) {
      console.error("Error fetching history", e);
    } finally {
      setLoading(false);
    }
  };

  const handleFavorite = async (timestamp) => {
    await fetch('http://localhost:8000/history/favorite', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ timestamp })
    });
    fetchHistory();
  };

  const handleDelete = async (timestamp) => {
    await fetch('http://localhost:8000/history/delete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ timestamp })
    });
    fetchHistory();
  };

  const filteredHistory = history.filter(item => 
    item.question.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto', display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '1.5rem', color: 'var(--text-primary)' }}>Query History</h2>
        <div style={{ position: 'relative', width: '300px' }}>
          <Search size={16} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
          <input 
            type="text" 
            className="input-base"
            style={{ paddingLeft: '2.5rem' }}
            placeholder="Search past questions..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {loading ? (
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
          Loading history...
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {filteredHistory.length === 0 && (
            <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)', border: '1px dashed var(--border-color)', borderRadius: 'var(--radius-lg)' }}>
              No history found matching your search.
            </div>
          )}
          
          {filteredHistory.map((item, idx) => (
            <div key={idx} style={{ background: 'var(--bg-panel)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-lg)', padding: '1.5rem', transition: 'all 0.2s ease' }} className="animate-slide-in">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                <h3 style={{ fontSize: '1.125rem', color: 'var(--text-primary)', fontWeight: 600, margin: 0 }}>{item.question}</h3>
                
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                  <span className={`status-badge ${item.status === 'success' ? 'status-success' : 'status-error'}`}>
                    {item.status === 'success' ? <CheckCircle size={14} /> : <XCircle size={14} />}
                    {item.status}
                  </span>
                  <button onClick={() => handleFavorite(item.timestamp)} className="btn btn-ghost" style={{ padding: '0.25rem', color: item.favorite ? '#F59E0B' : 'var(--text-muted)' }} title="Favorite">
                    <Star size={16} fill={item.favorite ? '#F59E0B' : 'none'} />
                  </button>
                  <button onClick={() => handleDelete(item.timestamp)} className="btn btn-ghost" style={{ padding: '0.25rem' }} title="Delete">
                    <Trash2 size={16} />
                  </button>
                  {onReRun && (
                    <button onClick={() => onReRun(item.question)} className="btn btn-primary" style={{ padding: '0.25rem 0.75rem', gap: '0.25rem', height: '32px' }} title="Re-Run Query">
                      <Play size={14} /> Run Again
                    </button>
                  )}
                </div>
              </div>
              
              <div style={{ display: 'flex', gap: '1.5rem', marginBottom: '1.5rem', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Clock size={14} /> {item.execution_time_ms} ms
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Database size={14} /> {item.row_count} rows returned
                </div>
              </div>

              <div style={{ background: 'var(--bg-input)', padding: '1rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', overflowX: 'auto', marginBottom: '1rem' }}>
                <code style={{ fontFamily: 'var(--font-mono)', fontSize: '0.875rem', color: 'var(--accent-primary)', whiteSpace: 'pre-wrap' }}>
                  {item.optimized_sql || item.generated_sql}
                </code>
              </div>
              
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--border-color)', paddingTop: '1rem' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  {new Date(item.timestamp).toLocaleString()}
                </span>
                
                {item.affected_tables && item.affected_tables.length > 0 && (
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    {item.affected_tables.map(t => (
                      <span key={t} style={{ fontSize: '0.75rem', background: 'var(--bg-hover)', color: 'var(--text-secondary)', padding: '0.25rem 0.5rem', borderRadius: 'var(--radius-sm)' }}>
                        {t}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default HistoryView;
