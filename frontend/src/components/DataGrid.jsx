import React, { useState, useMemo } from 'react';

const DataGrid = ({ columns = [], data = [], onDownload }) => {
  const [page, setPage] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });
  const rowsPerPage = 10;

  const handleSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  const internalDownload = async (type) => {
    if (onDownload) {
      onDownload(type, data, columns);
      return;
    }
    try {
      const payload = { data, columns, filename: `report_${Date.now()}` };
      const response = await fetch(`http://localhost:8000/export/${type}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const ext = type === 'excel' ? 'xlsx' : type;
      a.download = `report_${Date.now()}.${ext}`;
      a.click();
    } catch (err) {
      console.error('Export error:', err);
    }
  };

  const filteredData = useMemo(() => {
    if (!searchTerm) return data;
    return data.filter(row => 
      Object.values(row).some(val => 
        String(val).toLowerCase().includes(searchTerm.toLowerCase())
      )
    );
  }, [data, searchTerm]);

  const sortedData = useMemo(() => {
    let sortableItems = [...filteredData];
    if (sortConfig.key !== null) {
      sortableItems.sort((a, b) => {
        if (a[sortConfig.key] < b[sortConfig.key]) return sortConfig.direction === 'asc' ? -1 : 1;
        if (a[sortConfig.key] > b[sortConfig.key]) return sortConfig.direction === 'asc' ? 1 : -1;
        return 0;
      });
    }
    return sortableItems;
  }, [filteredData, sortConfig]);

  const paginatedData = sortedData.slice(page * rowsPerPage, (page + 1) * rowsPerPage);
  const totalPages = Math.ceil(sortedData.length / rowsPerPage);

  if (!data || data.length === 0) {
    return (
      <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
        <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>📭</div>
        <div style={{ fontWeight: 500 }}>No results found</div>
        <div style={{ fontSize: '0.875rem', marginTop: '0.5rem' }}>Try adjusting your query or filters.</div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', width: '100%' }}>
      {/* Search & Export Header */}
      <div style={{ padding: '0.75rem 1rem', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--bg-panel)', gap: '0.5rem', flexWrap: 'wrap' }}>
        <div style={{ position: 'relative', width: '220px' }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }}>
            <circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
          <input 
            type="text" 
            className="input-base"
            placeholder="Search rows..." 
            value={searchTerm}
            onChange={(e) => { setSearchTerm(e.target.value); setPage(0); }}
            style={{ paddingLeft: '2.25rem', height: '32px', fontSize: '0.8125rem' }}
          />
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 500, marginRight: '0.5rem' }}>
            {sortedData.length > 0 ? page * rowsPerPage + 1 : 0} - {Math.min((page + 1) * rowsPerPage, sortedData.length)} of {sortedData.length} rows
          </div>
          <div style={{ display: 'flex', gap: '0.375rem' }}>
            <button className="btn btn-secondary" style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }} title="Download CSV Report" onClick={() => internalDownload('csv')}>
              📥 CSV
            </button>
            <button className="btn btn-secondary" style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }} title="Download Excel Report" onClick={() => internalDownload('excel')}>
              📊 Excel
            </button>
            <button className="btn btn-secondary" style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }} title="Download PDF Report" onClick={() => internalDownload('pdf')}>
              📄 PDF
            </button>
            <button className="btn btn-secondary" style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }} title="Download JSON Report" onClick={() => internalDownload('json')}>
              📋 JSON
            </button>
          </div>
        </div>
      </div>
      
      {/* Table Container */}
      <div style={{ flex: 1, overflow: 'auto', backgroundColor: 'var(--bg-app)' }}>
        <table>
          <thead>
            <tr>
              {columns.map((col, idx) => (
                <th key={idx} onClick={() => handleSort(col)} style={{ cursor: 'pointer', userSelect: 'none' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                    {col}
                    <span style={{ color: sortConfig.key === col ? 'var(--text-primary)' : 'transparent', display: 'flex', flexDirection: 'column', fontSize: '0.65rem', lineHeight: '0.6rem' }}>
                      <span style={{ opacity: sortConfig.key === col && sortConfig.direction === 'asc' ? 1 : 0.3 }}>▲</span>
                      <span style={{ opacity: sortConfig.key === col && sortConfig.direction === 'desc' ? 1 : 0.3 }}>▼</span>
                    </span>
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {paginatedData.map((row, rIdx) => (
              <tr key={rIdx}>
                {columns.map((col, cIdx) => (
                  <td key={cIdx}>{row[col] !== null ? String(row[col]) : <span style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>NULL</span>}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        
        {paginatedData.length === 0 && (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            No rows match your search "{searchTerm}".
          </div>
        )}
      </div>
      
      {/* Pagination Footer */}
      <div style={{ padding: '0.5rem 1rem', borderTop: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--bg-panel)' }}>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
          Page {totalPages > 0 ? page + 1 : 0} of {totalPages}
        </div>
        <div style={{ display: 'flex', gap: '0.25rem' }}>
          <button 
            className="btn btn-secondary" 
            style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }} 
            disabled={page === 0} 
            onClick={() => setPage(p => p - 1)}
          >
            Prev
          </button>
          <button 
            className="btn btn-secondary" 
            style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }} 
            disabled={page >= totalPages - 1 || totalPages === 0} 
            onClick={() => setPage(p => p + 1)}
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
};

export default DataGrid;

