import React from 'react';
import { Skeleton } from '../ui';

interface MetricCardProps {
  id: string;
  icon: string;
  title: string;
  value: string;
  positive?: boolean;
  delta?: string;
  loading?: boolean;
  warning?: boolean;
}

/**
 * A single KPI metric card with optional loading skeleton,
 * success highlight, and warning state.
 */
export const MetricCard: React.FC<MetricCardProps> = ({
  id,
  icon,
  title,
  value,
  positive,
  delta,
  loading,
  warning,
}) => (
  <div
    className={`metric-card frosted-glass ${warning ? 'warning' : positive ? 'success-card' : ''}`}
    id={id}
  >
    <span className="metric-card-icon">{icon}</span>
    <h3>{title}</h3>
    {loading ? (
      <Skeleton height="36px" width="60%" />
    ) : (
      <>
        <div
          className={`metric-value ${positive ? 'positive' : ''} ${warning ? 'text-warning' : ''}`}
        >
          {value}
        </div>
        {delta && <div className="metric-delta">↑ {delta}</div>}
      </>
    )}
  </div>
);
