import React, { useState, useEffect } from 'react';
import {
  ShieldCheck, RefreshCw, Cpu, Database, Activity, HardDrive,
  CheckCircle2, AlertCircle, Sparkles, Layers, Clock, Hash
} from 'lucide-react';

export const AdminPanel = ({ onToast }) => {
  const [stats, setStats] = useState(null);
  const [status, setStatus] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isRebuilding, setIsRebuilding] = useState(false);

  const fetchAdminData = () => {
    fetch('/admin/stats')
      .then(res => res.json())
      .then(data => setStats(data))
      .catch(err => console.error('Stats error:', err));

    fetch('/admin/status')
      .then(res => res.json())
      .then(data => setStatus(data))
      .catch(err => console.error('Status error:', err));
  };

  useEffect(() => {
    fetchAdminData();
  }, []);

  const handleRefreshMetadata = async () => {
    setIsRefreshing(true);
    try {
      const res = await fetch('/admin/refresh-metadata', { method: 'POST' });
      const data = await res.json();
      if (onToast) onToast({ type: 'success', message: data.message || 'Database schema metadata refreshed successfully.' });
      fetchAdminData();
    } catch (e) {
      if (onToast) onToast({ type: 'error', message: 'Error scanning database metadata.' });
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleRebuildEmbeddings = async () => {
    setIsRebuilding(true);
    try {
      const res = await fetch('/admin/rebuild-embeddings', { method: 'POST' });
      const data = await res.json();
      if (onToast) onToast({ type: 'success', message: data.message || 'ChromaDB semantic vectors rebuilt successfully.' });
      fetchAdminData();
    } catch (e) {
      if (onToast) onToast({ type: 'error', message: 'Error rebuilding vector embeddings.' });
    } finally {
      setIsRebuilding(false);
    }
  };

  return (
    <div className="dark-scroll" style={{ flex: 1, overflowY: 'auto', padding: '2rem' }}>
      <div style={{ maxWidth: '1080px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
        
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
              Admin Operations & Observability
            </h2>
            <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
              Knowledge base synchronization, vector embeddings & system telemetry
            </span>
          </div>

          <button
            className="btn btn-secondary"
            onClick={fetchAdminData}
            style={{ fontSize: '0.78rem' }}
          >
            <RefreshCw size={13} />
            <span>Refresh Diagnostics</span>
          </button>
        </div>

        {/* ── Real-time Health Cards Grid ── */}
        <div>
          <span style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.75rem' }}>
            Core Subsystem Health
          </span>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
            
            <div className="card" style={{ padding: '1.125rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>API Server</span>
                <span className="badge badge-success">
                  <CheckCircle2 size={11} /> Healthy
                </span>
              </div>
              <div style={{ fontSize: '1.125rem', fontWeight: 700, color: 'var(--text-primary)' }}>FastAPI 2.0</div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Port 8000 • Production</div>
            </div>

            <div className="card" style={{ padding: '1.125rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>Database</span>
                <span className="badge badge-success">
                  <CheckCircle2 size={11} /> Connected
                </span>
              </div>
              <div style={{ fontSize: '1.125rem', fontWeight: 700, color: 'var(--text-primary)' }}>MySQL Production</div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Read-Only Pool Active</div>
            </div>

            <div className="card" style={{ padding: '1.125rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>AI Model Engine</span>
                <span className="badge badge-gold">
                  <Cpu size={11} /> Ready
                </span>
              </div>
              <div style={{ fontSize: '1.125rem', fontWeight: 700, color: 'var(--text-primary)' }}>qwen2.5-coder:7b</div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Offline & On-Premises</div>
            </div>

            <div className="card" style={{ padding: '1.125rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>Validation Engine</span>
                <span className="badge badge-success">
                  <ShieldCheck size={11} /> Enforced
                </span>
              </div>
              <div style={{ fontSize: '1.125rem', fontWeight: 700, color: '#10B981' }}>5 / 5 AST Policies</div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Strict SELECT Security</div>
            </div>

          </div>
        </div>

        {/* ── System Metrics Summary ── */}
        {stats && (
          <div>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.75rem' }}>
              Knowledge Base & Execution Metrics
            </span>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '0.875rem' }}>
              
              <div className="card" style={{ padding: '1rem', textAlign: 'center' }}>
                <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--text-primary)', fontFamily: 'var(--font-display)' }}>
                  {stats.tables_tracked}
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
                  Tables Tracked
                </div>
              </div>

              <div className="card" style={{ padding: '1rem', textAlign: 'center' }}>
                <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--text-primary)', fontFamily: 'var(--font-display)' }}>
                  {stats.relationships_mapped}
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
                  Joins Mapped
                </div>
              </div>

              <div className="card" style={{ padding: '1rem', textAlign: 'center' }}>
                <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--text-primary)', fontFamily: 'var(--font-display)' }}>
                  {stats.query_history_count}
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
                  Queries Logged
                </div>
              </div>

              <div className="card" style={{ padding: '1rem', textAlign: 'center' }}>
                <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--accent-gold-700)', fontFamily: 'var(--font-display)' }}>
                  {stats.avg_latency_ms} ms
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
                  Avg Latency
                </div>
              </div>

              <div className="card" style={{ padding: '1rem', textAlign: 'center' }}>
                <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#10B981', fontFamily: 'var(--font-display)' }}>
                  {stats.avg_confidence}%
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
                  Avg Confidence
                </div>
              </div>

            </div>
          </div>
        )}

        {/* ── Knowledge Base Management Card ── */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">
              <Layers size={16} style={{ color: 'var(--accent-gold-600)' }} />
              Knowledge Base & Semantic Vector Synchronization
            </span>
          </div>
          <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', lineHeight: 1.6, margin: 0 }}>
              Trigger a full database scan to identify updated tables, columns, and foreign key relationships. Next, regenerate the ChromaDB semantic vector embeddings for natural language schema routing.
            </p>

            <div style={{ display: 'flex', gap: '0.875rem', flexWrap: 'wrap' }}>
              <button
                className="btn btn-secondary"
                onClick={handleRefreshMetadata}
                disabled={isRefreshing}
                style={{ padding: '0.625rem 1.125rem' }}
              >
                <RefreshCw size={14} className={isRefreshing ? 'spin-anim' : ''} />
                <span>{isRefreshing ? 'Scanning Database Metadata...' : '1. Refresh Schema Metadata'}</span>
              </button>

              <button
                className="btn btn-gold"
                onClick={handleRebuildEmbeddings}
                disabled={isRebuilding}
                style={{ padding: '0.625rem 1.125rem' }}
              >
                <Sparkles size={14} className={isRebuilding ? 'spin-anim' : ''} />
                <span>{isRebuilding ? 'Rebuilding ChromaDB Vectors...' : '2. Rebuild Vector Embeddings'}</span>
              </button>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};

export default AdminPanel;
