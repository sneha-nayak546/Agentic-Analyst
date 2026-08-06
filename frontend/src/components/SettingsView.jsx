import React, { useState, useEffect } from 'react';
import { Settings, Database, Cpu, Layout, Server, RefreshCw } from 'lucide-react';
import './SettingsView.css';

const SettingsView = () => {
  const [status, setStatus] = useState(null);
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [statusRes, settingsRes] = await Promise.all([
        fetch('/admin/status'),
        fetch('/admin/settings')
      ]);
      const statusData = await statusRes.json();
      const settingsData = await settingsRes.json();
      
      setStatus(statusData);
      setSettings(settingsData);
    } catch (e) {
      console.error("Error fetching settings data", e);
    } finally {
      setLoading(false);
    }
  };

  const handleAction = async (endpoint) => {
    try {
      const res = await fetch(endpoint, { method: 'POST' });
      const data = await res.json();
      alert(data.message || 'Action completed successfully');
      fetchData();
    } catch (e) {
      alert('Action failed. Check console.');
    }
  };

  if (loading || !status || !settings) {
    return <div className="settings-view loading">Loading configuration...</div>;
  }

  return (
    <div className="settings-view">
      <div className="settings-header">
        <h2>Platform Settings</h2>
        <p>Enterprise AI Data Analyst Configuration</p>
      </div>

      <div className="settings-grid">
        
        {/* Database Configuration */}
        <div className="settings-card">
          <div className="card-header">
            <Database size={18} className="text-accent" />
            <h3>Database Connections</h3>
          </div>
          <div className="card-body">
            <div className="setting-row">
              <span>Status</span>
              <span className={`status ${status.database_connected ? 'success' : 'error'}`}>
                {status.database_connected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
            <div className="setting-row">
              <span>Target Scope Tables</span>
              <span>{status.target_tables_count}</span>
            </div>
            <button className="btn outline-btn mt-16" onClick={() => handleAction('/admin/refresh-metadata')}>
              <RefreshCw size={14} /> Refresh Schema Metadata
            </button>
          </div>
        </div>

        {/* Inference / Model Configuration */}
        <div className="settings-card">
          <div className="card-header">
            <Cpu size={18} className="text-accent" />
            <h3>Inference Engine</h3>
          </div>
          <div className="card-body">
            <div className="setting-row">
              <span>Primary Model</span>
              <span className="mono">{settings.model_name}</span>
            </div>
            <div className="setting-row">
              <span>Temperature</span>
              <span>{settings.temperature}</span>
            </div>
            <div className="setting-row">
              <span>Status</span>
              <span className="status success">Local & Offline</span>
            </div>
          </div>
        </div>

        {/* Vector DB Configuration */}
        <div className="settings-card">
          <div className="card-header">
            <Server size={18} className="text-accent" />
            <h3>Knowledge Base (RAG)</h3>
          </div>
          <div className="card-body">
            <div className="setting-row">
              <span>Vector Store</span>
              <span>ChromaDB</span>
            </div>
            <div className="setting-row">
              <span>Embedding Model</span>
              <span className="mono">{settings.embedding_model}</span>
            </div>
            <button className="btn outline-btn mt-16" onClick={() => handleAction('/admin/rebuild-embeddings')}>
              <RefreshCw size={14} /> Rebuild Embeddings
            </button>
          </div>
        </div>

        {/* UI Configuration */}
        <div className="settings-card">
          <div className="card-header">
            <Layout size={18} className="text-accent" />
            <h3>Appearance</h3>
          </div>
          <div className="card-body">
            <div className="setting-row">
              <span>Theme</span>
              <span>Dark Mode (Enforced)</span>
            </div>
            <div className="setting-row">
              <span>Max Grid Rows</span>
              <span>{settings.max_rows}</span>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};

export default SettingsView;
