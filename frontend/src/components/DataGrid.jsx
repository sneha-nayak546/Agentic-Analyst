import React, { useState, useMemo } from 'react';
import {
  Search, ArrowUpDown, ArrowUp, ArrowDown, Maximize2,
  Minimize2, Copy, Check, FileText, FileSpreadsheet, ChevronLeft,
  ChevronRight, Table2, X
} from 'lucide-react';
import './DataGrid.css';

const formatCellValue = (val, colName = '') => {
  if (val === null || val === undefined) {
    return <span className="datagrid-cell-null">NULL</span>;
  }

  // Boolean
  if (typeof val === 'boolean') {
    return val ? (
      <span className="badge badge-success" style={{ fontSize: '0.7rem', padding: '0.1rem 0.4rem' }}>TRUE</span>
    ) : (
      <span className="badge badge-neutral" style={{ fontSize: '0.7rem', padding: '0.1rem 0.4rem' }}>FALSE</span>
    );
  }

  // Identifier / Code / Phone / Role / Status check — NEVER format with commas or currency
  const isIdOrCode = /(id$|_id$|^id$|^mobile|^phone|^code|^pin|^status|^user_role|^role_id|^year)/i.test(colName);
  if (isIdOrCode) {
    return String(val);
  }

  // Number / Currency / Percentage
  if (typeof val === 'number') {
    const isPercentage = /(percentage|pct|growth|rate|ratio)/i.test(colName);
    if (isPercentage) {
      const sign = val > 0 ? '+' : '';
      return `${sign}${val.toFixed(2)}%`;
    }
    const isCurrency = /(amount|earning|revenue|price|balance|payout|commission|cost)/i.test(colName) && !/points|boxes|scans|count/i.test(colName);
    if (isCurrency) {
      return `₹${val.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
    }
    return val.toLocaleString('en-IN');
  }

  return String(val);
};

export const DataGrid = ({
  columns = [],
  data = [],
  onToast,
  title = 'Query Results'
}) => {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [copiedCell, setCopiedCell] = useState(null);
  const [exportingType, setExportingType] = useState(null);

  // Auto-detect columns from data if not explicitly provided
  const activeColumns = useMemo(() => {
    if (columns && columns.length > 0) return columns;
    if (data && data.length > 0) return Object.keys(data[0]);
    return [];
  }, [columns, data]);

  const handleSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    } else if (sortConfig.key === key && sortConfig.direction === 'desc') {
      direction = 'asc';
    }
    setSortConfig({ key, direction });
  };

  const filteredData = useMemo(() => {
    if (!searchTerm.trim()) return data;
    const term = searchTerm.toLowerCase();
    return data.filter(row =>
      Object.values(row).some(val =>
        val !== null && val !== undefined && String(val).toLowerCase().includes(term)
      )
    );
  }, [data, searchTerm]);

  const sortedData = useMemo(() => {
    if (!sortConfig.key) return filteredData;
    const items = [...filteredData];
    items.sort((a, b) => {
      const valA = a[sortConfig.key];
      const valB = b[sortConfig.key];
      if (valA === valB) return 0;
      if (valA === null || valA === undefined) return 1;
      if (valB === null || valB === undefined) return -1;
      if (typeof valA === 'number' && typeof valB === 'number') {
        return sortConfig.direction === 'asc' ? valA - valB : valB - valA;
      }
      return sortConfig.direction === 'asc'
        ? String(valA).localeCompare(String(valB))
        : String(valB).localeCompare(String(valA));
    });
    return items;
  }, [filteredData, sortConfig]);

  const totalPages = Math.ceil(sortedData.length / pageSize) || 1;
  const paginatedData = useMemo(() => {
    return sortedData.slice(page * pageSize, (page + 1) * pageSize);
  }, [sortedData, page, pageSize]);

  const handleCopyCell = (val, cellId) => {
    if (val === null || val === undefined) return;
    navigator.clipboard.writeText(String(val));
    setCopiedCell(cellId);
    if (onToast) onToast({ type: 'success', message: `Copied "${String(val).slice(0, 30)}" to clipboard.` });
    setTimeout(() => setCopiedCell(null), 1500);
  };

  const handleCopyTable = () => {
    if (!data.length) return;
    const csvContent = [
      activeColumns.join(','),
      ...data.map(row => activeColumns.map(col => JSON.stringify(row[col] ?? '')).join(','))
    ].join('\n');
    navigator.clipboard.writeText(csvContent);
    if (onToast) onToast({ type: 'success', message: 'Full table data copied as CSV.' });
  };

  const handleExport = async (type) => {
    setExportingType(type);
    try {
      const payload = {
        data,
        columns: activeColumns,
        filename: `report_${Date.now()}`
      };
      const res = await fetch(`/export/${type}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!res.ok) throw new Error(`Export failed (${res.status})`);
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const ext = type === 'excel' ? 'xlsx' : type;
      a.download = `JGH_Report_${Date.now()}.${ext}`;
      a.click();
      window.URL.revokeObjectURL(url);
      if (onToast) onToast({ type: 'success', message: `Report exported as .${ext} successfully.` });
    } catch (err) {
      console.error('Export error:', err);
      if (onToast) onToast({ type: 'error', message: `Export failed: ${err.message}` });
    } finally {
      setExportingType(null);
    }
  };

  if (!data || data.length === 0) {
    return (
      <div className="datagrid-container">
        <div className="datagrid-empty">
          <Table2 size={32} style={{ color: 'var(--text-muted)' }} />
          <div style={{ fontWeight: 600, fontSize: '0.9375rem', color: 'var(--text-primary)' }}>No records returned</div>
          <div style={{ fontSize: '0.8125rem' }}>The query completed successfully with zero matching rows.</div>
        </div>
      </div>
    );
  }

  const tableContent = (
    <div className="datagrid-container" style={isFullscreen ? { height: '100%', border: 'none', borderRadius: 0 } : {}}>
      {/* ── Toolbar ── */}
      <div className="datagrid-toolbar">
        {/* Search */}
        <div className="datagrid-search-wrap">
          <Search size={14} className="datagrid-search-icon" />
          <input
            type="text"
            className="datagrid-search-input"
            placeholder="Search within results..."
            value={searchTerm}
            onChange={(e) => { setSearchTerm(e.target.value); setPage(0); }}
          />
        </div>

        {/* Actions */}
        <div className="datagrid-actions">
          {/* Row Count Info */}
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 500, marginRight: '0.25rem' }}>
            {sortedData.length > 0 ? page * pageSize + 1 : 0}–{Math.min((page + 1) * pageSize, sortedData.length)} of {sortedData.length} rows
          </span>

          {/* Copy Table */}
          <button
            className="btn btn-secondary"
            style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }}
            onClick={handleCopyTable}
            title="Copy table as CSV to clipboard"
          >
            <Copy size={12} />
            <span>Copy</span>
          </button>

          {/* Export Dropdown / Buttons */}
          <div style={{ display: 'flex', gap: '0.25rem' }}>
            <button
              className="btn btn-secondary"
              style={{ padding: '0.3rem 0.55rem', fontSize: '0.75rem' }}
              onClick={() => handleExport('csv')}
              disabled={exportingType === 'csv'}
              title="Download CSV"
            >
              <FileText size={12} />
              <span>CSV</span>
            </button>
            <button
              className="btn btn-secondary"
              style={{ padding: '0.3rem 0.55rem', fontSize: '0.75rem' }}
              onClick={() => handleExport('excel')}
              disabled={exportingType === 'excel'}
              title="Download Excel (.xlsx)"
            >
              <FileSpreadsheet size={12} />
              <span>Excel</span>
            </button>
            <button
              className="btn btn-secondary"
              style={{ padding: '0.3rem 0.55rem', fontSize: '0.75rem' }}
              onClick={() => handleExport('pdf')}
              disabled={exportingType === 'pdf'}
              title="Download PDF"
            >
              <FileText size={12} />
              <span>PDF</span>
            </button>
          </div>

          {/* Fullscreen Toggle */}
          <button
            className="btn-icon"
            onClick={() => setIsFullscreen(!isFullscreen)}
            title={isFullscreen ? "Exit Fullscreen" : "Fullscreen View"}
          >
            {isFullscreen ? <Minimize2 size={15} /> : <Maximize2 size={15} />}
          </button>
        </div>
      </div>

      {/* ── Table Area ── */}
      <div className="datagrid-table-wrap dark-scroll" style={isFullscreen ? { maxHeight: 'calc(100vh - 160px)' } : {}}>
        <table className="datagrid-table">
          <thead>
            <tr>
              <th className="datagrid-th" style={{ width: '40px', textAlign: 'center' }}>#</th>
              {activeColumns.map((col) => {
                const isSorted = sortConfig.key === col;
                return (
                  <th
                    key={col}
                    className="datagrid-th"
                    onClick={() => handleSort(col)}
                    title={`Click to sort by ${col}`}
                  >
                    <div className="datagrid-th-inner">
                      <span>{col}</span>
                      {isSorted ? (
                        sortConfig.direction === 'asc' ? (
                          <ArrowUp size={12} className="datagrid-sort-icon" />
                        ) : (
                          <ArrowDown size={12} className="datagrid-sort-icon" />
                        )
                      ) : (
                        <ArrowUpDown size={11} style={{ opacity: 0.35 }} />
                      )}
                    </div>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {paginatedData.map((row, rIdx) => {
              const globalIdx = page * pageSize + rIdx + 1;
              return (
                <tr key={rIdx} className="datagrid-row">
                  <td className="datagrid-td" style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                    {globalIdx}
                  </td>
                  {activeColumns.map((col, cIdx) => {
                    const cellKey = `${rIdx}-${cIdx}`;
                    const val = row[col];
                    const isCopied = copiedCell === cellKey;

                    return (
                      <td
                        key={cIdx}
                        className="datagrid-td"
                        onClick={() => handleCopyCell(val, cellKey)}
                        title="Click to copy cell value"
                        style={{ cursor: 'pointer' }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.5rem' }}>
                          <span>{formatCellValue(val, col)}</span>
                          {isCopied && <Check size={12} style={{ color: 'var(--success)', flexShrink: 0 }} />}
                        </div>
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>

        {paginatedData.length === 0 && (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            No rows match your filter "{searchTerm}".
          </div>
        )}
      </div>

      {/* ── Pagination Footer ── */}
      <div className="datagrid-footer">
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <span>
            Page <strong style={{color: 'var(--text-primary)'}}>{page + 1}</strong> of <strong style={{color: 'var(--text-primary)'}}>{totalPages}</strong>
          </span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Show:</span>
            <select
              value={pageSize}
              onChange={(e) => { setPageSize(Number(e.target.value)); setPage(0); }}
              style={{
                fontSize: '0.8125rem',
                padding: '0.25rem 0.5rem',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-color)',
                background: 'var(--bg-surface)',
                color: 'var(--text-primary)',
                outline: 'none'
              }}
            >
              <option value={10}>10 rows</option>
              <option value={25}>25 rows</option>
              <option value={50}>50 rows</option>
              <option value={100}>100 rows</option>
            </select>
          </div>
        </div>

        <div className="datagrid-pagination">
          <button
            className="datagrid-page-btn"
            onClick={() => setPage(p => Math.max(p - 1, 0))}
            disabled={page === 0}
          >
            <ChevronLeft size={14} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '4px' }} /> Prev
          </button>
          <button
            className="datagrid-page-btn"
            onClick={() => setPage(p => Math.min(p + 1, totalPages - 1))}
            disabled={page >= totalPages - 1}
          >
            Next <ChevronRight size={14} style={{ display: 'inline', verticalAlign: 'middle', marginLeft: '4px' }} />
          </button>
        </div>
      </div>
    </div>
  );

  if (isFullscreen) {
    return (
      <div className="fullscreen-grid-modal">
        <div style={{ padding: '1rem 1.5rem', borderBottom: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'var(--bg-surface)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <Table2 size={18} style={{ color: 'var(--primary)' }} />
            <h3 style={{ fontSize: '1rem', fontWeight: 600, margin: 0, color: 'var(--text-primary)' }}>{title} (Fullscreen Grid)</h3>
          </div>
          <button className="btn-icon" onClick={() => setIsFullscreen(false)} title="Close Fullscreen">
            <X size={20} />
          </button>
        </div>
        <div style={{ flex: 1, overflow: 'hidden' }}>
          {tableContent}
        </div>
      </div>
    );
  }

  return tableContent;
};

export default DataGrid;
