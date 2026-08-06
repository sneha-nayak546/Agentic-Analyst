import React, { useState, useEffect } from 'react';

const Settings = () => {
  const [settings, setSettings] = useState(null);
  const [status, setStatus] = useState(null);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    fetch('http://localhost:8000/admin/settings')
      .then(res => res.json())
      .then(data => setSettings(data))
      .catch(e => console.error(e));
      
    fetch('http://localhost:8000/admin/status')
      .then(res => res.json())
      .then(data => setStatus(data))
      .catch(e => console.error(e));
  }, []);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await fetch('http://localhost:8000/admin/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      });
      // Optionally show a custom toast notification instead of alert
      alert('Settings saved successfully!');
    } catch (e) {
      alert('Error saving settings');
    }
    setIsSaving(false);
  };

  const executeAdminAction = async (endpoint, successMessage) => {
    try {
      const res = await fetch(`http://localhost:8000${endpoint}`, { method: 'POST' });
      const data = await res.json();
      alert(data.message || successMessage);
    } catch (e) {
      alert(`Error executing action: ${e.message}`);
    }
  };

  if (!settings || !status) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: '1rem', color: 'var(--text-muted)' }}>
        <div className="skeleton-loader" style={{ width: '400px' }}>
          <div className="skeleton-line long"></div>
          <div className="skeleton-line medium"></div>
          <div className="skeleton-line short"></div>
        </div>
        <div>Loading configuration...</div>
      </div>
    );
  }

  return (
    <div className="animate-slide-in" style={{ display: 'flex', flexDirection: 'column', gap: '2rem', maxWidth: '800px', margin: '0 auto', paddingBottom: '4rem' }}>
      
      <div style={{ padding: '2rem', background: 'var(--bg-panel)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-xl)', boxShadow: 'var(--shadow-md)' }}>
        <h3 style={{ marginBottom: '1.5rem', color: 'var(--text-primary)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '1.125rem' }}>
          System Status & Health
          <span className="status-badge status-success" style={{ fontSize: '0.75rem', padding: '0.25rem 0.75rem' }}>Platform Active</span>
        </h3>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem', color: 'var(--text-secondary)' }}>
          <div style={{ background: 'var(--bg-app)', padding: '1rem', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-color)' }}>
            <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Database Connection</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600, color: status.database_connected ? 'var(--success)' : 'var(--error)' }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', background: 'currentColor' }}></span>
              {status.database_connected ? 'Online' : 'Offline'}
            </div>
          </div>
          
          <div style={{ background: 'var(--bg-app)', padding: '1rem', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-color)' }}>
            <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Model Status</div>
            <div style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{status.model_status}</div>
          </div>
          
          <div style={{ background: 'var(--bg-app)', padding: '1rem', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-color)' }}>
            <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Embedding Status</div>
            <div style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{status.embedding_status}</div>
          </div>
          
          <div style={{ background: 'var(--bg-app)', padding: '1rem', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-color)' }}>
            <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Active Tables</div>
            <div style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{status.target_tables_count} <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>/ 9 Tracked</span></div>
          </div>
        </div>
        
        <div style={{ marginTop: '2rem', display: 'flex', gap: '1rem', flexWrap: 'wrap', paddingTop: '1.5rem', borderTop: '1px solid var(--border-color)' }}>
            <button className="btn btn-secondary" onClick={() => executeAdminAction('/admin/refresh-metadata', 'Knowledge Base Rebuilt')}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/></svg>
              Rebuild Knowledge Base
            </button>
            <button className="btn btn-secondary" onClick={() => executeAdminAction('/admin/rebuild-embeddings', 'Embeddings Rebuilt')}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline></svg>
              Rebuild Embeddings
            </button>
        </div>
      </div>

      <div style={{ padding: '2rem', background: 'var(--bg-panel)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-xl)', boxShadow: 'var(--shadow-md)' }}>
        <h3 style={{ marginBottom: '1.5rem', color: 'var(--text-primary)', fontSize: '1.125rem' }}>Platform Configuration</h3>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <label style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-secondary)' }}>LLM Model Name</label>
            <input 
              type="text" 
              className="input-base"
              value={settings.model_name || ''} 
              onChange={e => setSettings({...settings, model_name: e.target.value})}
              placeholder="e.g. llama3"
            />
          </div>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <label style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-secondary)' }}>Embedding Model</label>
            <input 
              type="text" 
              className="input-base"
              value={settings.embedding_model || ''} 
              onChange={e => setSettings({...settings, embedding_model: e.target.value})}
              placeholder="e.g. nomic-embed-text"
            />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <label style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-secondary)' }}>LLM Temperature</label>
              <span style={{ fontSize: '0.875rem', color: 'var(--text-primary)', fontWeight: 600 }}>{settings.temperature}</span>
            </div>
            <input 
              type="range" min="0" max="1" step="0.1"
              value={settings.temperature || 0} 
              onChange={e => setSettings({...settings, temperature: parseFloat(e.target.value)})}
              style={{ width: '100%', cursor: 'pointer' }}
            />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <label style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-secondary)' }}>Max Result Rows</label>
            <input 
              type="number" 
              className="input-base"
              value={settings.max_rows || 100} 
              onChange={e => setSettings({...settings, max_rows: parseInt(e.target.value)})}
            />
          </div>

          <button className="btn btn-primary" style={{ alignSelf: 'flex-start', marginTop: '1rem' }} onClick={handleSave} disabled={isSaving}>
            {isSaving ? 'Saving...' : 'Save Configuration'}
          </button>
        </div>
      </div>
      
    </div>
  );
};

export default Settings;
