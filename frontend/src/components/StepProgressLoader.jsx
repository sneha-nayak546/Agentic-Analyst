import React, { useState, useEffect } from 'react';
import { Bot, CheckCircle2, Loader2, Database, ShieldCheck, Cpu, BarChart3, Search, Target } from 'lucide-react';

const STEPS = [
  { id: 1, label: 'Understanding business question & intent...', icon: Bot },
  { id: 2, label: 'Resolving relevant database schema & relationships...', icon: Database },
  { id: 3, label: 'Synthesizing verified SQL query...', icon: Cpu },
  { id: 4, label: 'SQL validation — safety, schema & cost limits...', icon: ShieldCheck },
  { id: 5, label: 'Executing read-only query on database...', icon: Search },
  { id: 6, label: 'Verifying result accuracy against business rules...', icon: Target },
  { id: 7, label: 'Formatting business insights & preparing reports...', icon: BarChart3 },
];

export const StepProgressLoader = ({ question }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [elapsedMs, setElapsedMs] = useState(0);

  useEffect(() => {
    const startTime = Date.now();
    const timer = setInterval(() => {
      setElapsedMs(Date.now() - startTime);
    }, 100);

    // Step pacing simulation
    const stepInterval = setInterval(() => {
      setCurrentStep(prev => {
        if (prev < STEPS.length - 1) return prev + 1;
        return prev;
      });
    }, 700);

    return () => {
      clearInterval(timer);
      clearInterval(stepInterval);
    };
  }, []);

  return (
    <div style={{
      background: 'var(--bg-surface)',
      border: '1px solid var(--border-color)',
      borderRadius: 'var(--radius-xl)',
      padding: '1.5rem 1.75rem',
      boxShadow: 'var(--shadow-md)',
      maxWidth: '680px',
      width: '100%',
      display: 'flex',
      flexDirection: 'column',
      gap: '1.25rem',
      animation: 'fadeUp 0.3s ease-out'
    }}>
      {/* Header with question preview & elapsed timer */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.875rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
          <div style={{
            width: '28px',
            height: '28px',
            borderRadius: 'var(--radius-md)',
            background: 'var(--brand-navy-900)',
            color: 'var(--accent-gold-400)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Loader2 size={16} className="spin-anim" />
          </div>
          <div>
            <div style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              Processing Query with AI Engine
            </div>
            {question && (
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', maxWidth: '420px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                "{question}"
              </div>
            )}
          </div>
        </div>

        <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--accent-gold-700)', background: 'var(--accent-gold-50)', padding: '0.2rem 0.6rem', borderRadius: 'var(--radius-full)', border: '1px solid var(--accent-gold-100)' }}>
          {(elapsedMs / 1000).toFixed(1)}s elapsed
        </div>
      </div>

      {/* Progressive Step List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.625rem' }}>
        {STEPS.map((step, idx) => {
          const isDone = idx < currentStep;
          const isCurrent = idx === currentStep;
          const isPending = idx > currentStep;
          const StepIcon = step.icon;

          return (
            <div
              key={step.id}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                padding: '0.45rem 0.75rem',
                borderRadius: 'var(--radius-md)',
                background: isCurrent ? 'var(--bg-surface-subtle)' : 'transparent',
                border: isCurrent ? '1px solid var(--border-strong)' : '1px solid transparent',
                transition: 'all 0.2s ease',
                opacity: isPending ? 0.45 : 1
              }}
            >
              <div style={{
                width: '20px',
                height: '20px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0
              }}>
                {isDone ? (
                  <CheckCircle2 size={16} style={{ color: '#10B981' }} />
                ) : isCurrent ? (
                  <Loader2 size={15} className="spin-anim" style={{ color: '#D97706' }} />
                ) : (
                  <StepIcon size={14} style={{ color: '#94A3B8' }} />
                )}
              </div>

              <span style={{
                fontSize: '0.8125rem',
                fontWeight: isCurrent ? 600 : 500,
                color: isCurrent ? 'var(--text-primary)' : isDone ? 'var(--text-secondary)' : 'var(--text-muted)'
              }}>
                {step.label}
              </span>
            </div>
          );
        })}
      </div>

      {/* Micro progress bar */}
      <div style={{ height: '3px', background: 'var(--border-color)', borderRadius: '2px', overflow: 'hidden' }}>
        <div
          style={{
            height: '100%',
            background: 'linear-gradient(90deg, #F59E0B, #10B981)',
            width: `${((currentStep + 1) / STEPS.length) * 100}%`,
            transition: 'width 0.4s ease'
          }}
        />
      </div>
    </div>
  );
};

export default StepProgressLoader;
