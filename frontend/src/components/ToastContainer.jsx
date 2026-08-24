import React from 'react';
import { CheckCircle2, AlertCircle, AlertTriangle, Info, X } from 'lucide-react';

export const ToastContainer = ({ toasts = [], onDismiss }) => {
  if (!toasts || toasts.length === 0) return null;

  return (
    <div className="toast-container">
      {toasts.map((toast) => {
        const Icon =
          toast.type === 'success' ? CheckCircle2 :
          toast.type === 'error' ? AlertCircle :
          toast.type === 'warning' ? AlertTriangle : Info;

        const iconColor =
          toast.type === 'success' ? '#10B981' :
          toast.type === 'error' ? '#EF4444' :
          toast.type === 'warning' ? '#F59E0B' : '#FBBF24';

        return (
          <div key={toast.id} className={`toast-item ${toast.type || 'info'}`}>
            <Icon size={18} style={{ color: iconColor, flexShrink: 0 }} />
            <div style={{ flex: 1, lineHeight: 1.4 }}>
              {toast.title && <div style={{ fontWeight: 600, fontSize: '0.875rem' }}>{toast.title}</div>}
              <div style={{ fontSize: '0.8125rem', color: '#E2E8F0' }}>{toast.message}</div>
            </div>
            {onDismiss && (
              <button
                onClick={() => onDismiss(toast.id)}
                style={{
                  color: '#94A3B8',
                  padding: '2px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
                title="Dismiss"
              >
                <X size={14} />
              </button>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default ToastContainer;
