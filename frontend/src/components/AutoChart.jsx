import React, { useState, useMemo } from 'react';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { BarChart2, TrendingUp, PieChart as PieIcon } from 'lucide-react';

const CHART_COLORS = [
  '#3B82F6', '#8B5CF6', '#10B981', '#F59E0B', '#EF4444',
  '#06B6D4', '#EC4899', '#84CC16', '#F97316', '#6366F1',
];

const CHART_TYPES = [
  { id: 'bar', label: 'Bar', Icon: BarChart2 },
  { id: 'line', label: 'Line', Icon: TrendingUp },
  { id: 'pie', label: 'Pie', Icon: PieIcon },
];

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tooltip">
      {label && <div className="chart-tooltip-label">{label}</div>}
      {payload.map((entry, i) => (
        <div key={i} className="chart-tooltip-row" style={{ color: entry.color }}>
          <span>{entry.name}:</span>
          <span className="chart-tooltip-value">
            {typeof entry.value === 'number' ? entry.value.toLocaleString() : entry.value}
          </span>
        </div>
      ))}
    </div>
  );
};

const AutoChart = ({ columns = [], data = [] }) => {
  const [chartType, setChartType] = useState('bar');

  const { labelCol, numericCols, chartData } = useMemo(() => {
    if (!data.length || !columns.length) return { labelCol: null, numericCols: [], chartData: [] };

    // Detect numeric columns
    const numCols = columns.filter(col => {
      const vals = data.slice(0, 10).map(r => r[col]);
      return vals.some(v => v !== null && v !== undefined && !isNaN(Number(v)));
    });

    // Pick the best label column (non-numeric, or first col)
    const lblCol = columns.find(col => !numCols.includes(col)) || columns[0];

    // Use up to 20 rows for chart readability
    const slicedData = data.slice(0, 20).map(row => {
      const point = { name: String(row[lblCol] ?? '') };
      numCols.forEach(nc => { point[nc] = Number(row[nc]) || 0; });
      return point;
    });

    return { labelCol: lblCol, numericCols: numCols, chartData: slicedData };
  }, [columns, data]);

  // No numeric data → nothing to chart
  if (!numericCols.length || chartData.length === 0) return null;

  // Pie chart uses first numeric col only
  const pieData = chartData.map(d => ({ name: d.name, value: d[numericCols[0]] }));

  return (
    <div className="premium-card" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', fontWeight: 600, color: 'var(--text-primary)' }}>
          <BarChart2 size={18} style={{ color: 'var(--primary)' }} />
          <span>Data Visualization</span>
        </div>
        <div style={{ display: 'flex', gap: '0.25rem', background: 'var(--bg-surface-subtle)', padding: '0.25rem', borderRadius: 'var(--radius-md)' }}>
          {CHART_TYPES.map(({ id, label, Icon }) => (
            <button
              key={id}
              onClick={() => setChartType(id)}
              style={{
                display: 'flex', alignItems: 'center', gap: '0.4rem',
                padding: '0.4rem 0.85rem', fontSize: '0.8125rem', fontWeight: 500,
                border: 'none', borderRadius: 'var(--radius-sm)', cursor: 'pointer',
                background: chartType === id ? 'var(--bg-surface)' : 'transparent',
                color: chartType === id ? 'var(--text-primary)' : 'var(--text-muted)',
                boxShadow: chartType === id ? 'var(--shadow-xs)' : 'none',
                transition: 'all var(--transition-fast)'
              }}
            >
              <Icon size={14} />
              {label}
            </button>
          ))}
        </div>
      </div>

      <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-lg)', padding: '1.5rem', boxShadow: 'var(--shadow-sm)' }}>
        <ResponsiveContainer width="100%" height={300}>
          {chartType === 'bar' ? (
            <BarChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border-color)" />
              <XAxis dataKey="name" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} tickLine={false} axisLine={false} />
              <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 11 }} tickLine={false} axisLine={false} />
              <Tooltip content={<CustomTooltip />} cursor={{fill: 'var(--bg-hover)'}} />
              {numericCols.length > 1 && <Legend wrapperStyle={{ fontSize: '12px', color: 'var(--text-secondary)' }} />}
              {numericCols.map((col, i) => (
                <Bar key={col} dataKey={col} fill={CHART_COLORS[i % CHART_COLORS.length]} radius={[4, 4, 0, 0]} />
              ))}
            </BarChart>
          ) : chartType === 'line' ? (
            <LineChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border-color)" />
              <XAxis dataKey="name" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} tickLine={false} axisLine={false} />
              <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 11 }} tickLine={false} axisLine={false} />
              <Tooltip content={<CustomTooltip />} />
              {numericCols.length > 1 && <Legend wrapperStyle={{ fontSize: '12px', color: 'var(--text-secondary)' }} />}
              {numericCols.map((col, i) => (
                <Line
                  key={col}
                  type="monotone"
                  dataKey={col}
                  stroke={CHART_COLORS[i % CHART_COLORS.length]}
                  strokeWidth={3}
                  dot={{ r: 4, fill: CHART_COLORS[i % CHART_COLORS.length], strokeWidth: 2, stroke: 'var(--bg-surface)' }}
                  activeDot={{ r: 6 }}
                />
              ))}
            </LineChart>
          ) : (
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                outerRadius={110}
                innerRadius={60}
                dataKey="value"
                label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                labelLine={{ stroke: 'var(--border-color)', strokeWidth: 1 }}
              >
                {pieData.map((_, idx) => (
                  <Cell key={idx} fill={CHART_COLORS[idx % CHART_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: '12px', color: 'var(--text-secondary)' }} />
            </PieChart>
          )}
        </ResponsiveContainer>
      </div>

      {data.length > 20 && (
        <div style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', textAlign: 'center', marginTop: '0.5rem' }}>
          Showing first 20 rows for visualization. Download the full report for complete data.
        </div>
      )}
    </div>
  );
};

export default AutoChart;
