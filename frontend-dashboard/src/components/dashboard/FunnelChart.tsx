import React from 'react';
import { Skeleton } from '../ui';
import { FUNNEL_COLORS } from '../../constants';
import type { FunnelData } from '../../types';

interface FunnelChartProps {
  data: FunnelData | null;
  loading: boolean;
}

/**
 * Horizontal bar funnel chart with drop-off labels.
 */
export const FunnelChart: React.FC<FunnelChartProps> = ({ data, loading }) => {
  const funnelMax = data?.steps?.[0]?.visitor_count || 1;

  return (
    <div className="chart-card frosted-glass" id="funnel-chart">
      <h3>
        Conversion Funnel
        <span className="text-muted" style={{ fontSize: '0.75rem', fontWeight: 400 }}>
          Last 24h
        </span>
      </h3>

      {loading ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} height="48px" />
          ))}
        </div>
      ) : (
        <div className="funnel-chart">
          {data?.steps?.map((step, i) => (
            <div className="funnel-step" key={step.step_name}>
              <div className="funnel-step-header">
                <span className="funnel-step-name">{step.step_name}</span>
                <span className="funnel-step-count">
                  {step.visitor_count.toLocaleString()}
                </span>
              </div>
              <div className="funnel-bar-bg">
                <div
                  className="funnel-bar-fill"
                  style={{
                    width: `${(step.visitor_count / funnelMax) * 100}%`,
                    background: FUNNEL_COLORS[i],
                  }}
                />
              </div>
              {step.conversion_rate_from_previous !== null &&
                step.conversion_rate_from_previous !== undefined && (
                  <div className="funnel-drop">
                    ↓ {(100 - step.conversion_rate_from_previous).toFixed(1)}% drop-off
                  </div>
                )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
