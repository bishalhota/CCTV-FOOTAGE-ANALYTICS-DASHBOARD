import React, { useState } from 'react';
import './styles/index.css';

import { Sidebar, Topbar } from './components/layout';
import { STORES } from './constants';
import { ROUTES } from './app/routes';
import type { RouteId } from './app/routes';

// Page-level lazy imports kept as direct imports (no bundler code-split needed for
// this app size; swap to React.lazy if the bundle grows).
import OverviewPage  from './pages/Overview/OverviewPage';
import LiveFeedsPage from './pages/LiveFeeds/LiveFeedsPage';
import HeatmapsPage  from './pages/Heatmaps/HeatmapsPage';
import AnomaliesPage from './pages/Anomalies/AnomaliesPage';

// Validate route id at compile time
const DEFAULT_ROUTE: RouteId = ROUTES[0].id as RouteId;

/**
 * Application root.
 *
 * Responsibilities:
 *  - owns routing state (activeRoute)
 *  - owns store-selection state (selectedStoreId)
 *  - renders the two-panel shell (Sidebar + main)
 *  - delegates page rendering to the appropriate page component
 */
const App: React.FC = () => {
  const [activeRoute, setActiveRoute]       = useState<RouteId>(DEFAULT_ROUTE);
  const [selectedStoreId, setSelectedStoreId] = useState<string>(STORES[0].id);

  const selectedStore = STORES.find((s) => s.id === selectedStoreId) ?? STORES[0];

  return (
    <div className="app-wrapper theme-dark premium-glass-bg">
      <Sidebar
        activeRoute={activeRoute}
        onNavigate={(route) => setActiveRoute(route as RouteId)}
        selectedStoreId={selectedStoreId}
        onStoreChange={setSelectedStoreId}
        selectedStore={selectedStore}
      />

      <main className="main-content">
        <Topbar />

        <div className="viewport-scroll-area">
          {activeRoute === 'overview' && (
            <OverviewPage storeId={selectedStore.id} storeName={selectedStore.name} />
          )}
          {activeRoute === 'cameras' && (
            <LiveFeedsPage store={selectedStore} />
          )}
          {activeRoute === 'heatmaps' && (
            <HeatmapsPage storeId={selectedStore.id} storeName={selectedStore.name} />
          )}
          {activeRoute === 'anomalies' && (
            <AnomaliesPage storeId={selectedStore.id} storeName={selectedStore.name} />
          )}
        </div>
      </main>
    </div>
  );
};

export default App;
