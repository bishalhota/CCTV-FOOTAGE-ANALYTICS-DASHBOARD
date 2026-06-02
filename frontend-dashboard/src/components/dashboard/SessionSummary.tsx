import React from 'react';
import { Skeleton } from '../ui';
import type { DashboardMetrics } from '../../types';

interface SessionSummaryProps {
  metrics: DashboardMetrics | null;
  loading: boolean;
}

interface SummaryItem {
  label: string;
  value: number | string;
  icon: string;
}

/**
 * Quick-stats panel showing total exits, currently in-store count,
 * and queue conversion rate.
 */
export const SessionSummary: React.FC<SessionSummaryProps> = ({ metrics, loading }) => {
  const items: SummaryItem[] = [
    {
      label: 'Total Exits',
      value: metrics?.total_exits ?? metrics?.footfall ?? 0,
      icon: '🚶',
    },
    {
      label: 'Currently In Store',
      value: metrics?.active_visitor_count ?? metrics?.uniqueVisitors ?? 0,
      icon: '📍',
    },
    {
      label: 'Queue Conversion',
      value: metrics ? `${(metrics.conversionRate ?? 0).toFixed(1)}%` : '—',
      icon: '🎯',
    },
  ];

  return (
    <div className="chart-card frosted-glass" id="quick-stats">
      <h3>Session Summary</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        {items.map((item) => (
          <div
            key={item.label}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '12px 16px',
              background: 'rgba(255,255,255,0.03)',
              borderRadius: 8,
              border: '1px solid var(--color-border)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <span style={{ fontSize: '1.1rem' }}>{item.icon}</span>
              <span style={{ fontSize: '0.82rem', color: 'var(--color-text-secondary)' }}>
                {item.label}
              </span>
            </div>
            {loading ? (
              <Skeleton width="48px" height="20px" />
            ) : (
              <span style={{ fontWeight: 700, fontSize: '1rem' }}>
                {typeof item.value === 'number' ? item.value.toLocaleString() : item.value}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
