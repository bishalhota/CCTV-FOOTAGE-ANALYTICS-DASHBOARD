import React from 'react';
import { getHeatColor, getZoneTypeMeta, inferZoneType } from '../../utils';
import { ZONE_TYPE_COLORS } from '../../constants';
import type { ZoneHeatmapData } from '../../types';

interface HeatmapCardProps {
  zone: ZoneHeatmapData;
}

/**
 * Individual zone heatmap card showing dwell density, visitor count,
 * a heat bar, and a zone-type badge with inferred type colouring.
 */
export const HeatmapCard: React.FC<HeatmapCardProps> = ({ zone }) => {
  const zType     = inferZoneType(zone.zone_name);
  const meta      = getZoneTypeMeta(zType);
  const heatColor = getHeatColor(zone.dwell_time_density);

  return (
    <div
      className="heatmap-zone-card frosted-glass"
      id={`zone-${zone.zone_id}`}
      style={{ borderColor: `${meta.color}30`, background: meta.bg }}
    >
      <span
        className="zone-type-badge"
        style={{ background: `${meta.color}20`, color: meta.color }}
      >
        {meta.label}
      </span>
      <div className="zone-name">{zone.zone_name}</div>
      <div className="zone-density-label" style={{ color: heatColor }}>
        {(zone.dwell_time_density * 100).toFixed(0)}%
      </div>
      <div className="zone-visitors-label">{zone.unique_visitors} unique visitors</div>
      <div className="zone-heat-bar">
        <div
          className="zone-heat-fill"
          style={{ width: `${zone.dwell_time_density * 100}%`, background: heatColor }}
        />
      </div>
    </div>
  );
};

/**
 * Colour legend for zone types displayed above the heatmap grid.
 */
export const HeatmapLegend: React.FC = () => (
  <div style={{ display: 'flex', gap: 20, marginBottom: 8, flexWrap: 'wrap' }}>
    {Object.entries(ZONE_TYPE_COLORS).map(([type, meta]) => (
      <div
        key={type}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          fontSize: '0.75rem',
          color: 'var(--color-text-muted)',
        }}
      >
        <div
          style={{ width: 10, height: 10, borderRadius: 3, background: meta.color, opacity: 0.8 }}
        />
        {meta.label}
      </div>
    ))}
  </div>
);
