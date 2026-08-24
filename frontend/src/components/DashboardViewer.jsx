import React, { useState } from 'react';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import { TrendingUp, LayoutDashboard, Download, FileText, FileSpreadsheet, Check } from 'lucide-react';

const COLORS = ['#2563EB', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#06B6D4'];

const DashboardViewer = ({ spec }) => {
  const [downloading, setDownloading] = useState(null);

  if (!spec) return null;

  const { title, period, metric_cards, charts } = spec;

  const handleExport = async (type) => {
    setDownloading(type);
    try {
      // Flatten chart data for export
      let exportRows = [];
      if (charts && charts.length > 0) {
        exportRows = charts[0].data || [];
      } else if (metric_cards) {
        exportRows = metric_cards;
      }

      const res = await fetch(`/api/export/${type}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          data: exportRows,
          title: title || "Dashboard Report",
          filename: `Dashboard_Report_${Date.now()}`
        })
      });

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const ext = type === 'excel' ? 'xlsx' : type;
      a.download = `Dashboard_Report_${Date.now()}.${ext}`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Dashboard Export Error:", err);
    } finally {
      setTimeout(() => setDownloading(null), 1000);
    }
  };

  return (
    <div className="dashboard-viewer-wrap">
      <div className="dashboard-header">
        <div className="dashboard-header-title">
          <LayoutDashboard size={18} className="dashboard-header-icon" />
          <h3>{title || "July Executive Dashboard"}</h3>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          {period && <span className="dashboard-period-badge">{period}</span>}

          {/* Floating Export Toolbar */}
          <div className="dashboard-export-toolbar" style={{ display: 'flex', gap: '0.35rem' }}>
            <button
              className="dl-btn csv"
              onClick={() => handleExport('csv')}
              title="Export CSV"
              style={{ fontSize: '0.72rem', padding: '0.25rem 0.5rem' }}
            >
              <FileText size={12} /> CSV
            </button>
            <button
              className="dl-btn excel"
              onClick={() => handleExport('excel')}
              title="Export Excel (.xlsx)"
              style={{ fontSize: '0.72rem', padding: '0.25rem 0.5rem' }}
            >
              <FileSpreadsheet size={12} /> Excel
            </button>
            <button
              className="dl-btn pdf"
              onClick={() => handleExport('pdf')}
              title="Export PDF Report"
              style={{ fontSize: '0.72rem', padding: '0.25rem 0.5rem' }}
            >
              <FileText size={12} /> PDF
            </button>
          </div>
        </div>
      </div>

      {/* KPI Metric Cards */}
      {metric_cards && metric_cards.length > 0 && (
        <div className="dashboard-kpi-grid">
          {metric_cards.map((card, idx) => (
            <div key={idx} className="dashboard-kpi-card">
              <div className="kpi-card-header">
                <span className="kpi-title">{card.title}</span>
                {card.change && (
                  <span className="kpi-change positive">
                    <TrendingUp size={12} /> {card.change}
                  </span>
                )}
              </div>
              <div className="kpi-value">{card.value}</div>
              {card.subtitle && <div className="kpi-subtitle">{card.subtitle}</div>}
            </div>
          ))}
        </div>
      )}

      {/* Charts Grid */}
      {charts && charts.length > 0 && (
        <div className="dashboard-charts-grid">
          {charts.map((c, cIdx) => (
            <div key={cIdx} className="dashboard-chart-box">
              <h4 className="chart-box-title">{c.title}</h4>
              <div className="chart-box-canvas" style={{ width: '100%', height: 260 }}>
                <ResponsiveContainer width="100%" height="100%">
                  {c.chart_type === 'pie' ? (
                    <PieChart>
                      <Pie
                        data={c.data}
                        dataKey={c.y_axis || 'count'}
                        nameKey={c.x_axis || 'reference_type'}
                        cx="50%"
                        cy="50%"
                        outerRadius={80}
                        fill="#2563EB"
                        label
                      >
                        {c.data.map((_, i) => (
                          <Cell key={`cell-${i}`} fill={COLORS[i % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip contentStyle={{ background: '#1E293B', borderColor: '#334155', borderRadius: 8, color: '#F8FAFC' }} />
                      <Legend />
                    </PieChart>
                  ) : c.chart_type === 'line' ? (
                    <LineChart data={c.data}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
                      <XAxis dataKey={c.x_axis} stroke="#94A3B8" fontSize={11} />
                      <YAxis stroke="#94A3B8" fontSize={11} />
                      <Tooltip contentStyle={{ background: '#1E293B', borderColor: '#334155', borderRadius: 8, color: '#F8FAFC' }} />
                      <Line type="monotone" dataKey={c.y_axis} stroke="#2563EB" strokeWidth={2.5} dot={{ r: 4 }} />
                    </LineChart>
                  ) : (
                    <BarChart data={c.data}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
                      <XAxis dataKey={c.x_axis} stroke="#94A3B8" fontSize={11} />
                      <YAxis stroke="#94A3B8" fontSize={11} />
                      <Tooltip contentStyle={{ background: '#1E293B', borderColor: '#334155', borderRadius: 8, color: '#F8FAFC' }} />
                      <Bar dataKey={c.y_axis} fill="#2563EB" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  )}
                </ResponsiveContainer>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default DashboardViewer;
