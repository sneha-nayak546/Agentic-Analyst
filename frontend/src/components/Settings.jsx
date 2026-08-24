import React, { useState, useEffect } from 'react';
import {
  Settings as SettingsIcon, Save, RefreshCw, Cpu, Database,
  Sliders, ShieldCheck, CheckCircle2, Sparkles
} from 'lucide-react';

export const Settings = ({ onToast }) => {
  const [settings, setSettings] = useState(null);
  const [status, setStatus] = useState(null);
  const [isSaving, setIsSaving] = useState(false);
  const [actionLoading, setActionLoading] = useState(null);

  const fetchConfig = () => {
    fetch('/admin/settings')
      .then(res => res.json())
      .then(data => setSettings(data))
      .catch(e => console.error(e));

    fetch('/admin/status')
      .then(res => res.json())
      .then(data => setStatus(data))
      .catch(e => console.error(e));
  };

  useEffect(() => {
    fetchConfig();
  }, []);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const res = await fetch('/admin/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      });
      if (!res.ok) throw new Error('Failed to save settings');
      if (onToast) onToast({ type: 'success', message: 'Platform configuration saved successfully.' });
    } catch (e) {
      if (onToast) onToast({ type: 'error', message: 'Error saving settings.' });
    } finally {
      setIsSaving(false);
    }
  };

  const executeAction = async (endpoint, label) => {
    setActionLoading(label);
    try {
      const res = await fetch(endpoint, { method: 'POST' });
      const data = await res.json();
      if (onToast) onToast({ type: 'success', message: data.message || `${label} completed successfully.` });
      fetchConfig();
    } catch (e) {
      if (onToast) onToast({ type: 'error', message: `Error executing ${label}.` });
    } finally {
      setActionLoading(null);
    }
  };

  if (!settings || !status) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-muted)' }}>
        Loading platform configuration...
      </div>
    );
  }

  return (
    <div className="dark-scroll" style={{ flex: 1, overflowY: 'auto', padding: '2rem' }}>
      <div style={{ maxWidth: '840px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
        
        {/* Header */}
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
            Platform Settings & LLM Parameters
          </h2>
          <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
            Configure model engine, generation temperature, and result row caps
          </span>
        </div>

        {/* ── Configuration Form Card ── */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">
              <Sliders size={16} style={{ color: 'var(--accent-gold-600)' }} />
              Inference Parameters
            </span>
          </div>

          <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            
            {/* LLM Model */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
              <label style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                LLM Model Identifier
              </label>
              <input
                type="text"
                className="input-base"
                value={settings.model_name || ''}
                onChange={e => setSettings({ ...settings, model_name: e.target.value })}
                placeholder="e.g. qwen2.5-coder:7b"
              />
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                Target model used for natural language understanding and SQL synthesis.
              </span>
            </div>

            {/* Embedding Model */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
              <label style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                Vector Embedding Model
              </label>
              <input
                type="text"
                className="input-base"
                value={settings.embedding_model || ''}
                onChange={e => setSettings({ ...settings, embedding_model: e.target.value })}
                placeholder="e.g. all-MiniLM-L6-v2"
              />
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                Embedding model used for semantic schema retrieval and few-shot catalog matches.
              </span>
            </div>

            {/* Temperature Slider */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <label style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                  LLM Sampling Temperature
                </label>
                <span style={{ fontSize: '0.84375rem', fontWeight: 700, color: 'var(--accent-gold-700)', background: 'var(--accent-gold-50)', padding: '0.15rem 0.5rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--accent-gold-100)' }}>
                  {settings.temperature}
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={settings.temperature || 0}
                onChange={e => setSettings({ ...settings, temperature: parseFloat(e.target.value) })}
                style={{ width: '100%', cursor: 'pointer', accentColor: 'var(--accent-gold-500)' }}
              />
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                Lower values (0.0–0.2) ensure deterministic, mathematically precise SQL generation.
              </span>
            </div>

            {/* Max Result Rows */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
              <label style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                Maximum Query Result Rows
              </label>
              <input
                type="number"
                className="input-base"
                value={settings.max_rows || 100}
                onChange={e => setSettings({ ...settings, max_rows: parseInt(e.target.value) || 100 })}
                min="10"
                max="5000"
              />
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                Default automatic LIMIT enforced on SQL queries to protect database memory.
              </span>
            </div>

            {/* Save Button */}
            <button
              className="btn btn-gold"
              onClick={handleSave}
              disabled={isSaving}
              style={{ alignSelf: 'flex-start', marginTop: '0.5rem', padding: '0.55rem 1.25rem' }}
            >
              <Save size={15} />
              <span>{isSaving ? 'Saving Changes...' : 'Save Configuration'}</span>
            </button>

          </div>
        </div>

        {/* ── Status & Maintenance Actions ── */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">
              <Database size={16} style={{ color: 'var(--accent-gold-600)' }} />
              Target Tables & Knowledge Synchronization
            </span>
            <span className="badge badge-success">
              {status.target_tables_count || 9} Tables Connected
            </span>
          </div>

          <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap' }}>
              {(status.target_tables || []).map(tbl => (
                <span key={tbl} className="badge badge-neutral">
                  {tbl}
                </span>
              ))}
            </div>

            <div style={{ display: 'flex', gap: '0.75rem', paddingTop: '1rem', borderTop: '1px solid var(--border-subtle)' }}>
              <button
                className="btn btn-secondary"
                onClick={() => executeAction('/admin/refresh-metadata', 'Schema Metadata Refresh')}
                disabled={actionLoading !== null}
              >
                <RefreshCw size={13} className={actionLoading === 'Schema Metadata Refresh' ? 'spin-anim' : ''} />
                <span>Re-Extract Schema Metadata</span>
              </button>

              <button
                className="btn btn-secondary"
                onClick={() => executeAction('/admin/rebuild-embeddings', 'Vector Store Rebuild')}
                disabled={actionLoading !== null}
              >
                <Sparkles size={13} className={actionLoading === 'Vector Store Rebuild' ? 'spin-anim' : ''} />
                <span>Rebuild Semantic Vectors</span>
              </button>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};

export default Settings;
