import React, { useState } from 'react';
import { Bookmark, Play, Trash2, Copy, Check, Search, Sparkles, Database } from 'lucide-react';

export const SavedQueriesView = ({
  savedQueries = [],
  onReRun,
  onRemoveBookmark,
  onToast
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [copiedId, setCopiedId] = useState(null);

  const filteredQueries = savedQueries.filter(q =>
    q.question.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (q.sql || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleCopySql = (sql, id) => {
    if (!sql) return;
    navigator.clipboard.writeText(sql);
    setCopiedId(id);
    if (onToast) onToast({ type: 'success', message: 'SQL copied to clipboard.' });
    setTimeout(() => setCopiedId(null), 1500);
  };

  return (
    <div className="dark-scroll" style={{ flex: 1, overflowY: 'auto', padding: '2rem' }}>
      <div style={{ maxWidth: '960px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
              Saved & Pinned Queries
            </h2>
            <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
              Quick-access library of key business analytical questions
            </span>
          </div>

          <div style={{ position: 'relative', width: '280px' }}>
            <Search size={14} style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <input
              type="text"
              className="input-base"
              placeholder="Search saved queries..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{ paddingLeft: '2.25rem', height: '36px', fontSize: '0.8125rem' }}
            />
          </div>
        </div>

        {/* Empty State */}
        {filteredQueries.length === 0 ? (
          <div style={{
            padding: '4rem 2rem',
            textAlign: 'center',
            background: 'var(--bg-surface)',
            border: '1px dashed var(--border-strong)',
            borderRadius: 'var(--radius-xl)',
            color: 'var(--text-muted)'
          }}>
            <Bookmark size={36} style={{ color: 'var(--accent-gold-500)', margin: '0 auto 1rem', opacity: 0.7 }} />
            <div style={{ fontWeight: 600, fontSize: '1rem', color: 'var(--text-primary)' }}>No saved queries yet</div>
            <div style={{ fontSize: '0.84375rem', marginTop: '0.35rem', maxWidth: '400px', margin: '0.35rem auto 0' }}>
              Bookmark any question in the AI Analytics Workspace by clicking the bookmark icon on any answer.
            </div>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(440px, 1fr))', gap: '1rem' }}>
            {filteredQueries.map((item, idx) => (
              <div
                key={idx}
                className="card"
                style={{
                  padding: '1.25rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.875rem',
                  justifyContent: 'space-between'
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '0.5rem', marginBottom: '0.5rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--accent-gold-700)', fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase' }}>
                      <Bookmark size={13} fill="currentColor" />
                      <span>Pinned Query</span>
                    </div>

                    <button
                      className="btn-icon"
                      onClick={() => onRemoveBookmark && onRemoveBookmark(item.question)}
                      title="Remove bookmark"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>

                  <h4 style={{ fontSize: '0.9375rem', fontWeight: 700, color: 'var(--text-primary)', margin: '0 0 0.5rem 0', lineHeight: 1.4 }}>
                    {item.question}
                  </h4>

                  {item.sql && (
                    <div style={{
                      background: '#0B192C',
                      borderRadius: 'var(--radius-md)',
                      padding: '0.625rem 0.875rem',
                      maxHeight: '80px',
                      overflow: 'hidden',
                      border: '1px solid #1E293B',
                      marginBottom: '0.5rem'
                    }}>
                      <code style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: '#38BDF8' }}>
                        {item.sql}
                      </code>
                    </div>
                  )}
                </div>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: '0.75rem', borderTop: '1px solid var(--border-subtle)' }}>
                  <button
                    className="btn btn-secondary"
                    style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }}
                    onClick={() => handleCopySql(item.sql, idx)}
                  >
                    {copiedId === idx ? <Check size={12} style={{ color: '#10B981' }} /> : <Copy size={12} />}
                    <span>{copiedId === idx ? 'Copied' : 'Copy SQL'}</span>
                  </button>

                  <button
                    className="btn btn-gold"
                    style={{ padding: '0.3rem 0.75rem', fontSize: '0.75rem' }}
                    onClick={() => onReRun && onReRun(item.question)}
                  >
                    <Play size={12} fill="#FFFFFF" />
                    <span>Run Query</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

      </div>
    </div>
  );
};

export default SavedQueriesView;
