export const ZONE_TYPE_COLORS: Record<string, { bg: string; color: string; label: string }> = {
  QUEUE:      { bg: 'rgba(245,158,11,0.12)', color: '#f59e0b', label: 'Queue' },
  DISPLAY:    { bg: 'rgba(99,102,241,0.12)', color: '#6366f1', label: 'Display' },
  AISLE:      { bg: 'rgba(6,182,212,0.12)',  color: '#06b6d4', label: 'Aisle' },
  ENTRY_LINE: { bg: 'rgba(16,185,129,0.12)', color: '#10b981', label: 'Entry' },
};

export const FUNNEL_COLORS = ['#6366f1', '#8b5cf6', '#f59e0b'] as const;

export const ANOMALY_META: Record<string, { icon: string; title: string }> = {
  QUEUE_SPIKE:      { icon: '🚨', title: 'Queue Spike Detected' },
  DEAD_CAMERA:      { icon: '📹', title: 'Dead Camera Feed' },
  CONVERSION_DROP:  { icon: '📉', title: 'Conversion Rate Drop' },
  HIGH_ABANDONMENT: { icon: '⚠️', title: 'High Queue Abandonment' },
};
