import React, { useState, useEffect } from 'react';

const AdminPanel = () => {
  const [stats, setStats] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isRebuilding, setIsRebuilding] = useState(false);

  const fetchStats = () => {
    fetch('http://localhost:8000/admin/stats')
      .then(res => res.json())
      .then(data => setStats(data));
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const handleRefreshMetadata = async () => {
    setIsRefreshing(true);
    try {
      await fetch('http://localhost:8000/admin/refresh-metadata', { method: 'POST' });
      alert('Metadata refreshed successfully.');
      fetchStats();
    } catch (e) {
      alert('Error refreshing metadata');
    }
    setIsRefreshing(false);
  };

  const handleRebuildEmbeddings = async () => {
    setIsRebuilding(true);
    try {
      await fetch('http://localhost:8000/admin/rebuild-embeddings', { method: 'POST' });
      alert('Vector embeddings rebuilt successfully.');
      fetchStats();
    } catch (e) {
      alert('Error rebuilding embeddings');
    }
    setIsRebuilding(false);
  };

  if (!stats) return <div style={{ padding: '2rem' }}>Loading Admin Metrics...</div>;

  return (
    <div style={{ padding: '2rem', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
        <div className="glass-panel" style={{ padding: '1.5rem', textAlign: 'center' }}>
          <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--primary-color)' }}>{stats.tables_tracked}</div>
          <div style={{ color: 'var(--text-secondary)' }}>Tables Tracked</div>
        </div>
        <div className="glass-panel" style={{ padding: '1.5rem', textAlign: 'center' }}>
          <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--primary-color)' }}>{stats.relationships_mapped}</div>
          <div style={{ color: 'var(--text-secondary)' }}>Relationships Mapped</div>
        </div>
        <div className="glass-panel" style={{ padding: '1.5rem', textAlign: 'center' }}>
          <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--primary-color)' }}>{stats.query_history_count}</div>
          <div style={{ color: 'var(--text-secondary)' }}>Queries Executed</div>
        </div>
        <div className="glass-panel" style={{ padding: '1.5rem', textAlign: 'center' }}>
          <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--accent-color)' }}>{stats.avg_latency_ms} ms</div>
          <div style={{ color: 'var(--text-secondary)' }}>Avg DB Latency</div>
        </div>
      </div>

      <div className="glass-panel" style={{ padding: '1.5rem' }}>
        <h3 style={{ marginBottom: '1.5rem', color: 'var(--primary-color)' }}>Knowledge Base Management</h3>
        <p style={{ marginBottom: '1.5rem', color: 'var(--text-secondary)' }}>
          Trigger a full database scan to identify new tables, columns, constraints, and compute cardinalities. Then rebuild the ChromaDB semantic vectors for the enterprise agent.
        </p>
        <div style={{ display: 'flex', gap: '1rem' }}>
          <button className="btn secondary" onClick={handleRefreshMetadata} disabled={isRefreshing}>
            {isRefreshing ? 'Scanning Database...' : '1. Refresh Schema Metadata'}
          </button>
          <button className="btn" onClick={handleRebuildEmbeddings} disabled={isRebuilding}>
            {isRebuilding ? 'Rebuilding Vectors...' : '2. Rebuild RAG Embeddings'}
          </button>
        </div>
      </div>
      
    </div>
  );
};

export default AdminPanel;
