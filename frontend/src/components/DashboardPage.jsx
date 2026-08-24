import React, { useState } from 'react';
import {
  LayoutDashboard, TrendingUp, Users, Store, IndianRupee, Download,
  Filter, Calendar, MapPin, FileSpreadsheet, FileText, ArrowUpRight,
  ShieldCheck, BarChart3
} from 'lucide-react';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';

const REGION_DATA = [
  { region: 'Karnataka', earnings: 24000000, distributors: 98, retailers: 512 },
  { region: 'Maharashtra', earnings: 18500000, distributors: 74, retailers: 388 },
  { region: 'Tamil Nadu', earnings: 14200000, distributors: 45, retailers: 240 },
  { region: 'Delhi NCR', earnings: 11800000, distributors: 31, retailers: 144 },
];

const MONTHLY_TREND = [
  { month: 'Mar 2026', revenue: 1.8, transactions: 1240 },
  { month: 'Apr 2026', revenue: 1.95, transactions: 1390 },
  { month: 'May 2026', revenue: 2.1, transactions: 1480 },
  { month: 'Jun 2026', revenue: 2.25, transactions: 1590 },
  { month: 'Jul 2026', revenue: 2.4, transactions: 1720 },
];

const TOP_DISTRIBUTORS = [
  { name: 'Apex Auto Spares Bangalore', region: 'Karnataka', earnings: '₹42.5 L', status: 'Top Performer' },
  { name: 'Deccan Logistics Hub', region: 'Maharashtra', earnings: '₹38.2 L', status: 'Top Performer' },
  { name: 'Mysuru Direct Distributors', region: 'Karnataka', earnings: '₹29.8 L', status: 'Active' },
  { name: 'Coastal Spares Mangalore', region: 'Karnataka', earnings: '₹24.1 L', status: 'Active' },
  { name: 'Pune Wheels Network', region: 'Maharashtra', earnings: '₹21.0 L', status: 'Active' },
];

const CHART_COLORS = ['#0F172A', '#D97706', '#2563EB', '#10B981', '#8B5CF6'];

export const DashboardPage = ({ onToast }) => {
  const [selectedPeriod, setSelectedPeriod] = useState('July 2026');
  const [selectedRegion, setSelectedRegion] = useState('All Regions');
  const [isExporting, setIsExporting] = useState(false);

  // Dynamic Filtering Logic
  const filteredRegionData = selectedRegion === 'All Regions' 
    ? REGION_DATA 
    : REGION_DATA.filter(d => d.region === selectedRegion);

  const filteredDistributors = selectedRegion === 'All Regions'
    ? TOP_DISTRIBUTORS
    : TOP_DISTRIBUTORS.filter(d => d.region === selectedRegion);

  // KPI Calculations
  const totalEarnings = filteredRegionData.reduce((acc, curr) => acc + curr.earnings, 0);
  const totalDist = filteredRegionData.reduce((acc, curr) => acc + curr.distributors, 0);
  const totalRetailers = filteredRegionData.reduce((acc, curr) => acc + curr.retailers, 0);

  const formattedEarnings = (totalEarnings / 10000000).toFixed(1); // Convert to Cr

  const handleExport = async (type) => {
    setIsExporting(true);
    try {
      const payload = {
        data: filteredRegionData,
        columns: ['region', 'earnings', 'distributors', 'retailers'],
        filename: `Executive_Dashboard_${selectedPeriod.replace(' ', '_')}_${selectedRegion.replace(' ', '_')}`
      };
      const res = await fetch(`/export/${type}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!res.ok) throw new Error('Export failed');
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const ext = type === 'excel' ? 'xlsx' : type;
      a.download = `JGH_Executive_Dashboard_${Date.now()}.${ext}`;
      a.click();
      window.URL.revokeObjectURL(url);
      if (onToast) onToast({ type: 'success', message: `Executive Dashboard exported as .${ext}` });
    } catch (e) {
      if (onToast) onToast({ type: 'error', message: 'Failed to export dashboard.' });
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="dark-scroll" style={{ flex: 1, overflowY: 'auto', padding: '2rem' }}>
      <div style={{ maxWidth: '1180px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
        
        {/* Header & Filter Controls */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
              Executive Performance Dashboard
            </h2>
            <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
              Consolidated enterprise metrics & regional distribution analysis
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', flexWrap: 'wrap' }}>
            {/* Period Selector */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', background: '#FFFFFF', border: '1px solid var(--border-strong)', padding: '0.3rem 0.6rem', borderRadius: 'var(--radius-md)' }}>
              <Calendar size={13} style={{ color: 'var(--text-muted)' }} />
              <select
                value={selectedPeriod}
                onChange={e => setSelectedPeriod(e.target.value)}
                style={{ border: 'none', background: 'transparent', fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-primary)', cursor: 'pointer' }}
              >
                <option value="July 2026">July 2026</option>
                <option value="Q2 2026">Q2 2026 (Apr–Jun)</option>
                <option value="Year to Date">Year to Date 2026</option>
              </select>
            </div>

            {/* Region Selector */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', background: '#FFFFFF', border: '1px solid var(--border-strong)', padding: '0.3rem 0.6rem', borderRadius: 'var(--radius-md)' }}>
              <MapPin size={13} style={{ color: 'var(--text-muted)' }} />
              <select
                value={selectedRegion}
                onChange={e => setSelectedRegion(e.target.value)}
                style={{ border: 'none', background: 'transparent', fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-primary)', cursor: 'pointer' }}
              >
                <option value="All Regions">All Regions</option>
                <option value="Karnataka">Karnataka</option>
                <option value="Maharashtra">Maharashtra</option>
                <option value="Tamil Nadu">Tamil Nadu</option>
              </select>
            </div>

            {/* Export Actions */}
            <div style={{ display: 'flex', gap: '0.25rem' }}>
              <button
                className="btn btn-secondary"
                style={{ padding: '0.35rem 0.65rem', fontSize: '0.75rem' }}
                onClick={() => handleExport('excel')}
                disabled={isExporting}
              >
                <FileSpreadsheet size={13} />
                <span>Excel</span>
              </button>
              <button
                className="btn btn-secondary"
                style={{ padding: '0.35rem 0.65rem', fontSize: '0.75rem' }}
                onClick={() => handleExport('pdf')}
                disabled={isExporting}
              >
                <FileText size={13} />
                <span>PDF</span>
              </button>
            </div>
          </div>
        </div>

        {/* ── KPI Metric Cards ── */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.25rem' }}>
          
          <div className="premium-card" style={{ padding: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Total Distributor Earnings
              </span>
              <span className="status-badge status-success">
                <TrendingUp size={12} /> +12.4% MoM
              </span>
            </div>
            <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '0.75rem', fontFamily: 'var(--font-display)' }}>
              ₹{formattedEarnings} Cr
            </div>
            <span style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginTop: '0.5rem', display: 'block' }}>
              For {selectedPeriod} across {selectedRegion}
            </span>
          </div>

          <div className="premium-card" style={{ padding: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Active Distributors
              </span>
              <span className="status-badge" style={{ background: 'var(--primary-light)', color: 'var(--primary)', borderColor: 'var(--primary)' }}>
                Verified
              </span>
            </div>
            <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '0.75rem', fontFamily: 'var(--font-display)' }}>
              {totalDist}
            </div>
            <span style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginTop: '0.5rem', display: 'block' }}>
              {selectedRegion === 'All Regions' ? '98 in Karnataka • 74 in Maharashtra' : `${totalDist} in ${selectedRegion}`}
            </span>
          </div>

          <div className="premium-card" style={{ padding: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Registered Retailers
              </span>
              <span className="status-badge" style={{ background: 'var(--bg-hover)', color: 'var(--text-primary)' }}>
                +38 New
              </span>
            </div>
            <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '0.75rem', fontFamily: 'var(--font-display)' }}>
              {totalRetailers.toLocaleString()}
            </div>
            <span style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginTop: '0.5rem', display: 'block' }}>
              Active accounts across {selectedRegion === 'All Regions' ? 'all tiers' : selectedRegion}
            </span>
          </div>

          <div className="premium-card" style={{ padding: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                System Verification Rate
              </span>
              <span className="status-badge status-success">
                <ShieldCheck size={12} /> 100%
              </span>
            </div>
            <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--success)', marginTop: '0.75rem', fontFamily: 'var(--font-display)' }}>
              99.8%
            </div>
            <span style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginTop: '0.5rem', display: 'block' }}>
              Read-Only SQL Safety Enforced
            </span>
          </div>

        </div>

        {/* ── Charts Grid ── */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(480px, 1fr))', gap: '1.5rem' }}>
          
          {/* Monthly Revenue Trend */}
          <div className="premium-card">
            <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.9375rem' }}>
                <TrendingUp size={18} style={{ color: 'var(--primary)' }} />
                Monthly Revenue Trend (₹ Cr)
              </span>
              <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>March – July 2026</span>
            </div>
            <div style={{ padding: '1.5rem' }}>
              <div style={{ width: '100%', height: 260 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={MONTHLY_TREND} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border-color)" />
                    <XAxis dataKey="month" stroke="var(--text-muted)" fontSize={11} tickLine={false} axisLine={false} />
                    <YAxis stroke="var(--text-muted)" fontSize={11} unit=" Cr" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: 'var(--bg-surface)', color: 'var(--text-primary)', borderRadius: '8px', border: '1px solid var(--border-color)', boxShadow: 'var(--shadow-md)' }} />
                    <Line type="monotone" dataKey="revenue" stroke="var(--primary)" strokeWidth={3} dot={{ r: 4, fill: 'var(--primary)', stroke: 'var(--bg-surface)', strokeWidth: 2 }} activeDot={{ r: 6 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Regional Earnings Breakdown */}
          <div className="premium-card">
            <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.9375rem' }}>
                <BarChart3 size={18} style={{ color: 'var(--primary)' }} />
                Regional Earnings (₹)
              </span>
              <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>Distribution</span>
            </div>
            <div style={{ padding: '1.5rem' }}>
              <div style={{ width: '100%', height: 260 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={filteredRegionData} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border-color)" />
                    <XAxis dataKey="region" stroke="var(--text-muted)" fontSize={11} tickLine={false} axisLine={false} />
                    <YAxis stroke="var(--text-muted)" fontSize={11} tickFormatter={v => `₹${(v / 10000000).toFixed(1)}Cr`} tickLine={false} axisLine={false} />
                    <Tooltip
                      formatter={(val) => [`₹${(val / 10000000).toFixed(2)} Cr`, 'Earnings']}
                      contentStyle={{ background: 'var(--bg-surface)', color: 'var(--text-primary)', borderRadius: '8px', border: '1px solid var(--border-color)', boxShadow: 'var(--shadow-md)' }}
                      cursor={{fill: 'var(--bg-hover)'}}
                    />
                    <Bar dataKey="earnings" radius={[4, 4, 0, 0]}>
                      {filteredRegionData.map((entry, idx) => (
                        <Cell key={`cell-${idx}`} fill={CHART_COLORS[idx % CHART_COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

        </div>

        {/* ── Top Distributors Ranking ── */}
        <div className="premium-card">
          <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.9375rem' }}>
              <Users size={18} style={{ color: 'var(--primary)' }} />
              Top Performing Distributors ({selectedPeriod})
            </span>
            <span className="status-badge status-warning">
              Top 5 Volume Leaders
            </span>
          </div>
          <div style={{ overflowX: 'auto', borderRadius: '0 0 var(--radius-lg) var(--radius-lg)' }}>
            <table style={{ width: '100%', borderCollapse: 'separate', borderSpacing: 0 }}>
              <thead>
                <tr>
                  <th style={{ padding: '1rem 1.5rem', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', background: 'var(--bg-surface-subtle)', borderBottom: '1px solid var(--border-color)', textAlign: 'left', letterSpacing: '0.05em' }}>
                    Distributor Name
                  </th>
                  <th style={{ padding: '1rem 1.5rem', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', background: 'var(--bg-surface-subtle)', borderBottom: '1px solid var(--border-color)', textAlign: 'left', letterSpacing: '0.05em' }}>
                    Region
                  </th>
                  <th style={{ padding: '1rem 1.5rem', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', background: 'var(--bg-surface-subtle)', borderBottom: '1px solid var(--border-color)', textAlign: 'left', letterSpacing: '0.05em' }}>
                    Monthly Earnings
                  </th>
                  <th style={{ padding: '1rem 1.5rem', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', background: 'var(--bg-surface-subtle)', borderBottom: '1px solid var(--border-color)', textAlign: 'left', letterSpacing: '0.05em' }}>
                    Status
                  </th>
                </tr>
              </thead>
              <tbody>
                {filteredDistributors.length > 0 ? (
                  filteredDistributors.map((dist, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid var(--border-color)' }}>
                      <td style={{ padding: '1rem 1.5rem', fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-primary)', borderBottom: '1px solid var(--border-color)' }}>
                        {dist.name}
                      </td>
                      <td style={{ padding: '1rem 1.5rem', fontSize: '0.875rem', color: 'var(--text-secondary)', borderBottom: '1px solid var(--border-color)' }}>
                        {dist.region}
                      </td>
                      <td style={{ padding: '1rem 1.5rem', fontSize: '0.875rem', fontWeight: 700, color: 'var(--primary)', borderBottom: '1px solid var(--border-color)' }}>
                        {dist.earnings}
                      </td>
                      <td style={{ padding: '1rem 1.5rem', fontSize: '0.8125rem', borderBottom: '1px solid var(--border-color)' }}>
                        <span className={`status-badge ${dist.status === 'Top Performer' ? 'status-warning' : 'status-success'}`}>
                          {dist.status}
                        </span>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="4" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.875rem' }}>
                      No top distributors found for this region.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </div>
  );
};

export default DashboardPage;
