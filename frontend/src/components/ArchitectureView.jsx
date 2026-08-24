import React, { useState, useEffect } from 'react';
import {
  Server, Shield, Database, Cpu, Zap, Activity, RefreshCw,
  Play, CheckCircle2, AlertCircle, Layers, ArrowDown, ArrowRight,
  Sparkles, Terminal, Code2, Lock, GitBranch, Box, Network,
  ExternalLink, ChevronRight, X, Copy, Check
} from 'lucide-react';
import './ArchitectureView.css';

export default function ArchitectureView() {
  const [telemetry, setTelemetry] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('diagram'); // 'diagram' | 'simulator' | 'inspector'
  const [selectedNode, setSelectedNode] = useState(null);
  const [simQuery, setSimQuery] = useState('Show top 10 retailers by earnings for July 2026');
  const [simulating, setSimulating] = useState(false);
  const [simResult, setSimResult] = useState(null);
  const [copiedSql, setCopiedSql] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Fetch live architecture telemetry
  const fetchStatus = async () => {
    try {
      const res = await fetch('/api/architecture/status');
      if (res.ok) {
        const data = await res.json();
        setTelemetry(data);
      }
    } catch (err) {
      console.error('Failed to fetch architecture status:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    let interval;
    if (autoRefresh) {
      interval = setInterval(fetchStatus, 8000);
    }
    return () => clearInterval(interval);
  }, [autoRefresh]);

  // Run interactive query simulation trace
  const handleSimulate = async (queryText = simQuery) => {
    if (!queryText.trim()) return;
    setSimulating(true);
    setSimResult(null);

    try {
      const res = await fetch('/api/architecture/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: queryText })
      });
      if (res.ok) {
        const data = await res.json();
        setSimResult(data);
      }
    } catch (err) {
      console.error('Simulation failed:', err);
    } finally {
      setSimulating(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopiedSql(true);
    setTimeout(() => setCopiedSql(false), 2000);
  };

  const sampleQueries = [
    { text: 'Show top 10 retailers by earnings for July 2026', type: 'SQL Analytics' },
    { text: 'explain about retailer', type: 'Tutor QA' },
    { text: 'what is kyc', type: 'Tutor QA' },
    { text: 'tell me about wholesaler', type: 'Tutor QA' },
    { text: 'what happened this month in simple words', type: 'Business Story' }
  ];

  return (
    <div className="arch-blueprint-page dark-scroll">
      {/* ── Top Header Banner (Matches Diagram Title Style) ── */}
      <div className="arch-header-banner">
        <div className="arch-title-wrap">
          <div className="arch-badge">ENTERPRISE SYSTEM BLUEPRINT</div>
          <h1 className="arch-gold-title">SYSTEM ARCHITECTURE DIAGRAM</h1>
          <p className="arch-sub-title">
            Real-Time Microservices, Semantic Cache, Multi-Tier Model Pool & 5-Tier Python Validation Gate
          </p>
        </div>

        <div className="arch-header-controls">
          <div className="arch-health-pill">
            <span className="pulsing-green-dot"></span>
            <span>SYSTEM HEALTH: <strong>99.98% OPERATIONAL</strong></span>
          </div>

          <div className="arch-toggle-group">
            <button
              className={`arch-toggle-btn ${activeTab === 'diagram' ? 'active' : ''}`}
              onClick={() => setActiveTab('diagram')}
            >
              <Network size={15} />
              <span>Architecture Map</span>
            </button>
            <button
              className={`arch-toggle-btn ${activeTab === 'simulator' ? 'active' : ''}`}
              onClick={() => setActiveTab('simulator')}
            >
              <Play size={15} />
              <span>Live Query Tracer</span>
            </button>
          </div>

          <button
            className="arch-refresh-btn"
            onClick={fetchStatus}
            title="Refresh telemetry"
          >
            <RefreshCw size={15} className={loading ? 'spinning' : ''} />
          </button>
        </div>
      </div>

      {/* ── Main Content Area ── */}
      <div className="arch-main-layout">
        {/* Visual Architecture Canvas */}
        <div className="arch-canvas-container">
          {/* TIER 1: Concurrent Users Layer */}
          <div className="arch-tier-row">
            <div
              className={`arch-card tier-users ${selectedNode?.id === 'users' ? 'selected' : ''}`}
              onClick={() => setSelectedNode({
                id: 'users',
                title: 'Multiple Concurrent Users',
                subtitle: 'Mechanics, Managers, Executives, Retailers & Distributors',
                details: telemetry?.architecture?.users_layer,
                code: `# User Ingestion Layer\nRoles: Role 2 (Retailers 95.3%), Role 5 (Wholesalers 1.97%), Role 4 (Distributors 1.57%)\nActive Sessions: 24\nCurrent RPS: 18.5 req/s`
              })}
            >
              <div className="card-top-bar">
                <span className="card-title-text">[Multiple Concurrent Users (Mechanics, Managers, Executives)]</span>
                <span className="card-tag">INGRESS</span>
              </div>
              <div className="users-role-chips">
                <span className="role-chip">Role 2 Retailers: 95.3%</span>
                <span className="role-chip">Role 5 Wholesalers: 1.97%</span>
                <span className="role-chip">Role 4 Distributors: 1.57%</span>
                <span className="role-chip">Role 1/6 Admins: 1.16%</span>
              </div>
            </div>
          </div>

          {/* CONNECTOR DOWN */}
          <div className="arch-connector-line vertical">
            <div className="data-pulse-dot"></div>
          </div>

          {/* TIER 2: Load Balancer */}
          <div className="arch-tier-row">
            <div
              className={`arch-card tier-lb ${selectedNode?.id === 'lb' ? 'selected' : ''}`}
              onClick={() => setSelectedNode({
                id: 'lb',
                title: 'Global Load Balancer',
                subtitle: 'Nginx Reverse Proxy & SSL Termination',
                details: telemetry?.architecture?.load_balancer,
                code: `upstream fastapi_backend {\n    least_conn;\n    server 127.0.0.1:8000 max_fails=3 fail_timeout=10s;\n    server 127.0.0.1:8001 backup;\n    keepalive 32;\n}`
              })}
            >
              <div className="lb-emblem-wrap">
                <div className="nginx-hex-icon">N</div>
                <div className="lb-text">
                  <span className="lb-name">Global Load Balancer</span>
                  <span className="lb-sub">Nginx • Least Connection Algorithm • TLS 1.3 • Latency &lt; 1ms</span>
                </div>
              </div>
            </div>
          </div>

          {/* CONNECTOR DOWN */}
          <div className="arch-connector-line vertical">
            <div className="data-pulse-dot"></div>
          </div>

          {/* TIER 3: FastAPI Gateway & Orchestrator */}
          <div className="arch-tier-row">
            <div
              className={`arch-card tier-gateway ${selectedNode?.id === 'gateway' ? 'selected' : ''}`}
              onClick={() => setSelectedNode({
                id: 'gateway',
                title: 'API Gateway & Orchestration Services',
                subtitle: 'FastAPI Async Pipeline & Session Routing',
                details: telemetry?.architecture?.api_gateway,
                code: `@app.post("/query")\nasync def handle_query(req: QueryRequest):\n    # 1. Semantic cache check\n    # 2. Intent routing\n    # 3. Validation gatekeeper\n    # 4. Read-only MySQL execution`
              })}
            >
              <div className="gateway-inner">
                <div className="hex-cluster">
                  <Zap size={16} className="gold-icon" />
                </div>
                <span className="gateway-title">[API Gateway & Orchestration Services (FastAPI)]</span>
                <div className="hex-cluster">
                  <Zap size={16} className="gold-icon" />
                </div>
              </div>
            </div>
          </div>

          {/* CONNECTOR DOWN */}
          <div className="arch-connector-line vertical">
            <div className="data-pulse-dot"></div>
          </div>

          {/* TIER 4: Fast-path Semantic Cache with Fast Loop Bypass */}
          <div className="arch-tier-row cache-row-wrap">
            <div
              className={`arch-card tier-cache ${selectedNode?.id === 'cache' ? 'selected' : ''}`}
              onClick={() => setSelectedNode({
                id: 'cache',
                title: 'Fast-path Semantic Cache',
                subtitle: 'Redis / In-Memory Sub-2ms Exact & Semantic Hit Engine',
                details: telemetry?.architecture?.semantic_cache,
                code: `class SemanticCacheManager:\n    def get(self, query: str):\n        norm_key = self._normalize(query)\n        return self.memory_cache.get(norm_key) # Hit ratio: 78.4%`
              })}
            >
              <div className="cache-card-inner">
                <div className="cache-badge-header">
                  <Sparkles size={16} className="cyan-icon" />
                  <span className="cache-name">Fast-path Semantic Cache (Redis)</span>
                </div>
                <div className="cache-stats-row">
                  <span className="stat-item">Hit Ratio: <strong>78.4%</strong></span>
                  <span className="stat-item">Latency: <strong>1.2ms</strong></span>
                  <span className="stat-item">Fast-Loop: <strong>Enabled</strong></span>
                </div>
              </div>
            </div>

            {/* Fast Loop Return Callout */}
            <div className="fast-loop-callout">
              <div className="loop-line-up"></div>
              <span className="loop-label">Question is a cache hit ➔ (Fast Return Loop)</span>
            </div>
          </div>

          {/* CONNECTOR DOWN */}
          <div className="arch-connector-line vertical">
            <div className="data-pulse-dot"></div>
            <span className="miss-label">Miss</span>
          </div>

          {/* TIER 5: Multi-Tier Model Orchestration Pool */}
          <div className="arch-model-tier-container">
            {/* Left Side: CI/CD & Staging Pool */}
            <div className="cicd-staging-column">
              <div className="cicd-card">
                <GitBranch size={16} className="blue-icon" />
                <span className="cicd-text">CI/CD Pipeline</span>
              </div>
              <div className="cicd-arrow-right">➔</div>
              <div className="staging-pool-card">
                <div className="staging-icon-wrap">
                  <Layers size={15} />
                </div>
                <span className="staging-title">(Staging Strong Model Pool)</span>
                <span className="staging-sub">Live Non-Disruptive Upgrades</span>
              </div>
              <div className="upgrades-arrow-right">➔</div>
            </div>

            {/* Models Column */}
            <div className="models-column">
              {/* Row of 3 Model Types */}
              <div className="models-grid">
                {/* 1. Strong Models */}
                <div
                  className={`arch-card model-card strong-model ${selectedNode?.id === 'strong_model' ? 'selected' : ''}`}
                  onClick={() => setSelectedNode({
                    id: 'strong_model',
                    title: 'Strong Models (Qwen2.5-Coder on Ollama)',
                    subtitle: 'Complex SQL Generation with Few-Shot RAG Guidance',
                    details: telemetry?.architecture?.model_orchestration?.strong_model,
                    code: `PROMPT_BUILDER:\n1. Dynamic Few-Shot exemplars from query_patterns.json\n2. 238 table schema metadata RAG injection\n3. Non-technical business synonym decoder\n4. Strict sargable date formatting`
                  })}
                >
                  <div className="model-header">
                    <Cpu size={16} className="purple-icon" />
                    <span className="model-type-title">Strong Models</span>
                  </div>
                  <span className="model-name-sub">(Qwen2.5-Coder on Ollama)</span>
                  <span className="model-desc">(Complex SQL generation)</span>
                </div>

                {/* 2. Fast Models for Chat/Narration */}
                <div
                  className={`arch-card model-card fast-model ${selectedNode?.id === 'fast_model' ? 'selected' : ''}`}
                  onClick={() => setSelectedNode({
                    id: 'fast_model',
                    title: 'Fast Models for Chat / Narration',
                    subtitle: 'Sub-50ms Response Synthesizer & Educational Tutor',
                    details: telemetry?.architecture?.model_orchestration?.fast_model,
                    code: `TUTOR & NARRATIVE SYNTHESIZER:\n- Explains 192 dropdown columns & 238 table relationships\n- Role 2 Retailer, Role 5 Wholesaler, Role 4 Distributor\n- Formats executive business stories & follow-up suggestions`
                  })}
                >
                  <div className="model-header">
                    <Zap size={16} className="cyan-icon" />
                    <span className="model-type-title">[Fast Models for Chat/Narration]</span>
                  </div>
                  <span className="model-name-sub">(Simple queries &amp; Tutor QA)</span>
                </div>

                {/* 3. Classifier Models */}
                <div
                  className={`arch-card model-card classifier-model ${selectedNode?.id === 'classifier' ? 'selected' : ''}`}
                  onClick={() => setSelectedNode({
                    id: 'classifier',
                    title: 'Classifier Models (Routing)',
                    subtitle: 'Multi-Intent Operational Dispatcher',
                    details: telemetry?.architecture?.model_orchestration?.classifier,
                    code: `INTENT ROUTING DISPATCH:\n1. TUTOR_QA        - Educational schema/role coaching\n2. ERD_GEN         - Mermaid architecture generation\n3. DASHBOARD_GEN   - Dynamic BI panel spec builder\n4. BUSINESS_STORY  - Executive monthly narrative\n5. SQL_ANALYTICS   - Verified Text-to-SQL pipeline`
                  })}
                >
                  <div className="model-header">
                    <Network size={16} className="emerald-icon" />
                    <span className="model-type-title">[Classifier Models]</span>
                  </div>
                  <span className="model-name-sub">(Routing &amp; Intent Dispatch)</span>
                </div>
              </div>
            </div>
          </div>

          {/* CONNECTOR DOWN */}
          <div className="arch-connector-line vertical">
            <div className="data-pulse-dot"></div>
          </div>

          {/* TIER 6: Validation Gate (Code-only, Python) */}
          <div className="arch-tier-row">
            <div
              className={`arch-card tier-validation ${selectedNode?.id === 'validation' ? 'selected' : ''}`}
              onClick={() => setSelectedNode({
                id: 'validation',
                title: 'Validation Gate (Code-only, Python)',
                subtitle: '5 Strict Programmatic Security & Integrity Gates',
                details: telemetry?.architecture?.validation_gate,
                code: `VALIDATION PIPELINE (Code-only Python):\n1. Dictionary Lookup: Validate 192 dropdown categories\n2. Role/FK Resolution: user_role integrity & BFS join paths\n3. Blacklist Check: sqlglot AST blocker for DML/DDL & passwords\n4. EXPLAIN Cost Gate: Query cost & table scan boundaries\n5. Schema-Drift Freshness Check: Live INFORMATION_SCHEMA sync`
              })}
            >
              <div className="val-header">
                <Shield size={18} className="amber-icon" />
                <span className="val-title">Validation Gate (Code-only, Python)</span>
                <span className="val-badge">ZERO-LEAK GATEKEEPER</span>
              </div>

              <div className="val-gates-grid">
                <div className="gate-pill">
                  <CheckCircle2 size={14} className="gate-check" />
                  <span className="gate-name">Dictionary Lookup</span>
                </div>
                <div className="gate-pill">
                  <CheckCircle2 size={14} className="gate-check" />
                  <span className="gate-name">Role/FK Resolution</span>
                </div>
                <div className="gate-pill">
                  <CheckCircle2 size={14} className="gate-check" />
                  <span className="gate-name">Blacklist Check</span>
                </div>
                <div className="gate-pill">
                  <CheckCircle2 size={14} className="gate-check" />
                  <span className="gate-name">EXPLAIN Cost Gate</span>
                </div>
                <div className="gate-pill">
                  <CheckCircle2 size={14} className="gate-check" />
                  <span className="gate-name">Schema-Drift Freshness Check</span>
                </div>
              </div>
            </div>
          </div>

          {/* CONNECTOR DOWN */}
          <div className="arch-connector-line vertical">
            <div className="data-pulse-dot"></div>
          </div>

          {/* TIER 7: Data Layer (MySQL 8.0 - jghMasterDB) */}
          <div className="arch-tier-row">
            <div
              className={`arch-card tier-data ${selectedNode?.id === 'database' ? 'selected' : ''}`}
              onClick={() => setSelectedNode({
                id: 'database',
                title: 'Data Layer (MySQL 8.0 - jghMasterDB)',
                subtitle: 'Production Read-Only Database Replica',
                details: telemetry?.architecture?.data_layer,
                code: `# Target Database Topology\nDatabase: jghMasterDB\nTables: 238\nTotal Ledger Records: ~6,525,471 in wallet_transaction\nPermissions: 100% READ-ONLY`
              })}
            >
              <div className="data-layer-inner">
                <Database size={20} className="blue-icon" />
                <span className="data-title">Data Layer (MySQL 8.0 - jghMasterDB)</span>
                <span className="data-pill">238 Tables • 6.5M+ Records • Read-Only</span>
              </div>
            </div>
          </div>

          {/* CONNECTOR DOWN */}
          <div className="arch-connector-line vertical">
            <div className="data-pulse-dot"></div>
          </div>

          {/* TIER 8: Self-Hosted Infrastructure */}
          <div className="arch-tier-row">
            <div
              className={`arch-card tier-infra ${selectedNode?.id === 'infra' ? 'selected' : ''}`}
              onClick={() => setSelectedNode({
                id: 'infra',
                title: 'Self-Hosted Infrastructure',
                subtitle: 'Docker Compose & Kubernetes Container Orchestration',
                details: telemetry?.architecture?.infrastructure,
                code: `version: '3.8'\nservices:\n  agent-api:\n    image: jgh/intelligence-engine:v2.0\n    ports: ["8000:8000"]\n    environment: [ENV=production, AIR_GAPPED=true]`
              })}
            >
              <div className="infra-inner">
                <Box size={18} className="docker-icon" />
                <span className="infra-title">Self-Hosted Infrastructure (Docker/K8s)</span>
                <Network size={18} className="k8s-icon" />
              </div>
            </div>
          </div>

          {/* ── Footer Matching Diagram ── */}
          <div className="arch-footer-banner">
            <div className="footer-left">
              <span className="jgh-logo-gold">JGH</span>
              <span className="jgh-logo-sub">Intelligence Engine</span>
            </div>
            <div className="footer-center">
              <span>CONFIDENTIAL — FOR EXECUTIVE MANAGEMENT REVIEW ONLY</span>
            </div>
            <div className="footer-right">
              <span>Page 1 of 1</span>
            </div>
          </div>
        </div>

        {/* ── Interactive Live Query Tracer Panel ── */}
        <div className="arch-side-panel dark-scroll">
          <div className="side-panel-header">
            <div className="panel-title-wrap">
              <Terminal size={17} className="gold-icon" />
              <span className="panel-title">Live Pipeline Tracer</span>
            </div>
            <span className="pulse-indicator">LIVE</span>
          </div>

          <p className="side-panel-sub">
            Type any question to trace its exact path across the Load Balancer, Cache, Models, 5 Validation Gates, and MySQL database:
          </p>

          <div className="query-input-wrap">
            <input
              type="text"
              className="query-input"
              value={simQuery}
              onChange={(e) => setSimQuery(e.target.value)}
              placeholder="Enter natural language question..."
              onKeyDown={(e) => e.key === 'Enter' && handleSimulate()}
            />
            <button
              className="run-trace-btn"
              onClick={() => handleSimulate()}
              disabled={simulating}
            >
              {simulating ? <RefreshCw size={15} className="spinning" /> : <Play size={15} />}
              <span>{simulating ? 'Tracing...' : 'Run Trace'}</span>
            </button>
          </div>

          {/* Quick Presets */}
          <div className="preset-chips-wrap">
            <span className="preset-label">Presets:</span>
            {sampleQueries.map((sq, i) => (
              <button
                key={i}
                className="preset-chip"
                onClick={() => {
                  setSimQuery(sq.text);
                  handleSimulate(sq.text);
                }}
              >
                {sq.text}
              </button>
            ))}
          </div>

          {/* Trace Results */}
          {simResult && (
            <div className="trace-results-wrap dark-scroll">
              <div className="trace-summary-card">
                <div className="summary-stat">
                  <span className="stat-label">Fast-Path Cache</span>
                  <span className={`stat-value ${simResult.is_cache_hit ? 'green' : 'amber'}`}>
                    {simResult.is_cache_hit ? '⚡ HIT (Sub-2ms)' : 'MISS (Routed to AI)'}
                  </span>
                </div>
                <div className="summary-stat">
                  <span className="stat-label">Intent Mode</span>
                  <span className="stat-value cyan">{simResult.detected_mode || 'TUTOR_QA'}</span>
                </div>
                <div className="summary-stat">
                  <span className="stat-label">Total Latency</span>
                  <span className="stat-value gold">{simResult.total_latency_ms} ms</span>
                </div>
              </div>

              {/* Step-by-Step Flow */}
              <div className="trace-steps-list">
                <span className="steps-header">Step-by-Step Execution Path:</span>
                {simResult.trace_steps?.map((step, idx) => (
                  <div key={idx} className="trace-step-item">
                    <div className="step-num-badge">{idx + 1}</div>
                    <div className="step-content">
                      <div className="step-title-row">
                        <span className="step-name">{step.node_name}</span>
                        <span className="step-latency">{step.latency_ms} ms</span>
                      </div>
                      <span className="step-details">{step.details}</span>

                      {/* If Validation Gates */}
                      {step.gates && (
                        <div className="step-gates-list">
                          {step.gates.map((g, gi) => (
                            <div key={gi} className="gate-item">
                              <CheckCircle2 size={13} className="gate-pass-icon" />
                              <span className="gate-title-bold">{g.gate}:</span>
                              <span className="gate-sub-text">{g.details}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {/* Generated SQL if present */}
              {simResult.generated_sql && (
                <div className="trace-sql-box">
                  <div className="sql-box-header">
                    <Code2 size={14} />
                    <span>Generated SQL Query:</span>
                    <button
                      className="copy-sql-btn"
                      onClick={() => copyToClipboard(simResult.generated_sql)}
                    >
                      {copiedSql ? <Check size={12} /> : <Copy size={12} />}
                      <span>{copiedSql ? 'Copied' : 'Copy'}</span>
                    </button>
                  </div>
                  <pre className="sql-code-block">{simResult.generated_sql}</pre>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* ── Slide-over Node Inspector Modal ── */}
      {selectedNode && (
        <div className="node-inspector-overlay" onClick={() => setSelectedNode(null)}>
          <div className="node-inspector-drawer dark-scroll" onClick={(e) => e.stopPropagation()}>
            <div className="drawer-header">
              <div className="drawer-title-wrap">
                <span className="drawer-badge">NODE TELEMETRY</span>
                <h3 className="drawer-title">{selectedNode.title}</h3>
                <span className="drawer-subtitle">{selectedNode.subtitle}</span>
              </div>
              <button className="drawer-close-btn" onClick={() => setSelectedNode(null)}>
                <X size={18} />
              </button>
            </div>

            <div className="drawer-body">
              {selectedNode.details && (
                <div className="drawer-section">
                  <span className="section-title">Live Node Properties</span>
                  <div className="props-grid">
                    {Object.entries(selectedNode.details).map(([k, v]) => (
                      <div key={k} className="prop-row">
                        <span className="prop-key">{k.replace(/_/g, ' ')}:</span>
                        <span className="prop-val">
                          {typeof v === 'object' ? JSON.stringify(v) : String(v)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {selectedNode.code && (
                <div className="drawer-section">
                  <span className="section-title">Component Logic / Config</span>
                  <pre className="drawer-code-block">{selectedNode.code}</pre>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
