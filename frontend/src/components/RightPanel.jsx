import React from 'react';
import { Database, AlertCircle, TrendingUp, CheckCircle, Table, Link } from 'lucide-react';
import './RightPanel.css';

const RightPanel = ({ context }) => {
  if (!context) {
    return (
      <div className="right-panel empty">
        <div className="empty-state">
          <Database size={24} className="text-tertiary mb-4" />
          <p>No active context</p>
          <span className="text-tertiary text-xs">Run a query to see investigation details</span>
        </div>
      </div>
    );
  }

  return (
    <div className="right-panel">
      <div className="panel-section">
        <h3 className="section-title">Context Analysis</h3>
        
        <div className="score-card">
          <div className="score-header">
            <span className="score-label">Confidence Score</span>
            <span className={`score-value ${context.confidence > 90 ? 'high' : 'medium'}`}>
              {context.confidence}%
            </span>
          </div>
          <div className="score-bar-bg">
            <div className="score-bar-fill" style={{ width: `${context.confidence}%` }}></div>
          </div>
        </div>
      </div>

      <div className="panel-section">
        <h3 className="section-title flex-align">
          <Table size={14} /> Tables Involved
        </h3>
        <div className="tag-list">
          {context.tables?.map((table, i) => (
            <span key={i} className="tag">{table}</span>
          ))}
          {!context.tables?.length && <span className="text-tertiary text-sm">None</span>}
        </div>
      </div>

      <div className="panel-section">
        <h3 className="section-title flex-align">
          <Link size={14} /> Relationships Mapped
        </h3>
        <div className="relationship-list">
          {context.relationships?.map((rel, i) => (
            <div key={i} className="rel-item">
              <span className="rel-text">{rel.replace('JOIN ', '').replace(' ON ', ' → ')}</span>
            </div>
          ))}
          {!context.relationships?.length && <span className="text-tertiary text-sm">No joins detected</span>}
        </div>
      </div>

      {context.plan && context.plan.cost > 0 && (
        <div className="panel-section">
          <h3 className="section-title flex-align">
            <TrendingUp size={14} /> Execution Plan
          </h3>
          <div className="info-box">
            <div className="info-row">
              <span className="info-label">Estimated Cost:</span>
              <span className="info-value">{context.plan.cost}</span>
            </div>
            {context.plan.warnings?.length > 0 && (
              <div className="warning-box mt-3">
                <AlertCircle size={14} className="text-yellow" />
                <span>{context.plan.warnings[0]}</span>
              </div>
            )}
          </div>
        </div>
      )}
      
      <div className="panel-section mt-auto">
        <div className="info-box success">
          <CheckCircle size={14} className="text-green" />
          <span className="text-sm">Verified against Enterprise Schema</span>
        </div>
      </div>
    </div>
  );
};

export default RightPanel;
