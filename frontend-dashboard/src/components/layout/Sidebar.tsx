import React from 'react';
import { STORES } from '../../constants';
import type { Store } from '../../types';

interface NavItem {
  id: string;
  icon: string;
  label: string;
}

const NAV_ITEMS: NavItem[] = [
  { id: 'overview',  icon: '📊', label: 'Overview' },
  { id: 'cameras',   icon: '🎥', label: 'Live Feeds' },
  { id: 'heatmaps',  icon: '🔥', label: 'Zone Heatmaps' },
  { id: 'anomalies', icon: '⚠️', label: 'Anomalies' },
];

interface SidebarProps {
  activeRoute: string;
  onNavigate: (route: string) => void;
  selectedStoreId: string;
  onStoreChange: (storeId: string) => void;
  selectedStore: Store;
}

/**
 * Application sidebar: brand, store selector, nav menu, status footer.
 */
export const Sidebar: React.FC<SidebarProps> = ({
  activeRoute,
  onNavigate,
  selectedStoreId,
  onStoreChange,
  selectedStore,
}) => (
  <aside className="sidebar frosted-glass">
    {/* Brand */}
    <div className="brand-header">
      <div className="brand-logo-glow" />
      <h1 className="brand-text">Store Intel</h1>
    </div>

    {/* Store Selector */}
    <div className="store-selector-widget">
      <label>Active Store</label>
      <select
        id="store-selector"
        className="premium-select"
        value={selectedStoreId}
        onChange={(e) => onStoreChange(e.target.value)}
      >
        {STORES.map((s) => (
          <option key={s.id} value={s.id}>
            {s.name}
          </option>
        ))}
      </select>
      <div style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)', marginTop: 4 }}>
        📍 {selectedStore.location} · {selectedStore.cameras} cams
      </div>
    </div>

    {/* Navigation */}
    <nav className="nav-menu" aria-label="Main navigation">
      <div className="nav-section-label">Analytics</div>
      {NAV_ITEMS.map((item) => (
        <button
          key={item.id}
          id={`nav-${item.id}`}
          className={`nav-button ${activeRoute === item.id ? 'active' : ''}`}
          onClick={() => onNavigate(item.id)}
          aria-current={activeRoute === item.id ? 'page' : undefined}
        >
          <span className="icon">{item.icon}</span>
          {item.label}
        </button>
      ))}
    </nav>

    {/* Footer */}
    <div className="sidebar-footer">
      <div className="sidebar-badge">
        <div className="pulse-indicator healthy" />
        Pipeline Active
      </div>
    </div>
  </aside>
);
