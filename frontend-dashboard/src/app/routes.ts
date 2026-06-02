/**
 * Route configuration for the application.
 * Each entry maps a route ID to its metadata.
 */
export interface RouteConfig {
  id: string;
  icon: string;
  label: string;
}

export const ROUTES: RouteConfig[] = [
  { id: 'overview',  icon: '📊', label: 'Overview' },
  { id: 'cameras',   icon: '🎥', label: 'Live Feeds' },
  { id: 'heatmaps',  icon: '🔥', label: 'Zone Heatmaps' },
  { id: 'anomalies', icon: '⚠️', label: 'Anomalies' },
] as const;

export type RouteId = typeof ROUTES[number]['id'];
