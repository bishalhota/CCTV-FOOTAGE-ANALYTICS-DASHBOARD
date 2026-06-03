import { useMemo } from 'react';
import type { CameraStatus } from '../types';

interface Camera {
  key: string;
  name: string;
  fps: number;
}

interface UseCameraTrackingResult {
  cameras: Camera[];
  completedCameras: number;
  processingCamera: [string, CameraStatus] | undefined;
}

/**
 * Derives the ordered camera list for a store and computes aggregate
 * pipeline status helpers (completedCameras, processingCamera) from
 * the raw cameraStatuses map.
 *
 * @param totalCameras  - Number of cameras configured for the store.
 * @param cameraStatuses - Live status map keyed by camera ID.
 */
export function useCameraTracking(
  totalCameras: number,
  cameraStatuses: Record<string, CameraStatus>,
  storeId?: string
): UseCameraTrackingResult {
  const cameras: Camera[] = useMemo(() => {
    // Dynamically set camera names based on Store ID
    if (storeId === 'a1b2c3d4-0002-4000-8000-000000000002') {
      return [
        { key: 'cam-1', name: 'Entry 1', fps: 2 },
        { key: 'cam-2', name: 'Entry 2', fps: 2 },
        { key: 'cam-3', name: 'Zone Area', fps: 2 },
        { key: 'cam-4', name: 'Billing Area', fps: 2 },
      ].slice(0, totalCameras);
    }
    
    // Default / Store 1
    return [
      { key: 'cam-1', name: 'Entrance Left',   fps: 2 },
      { key: 'cam-2', name: 'Entrance Right',  fps: 2 },
      { key: 'cam-3', name: 'Outside Area',    fps: 2 },
      { key: 'cam-4', name: 'Storage Room',    fps: 2 },
      { key: 'cam-5', name: 'Billing Counter', fps: 2 },
    ].slice(0, totalCameras);
  }, [totalCameras, storeId]);

  const completedCameras = useMemo(
    () => Object.values(cameraStatuses).filter((s) => s.status === 'COMPLETE').length,
    [cameraStatuses]
  );

  const processingCamera = useMemo(
    () =>
      Object.entries(cameraStatuses).find(
        ([, s]) => s.status === 'PROCESSING'
      ) as [string, CameraStatus] | undefined,
    [cameraStatuses]
  );

  return { cameras, completedCameras, processingCamera };
}
