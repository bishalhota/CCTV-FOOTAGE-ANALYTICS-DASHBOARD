import React from 'react';

/**
 * Application top bar: system health indicator and user controls.
 */
export const Topbar: React.FC = () => (
  <header className="topbar">
    <div className="system-health">
      <div className="pulse-indicator healthy" />
      <span className="health-text">
        Systems Operational · Redis ✓ · PostgreSQL ✓ · Edge Node ✓
      </span>
    </div>
    <div className="user-controls">
      <button className="icon-btn" id="btn-refresh" title="Refresh data" aria-label="Refresh data">
        🔄
      </button>
      <button
        className="icon-btn"
        id="btn-notifications"
        title="Notifications"
        aria-label="Notifications"
      >
        🔔
      </button>
      <div className="avatar-circle" title="Principal Engineer">
        PE
      </div>
    </div>
  </header>
);
