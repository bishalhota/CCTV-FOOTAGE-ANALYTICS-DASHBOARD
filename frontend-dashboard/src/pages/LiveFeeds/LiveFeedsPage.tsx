import React from 'react';
import { PageHeader } from '../../components/layout';
import { CameraFeedCard, EventLog } from '../../components/cameras';
import { useEventStream, useCameraTracking } from '../../hooks';
import type { Store } from '../../types';

interface LiveFeedsPageProps {
  store: Store;
}

/**
 * Live Feeds page — real-time CCTV feed simulation with detection overlays,
 * pipeline status tracking, and domain event log driven by SSE.
 */
const LiveFeedsPage: React.FC<LiveFeedsPageProps> = ({ store }) => {
  const { events, cameraStatuses, liveDetections } = useEventStream(store.id);
  const { cameras, completedCameras, processingCamera } = useCameraTracking(
    store.cameras,
    cameraStatuses,
    store.id
  );

  return (
    <div className="page-fade-in" id="live-feeds-page">
      <PageHeader
        title="Store Cam processing"
      />

      <div className="feeds-grid">
        {cameras.map((cam) => (
          <CameraFeedCard
            key={cam.key}
            camKey={cam.key}
            name={cam.name}
            fps={cam.fps}
            cameraStatus={cameraStatuses[cam.key] ?? { status: 'IDLE', progress: 0 }}
            trackCount={liveDetections[cam.key]?.length ?? 0}
            detections={liveDetections[cam.key] ?? []}
          />
        ))}
      </div>

      <EventLog
        events={events}
        processingCamera={processingCamera}
        completedCameras={completedCameras}
        totalCameras={cameras.length}
      />
    </div>
  );
};

export default LiveFeedsPage;
