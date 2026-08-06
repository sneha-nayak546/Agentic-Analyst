import React, { useState, useEffect } from 'react';
import { Database, ChevronRight, ChevronDown, RefreshCw, Columns } from 'lucide-react';

const DatabaseSchemaPanel = () => {
  const [schema, setSchema] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedTables, setExpandedTables] = useState({});
  const [searchTerm, setSearchTerm] = useState('');

  const fetchSchema = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch('http://localhost:8000/schema');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const schemaData = data.schema || {};
      setSchema(schemaData);
      // Auto-expand all tables by default
      const expanded = {};
      Object.keys(schemaData).forEach(t => { expanded[t] = true; });
      setExpandedTables(expanded);
    } catch (e) {
      setError('Failed to load database schema.');
      console.error('Schema fetch error:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSchema();
  }, []);

  const toggleTable = (tableName) => {
    setExpandedTables(prev => ({ ...prev, [tableName]: !prev[tableName] }));
  };

  const filteredSchema = Object.entries(schema).filter(([table, cols]) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return table.toLowerCase().includes(term) || cols.some(c => c.toLowerCase().includes(term));
  });

  const tableCount = Object.keys(schema).length;
  const colCount = Object.values(schema).reduce((sum, cols) => sum + cols.length, 0);

  return (
    <div className="schema-panel">
      <div className="schema-panel-header">
        <div className="schema-panel-title">
          <Database size={16} className="schema-icon" />
          <span>Database Schema</span>
        </div>
        <button
          className="schema-refresh-btn"
          onClick={fetchSchema}
          title="Refresh schema"
        >
          <RefreshCw size={13} className={loading ? 'spin-anim' : ''} />
        </button>
      </div>

      {!loading && !error && (
        <div className="schema-stats">
          <span className="schema-stat">{tableCount} tables</span>
          <span className="schema-stat-dot">·</span>
          <span className="schema-stat">{colCount} columns</span>
        </div>
      )}

      <div className="schema-search-wrap">
        <input
          className="schema-search"
          placeholder="Search tables & columns..."
          value={searchTerm}
          onChange={e => setSearchTerm(e.target.value)}
        />
      </div>

      <div className="schema-list">
        {loading && (
          <div className="schema-loading">
            <div className="schema-skeleton" />
            <div className="schema-skeleton short" />
            <div className="schema-skeleton" />
            <div className="schema-skeleton short" />
          </div>
        )}

        {error && (
          <div className="schema-error">
            <span>⚠ {error}</span>
            <button className="schema-retry-btn" onClick={fetchSchema}>Retry</button>
          </div>
        )}

        {!loading && !error && filteredSchema.length === 0 && (
          <div className="schema-empty">No tables match your search.</div>
        )}

        {!loading && !error && filteredSchema.map(([tableName, columns]) => (
          <div key={tableName} className="schema-table-item">
            <button
              className="schema-table-header"
              onClick={() => toggleTable(tableName)}
            >
              <span className="schema-table-toggle">
                {expandedTables[tableName]
                  ? <ChevronDown size={12} />
                  : <ChevronRight size={12} />
                }
              </span>
              <span className="schema-table-name">{tableName}</span>
              <span className="schema-col-count">{columns.length}</span>
            </button>

            {expandedTables[tableName] && (
              <div className="schema-columns">
                {columns.map((col, i) => {
                  const highlight = searchTerm && col.toLowerCase().includes(searchTerm.toLowerCase());
                  return (
                    <div key={i} className={`schema-col-item ${highlight ? 'schema-col-highlight' : ''}`}>
                      <Columns size={10} className="schema-col-icon" />
                      <span className="schema-col-name">{col}</span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default DatabaseSchemaPanel;
