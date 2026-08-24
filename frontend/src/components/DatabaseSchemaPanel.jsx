import React, { useState, useEffect } from 'react';
import {
  Database, Search, RefreshCw, Key, Link as LinkIcon,
  Layers, Columns, CheckCircle2, Table2
} from 'lucide-react';
import MermaidViewer from './MermaidViewer';

export const DatabaseSchemaPanel = ({ onToast }) => {
  const [schema, setSchema] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedTable, setSelectedTable] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [viewMode, setViewMode] = useState('columns'); // 'columns' | 'erd'
  const [adminSchema, setAdminSchema] = useState({});

  const fetchSchema = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [resSchema, resAdmin] = await Promise.all([
        fetch('/schema'),
        fetch('/admin/schema').catch(() => null)
      ]);

      if (!resSchema.ok) throw new Error(`HTTP ${resSchema.status}`);
      const data = await resSchema.json();
      const schemaData = data.schema || {};
      setSchema(schemaData);

      if (resAdmin && resAdmin.ok) {
        const adminData = await resAdmin.json();
        setAdminSchema(adminData.schema || {});
      }

      // Default select the first table
      const tables = Object.keys(schemaData);
      if (tables.length > 0 && !selectedTable) {
        setSelectedTable(tables[0]);
      }
    } catch (e) {
      setError('Failed to load database schema metadata.');
      console.error('Schema fetch error:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSchema();
  }, []);

  const filteredTables = Object.entries(schema).filter(([tbl, cols]) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return tbl.toLowerCase().includes(term) || cols.some(c => c.toLowerCase().includes(term));
  });

  const activeTableMeta = adminSchema[selectedTable] || {};
  const activeTableCols = schema[selectedTable] || [];

  // Generate complete ERD diagram syntax dynamically from schema
  const generateMermaidERD = () => {
    let erd = 'erDiagram\n';
    Object.entries(schema).forEach(([tbl, cols]) => {
      erd += `    ${tbl} {\n`;
      cols.slice(0, 8).forEach(c => {
        const type = c.includes('id') ? 'int' : c.includes('date') || c.includes('created') ? 'datetime' : 'varchar';
        const key = c.endsWith('_id') && !c.startsWith(tbl) ? 'FK' : c === 'id' || c === `${tbl}_id` ? 'PK' : '';
        erd += `        ${type} ${c} ${key}\n`;
      });
      erd += `    }\n`;
    });

    // Sample relationships based on naming conventions
    if (schema['retailers'] && schema['distributors']) {
      erd += `    distributors ||--o{ retailers : "manages"\n`;
    }
    if (schema['wallet_transaction'] && schema['users']) {
      erd += `    users ||--o{ wallet_transaction : "has"\n`;
    }
    if (schema['sku_inventeries'] && schema['distributors']) {
      erd += `    distributors ||--o{ sku_inventeries : "stocks"\n`;
    }
    return erd;
  };

  return (
    <div style={{
      display: 'flex',
      height: '100%',
      width: '100%',
      background: 'var(--bg-app)',
      overflow: 'hidden'
    }}>
      {/* ── Left Pane: Tables List ── */}
      <div style={{
        width: '320px',
        minWidth: '280px',
        borderRight: '1px solid var(--border-color)',
        background: 'var(--bg-surface)',
        display: 'flex',
        flexDirection: 'column',
        height: '100%'
      }}>
        {/* Header */}
        <div style={{
          padding: '1rem 1.25rem',
          borderBottom: '1px solid var(--border-color)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Database size={17} style={{ color: 'var(--accent-gold-600)' }} />
            <h3 style={{ fontSize: '0.9375rem', fontWeight: 700, margin: 0 }}>Database Tables</h3>
          </div>
          <button
            className="btn-icon"
            onClick={fetchSchema}
            title="Refresh schema"
          >
            <RefreshCw size={14} className={loading ? 'spin-anim' : ''} />
          </button>
        </div>

        {/* Search */}
        <div style={{ padding: '0.75rem 1.25rem', borderBottom: '1px solid var(--border-subtle)' }}>
          <div style={{ position: 'relative' }}>
            <Search size={14} style={{ position: 'absolute', left: '0.625rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <input
              type="text"
              className="input-base"
              placeholder="Filter tables & columns..."
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              style={{ paddingLeft: '2rem', height: '34px', fontSize: '0.8125rem' }}
            />
          </div>
        </div>

        {/* Table Count */}
        <div style={{ padding: '0.4rem 1.25rem', fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 600, background: '#FAFAFC', borderBottom: '1px solid var(--border-subtle)' }}>
          {filteredTables.length} Active Enterprise Tables
        </div>

        {/* Tables List */}
        <div className="dark-scroll" style={{ flex: 1, overflowY: 'auto', padding: '0.5rem' }}>
          {loading ? (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8125rem' }}>
              Loading database schema...
            </div>
          ) : error ? (
            <div style={{ padding: '1.5rem', color: 'var(--error)', fontSize: '0.8125rem' }}>
              {error}
            </div>
          ) : (
            filteredTables.map(([tbl, cols]) => {
              const isSelected = selectedTable === tbl;
              return (
                <button
                  key={tbl}
                  onClick={() => setSelectedTable(tbl)}
                  style={{
                    width: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '0.625rem 0.75rem',
                    borderRadius: 'var(--radius-md)',
                    background: isSelected ? 'var(--accent-gold-50)' : 'transparent',
                    border: isSelected ? '1px solid var(--accent-gold-400)' : '1px solid transparent',
                    color: isSelected ? 'var(--accent-gold-900)' : 'var(--text-primary)',
                    fontWeight: isSelected ? 600 : 500,
                    fontSize: '0.8125rem',
                    cursor: 'pointer',
                    transition: 'all var(--transition-fast)',
                    marginBottom: '2px',
                    textAlign: 'left'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', overflow: 'hidden' }}>
                    <Table2 size={14} style={{ color: isSelected ? '#D97706' : '#94A3B8', flexShrink: 0 }} />
                    <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{tbl}</span>
                  </div>
                  <span style={{ fontSize: '0.68rem', padding: '0.1rem 0.4rem', borderRadius: 'var(--radius-full)', background: isSelected ? '#FEF3C7' : '#F1F5F9', color: isSelected ? '#92400E' : 'var(--text-muted)' }}>
                    {cols.length}
                  </span>
                </button>
              );
            })
          )}
        </div>
      </div>

      {/* ── Right Pane: Table Details & ERD ── */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
        {/* Top Header & Tab Toggle */}
        <div style={{
          padding: '1rem 1.75rem',
          borderBottom: '1px solid var(--border-color)',
          background: 'var(--bg-surface)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
              {selectedTable ? selectedTable : 'Schema Explorer'}
            </h2>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              {activeTableCols.length} Columns • Read-Only Enterprise Schema
            </span>
          </div>

          <div style={{ display: 'flex', gap: '0.35rem' }}>
            <button
              className={`btn ${viewMode === 'columns' ? 'btn-primary' : 'btn-secondary'}`}
              style={{ fontSize: '0.78rem', padding: '0.35rem 0.75rem' }}
              onClick={() => setViewMode('columns')}
            >
              <Columns size={13} /> Columns & Keys
            </button>
            <button
              className={`btn ${viewMode === 'erd' ? 'btn-primary' : 'btn-secondary'}`}
              style={{ fontSize: '0.78rem', padding: '0.35rem 0.75rem' }}
              onClick={() => setViewMode('erd')}
            >
              <Layers size={13} /> Visual ERD Diagram
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div className="dark-scroll" style={{ flex: 1, overflowY: 'auto', padding: '1.75rem' }}>
          {viewMode === 'erd' ? (
            <div style={{ maxWidth: '960px', margin: '0 auto' }}>
              <div style={{ marginBottom: '1rem' }}>
                <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>Interactive Enterprise ER Diagram</h3>
                <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
                  Visual mapping of table schemas and foreign key relationships.
                </p>
              </div>
              <MermaidViewer code={generateMermaidERD()} />
            </div>
          ) : (
            <div style={{ maxWidth: '960px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              
              {/* Table Info Card */}
              <div className="card">
                <div className="card-header">
                  <span className="card-title">
                    <Database size={16} style={{ color: 'var(--accent-gold-600)' }} />
                    Table Metadata & Description
                  </span>
                  <span className="badge badge-success">
                    <CheckCircle2 size={12} /> Active in Scope
                  </span>
                </div>
                <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: '0.875rem' }}>
                  <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                    {activeTableMeta.description || `Enterprise database table storing verified records for ${selectedTable || 'operations'}.`}
                  </div>

                  <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap', paddingTop: '0.5rem', borderTop: '1px solid var(--border-subtle)' }}>
                    <div>
                      <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>Total Columns</div>
                      <div style={{ fontSize: '1.125rem', fontWeight: 700, color: 'var(--text-primary)' }}>{activeTableCols.length}</div>
                    </div>
                    <div>
                      <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>Primary Key</div>
                      <div style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--accent-gold-700)', display: 'flex', alignItems: 'center', gap: '0.25rem', marginTop: '2px' }}>
                        <Key size={13} /> {activeTableCols[0] || 'id'}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Columns Table */}
              <div className="card">
                <div className="card-header">
                  <span className="card-title">
                    <Columns size={16} style={{ color: 'var(--accent-gold-600)' }} />
                    Column Dictionary
                  </span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    {activeTableCols.length} fields
                  </span>
                </div>
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'separate', borderSpacing: 0 }}>
                    <thead>
                      <tr>
                        <th style={{ padding: '0.625rem 1.25rem', fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', background: '#FAFAFC', borderBottom: '1px solid var(--border-color)', textAlign: 'left' }}>
                          Column Name
                        </th>
                        <th style={{ padding: '0.625rem 1.25rem', fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', background: '#FAFAFC', borderBottom: '1px solid var(--border-color)', textAlign: 'left' }}>
                          Inferred Type
                        </th>
                        <th style={{ padding: '0.625rem 1.25rem', fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', background: '#FAFAFC', borderBottom: '1px solid var(--border-color)', textAlign: 'left' }}>
                          Key / Attribute
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {activeTableCols.map((col, idx) => {
                        const isPk = idx === 0 || col === 'id' || col === `${selectedTable}_id`;
                        const isFk = col.endsWith('_id') && !isPk;
                        const isDate = /(date|time|created|updated)/i.test(col);
                        const isNum = /(amount|count|price|earning|qty|balance)/i.test(col);
                        const typeLabel = isPk || isFk || isNum ? 'INTEGER' : isDate ? 'DATETIME' : 'VARCHAR';

                        return (
                          <tr key={col} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                            <td style={{ padding: '0.625rem 1.25rem', fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                              <code>{col}</code>
                            </td>
                            <td style={{ padding: '0.625rem 1.25rem', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                              <span className="badge badge-neutral">{typeLabel}</span>
                            </td>
                            <td style={{ padding: '0.625rem 1.25rem', fontSize: '0.75rem' }}>
                              {isPk && (
                                <span className="badge badge-gold">
                                  <Key size={10} /> PRIMARY KEY
                                </span>
                              )}
                              {isFk && (
                                <span className="badge badge-info">
                                  <LinkIcon size={10} /> FOREIGN KEY
                                </span>
                              )}
                              {!isPk && !isFk && (
                                <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Standard Column</span>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DatabaseSchemaPanel;
