import logging
import time
import json
import cv2
import numpy as np
import redis
import torch
import torchvision.transforms as transforms
import torchvision.models as models
from ultralytics import YOLO

logger = logging.getLogger("edge-node.pipeline")

class TelemetryClient:
    def __init__(self, redis_uri: str):
        self.client = redis.from_url(redis_uri)
        self.stream_name = "telemetry_raw"
        
    def publish(self, payload: dict):
        try:
            redis_payload = {
                "store_id": payload["store_id"],
                "camera_id": payload["camera_id"],
                "track_id": str(payload["track_id"]),
                "bbox": json.dumps(payload["bbox"]),
                "frame_width": str(payload["frame_width"]),
                "frame_height": str(payload["frame_height"]),
                "embedding": json.dumps(payload["embedding"]) if payload["embedding"] else "",
                "quality_score": str(payload["quality_score"]),
                "timestamp": str(payload["timestamp"]),
                "video_timestamp": str(payload.get("video_timestamp", 0.0))
            }
            self.client.xadd(self.stream_name, redis_payload)
            logger.debug(f"Published telemetry for track_id {payload['track_id']}")
        except Exception as e:
            logger.error(f"Failed to publish telemetry: {e}")

    def publish_status(self, store_id: str, camera_id: str, status: str, progress: float = 0.0):
        """Publish processing status for dashboard monitoring."""
        try:
            status_payload = {
                "store_id": store_id,
                "camera_id": camera_id,
                "status": status,
                "progress": str(progress),
                "timestamp": str(time.time())
            }
            self.client.publish("pipeline_status", json.dumps(status_payload))
        except Exception as e:
            logger.error(f"Failed to publish status: {e}")

class ReIDExtractor:
    def __init__(self):
        logger.info("Loading ResNet18 Extractor...")
        self.device = torch.device("cpu")
        import os
        os.environ['TORCH_HOME'] = '/tmp'
        
        self.model = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
        self.model.fc = torch.nn.Identity()
        self.model.to(self.device)
        self.model.eval()
        
        self.transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((256, 128)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        
    def extract(self, crop: np.ndarray) -> np.ndarray:
        crop_rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
        tensor = self.transform(crop_rgb).unsqueeze(0).to(self.device)
        with torch.no_grad():
            embedding = self.model(tensor).squeeze().cpu().numpy()
            
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        return embedding

class VisionPipeline:
    def __init__(self, store_id: str, camera_id: str, video_source: str, redis_uri: str):
        self.store_id = store_id
        self.camera_id = camera_id
        self.video_source = video_source
        
        logger.info("Initializing Vision Pipeline dependencies...")
        self.telemetry_client = TelemetryClient(redis_uri)
        self.extractor = ReIDExtractor()
        
        logger.info("Loading YOLOv8n...")
        self.detector = YOLO("yolov8n.pt")
        
        # 2 FPS processing to keep CPU usage manageable
        self.target_fps = 2
        self.frame_interval = 1.0 / self.target_fps
        self.last_process_time = 0.0
        
        # Track-specific cache: track_id -> last_seen_timestamp
        self.extracted_tracks = {}

    def run(self):
        """Process a video file from start to finish (non-looping)."""
        logger.info(f"Starting video processing for Camera: {self.camera_id} @ {self.video_source}")
        
        cap = cv2.VideoCapture(self.video_source)
        if not cap.isOpened():
            logger.critical(f"Failed to open video: {self.video_source}")
            self.telemetry_client.publish_status(self.store_id, self.camera_id, "ERROR")
            return False

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        video_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        frame_skip = max(1, int(video_fps / self.target_fps))
        
        logger.info(f"Video Info: {total_frames} frames at {video_fps:.1f} FPS. Sampling every {frame_skip} frames ({self.target_fps} FPS effective)")
        
        self.telemetry_client.publish_status(self.store_id, self.camera_id, "PROCESSING", 0.0)
        
        frame_count = 0
        processed_count = 0
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    logger.info(f"Video {self.camera_id} processing complete. Processed {processed_count} frames out of {frame_count} total.")
                    break

                frame_count += 1
                
                # Skip frames to achieve target FPS
                if frame_count % frame_skip != 0:
                    continue
                
                current_time = time.time()
                video_timestamp = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
                self.process_frame(frame, current_time, video_timestamp)
                processed_count += 1
                
                # Report progress every 50 processed frames
                if processed_count % 50 == 0:
                    progress = (frame_count / total_frames) * 100.0 if total_frames > 0 else 0
                    logger.info(f"[{self.camera_id}] Progress: {progress:.1f}% ({processed_count} frames processed)")
                    self.telemetry_client.publish_status(self.store_id, self.camera_id, "PROCESSING", progress)
                
                # Brief sleep to throttle CPU
                elapsed = time.time() - current_time
                sleep_time = max(0, (1.0 / self.target_fps) - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
        except KeyboardInterrupt:
            logger.info("Termination requested.")
        finally:
            cap.release()
        
        self.telemetry_client.publish_status(self.store_id, self.camera_id, "COMPLETE", 100.0)
        return True

    def process_frame(self, frame: np.ndarray, timestamp: float, video_timestamp: float = 0.0):
        # Run YOLO with built-in ByteTrack
        results = self.detector.track(frame, tracker="bytetrack.yaml", persist=True, classes=[0], verbose=False)
        
        if len(results) == 0 or results[0].boxes is None or results[0].boxes.id is None:
            return
            
        boxes = results[0].boxes.xyxy.cpu().numpy()
        track_ids = results[0].boxes.id.cpu().numpy()
        
        # Clean up stale track cache entries older than 15 seconds
        for tid, t_last in list(self.extracted_tracks.items()):
            if timestamp - t_last > 15.0:
                self.extracted_tracks.pop(tid, None)
        
        for i in range(len(boxes)):
            x1, y1, x2, y2 = map(int, boxes[i])
            track_id = int(track_ids[i])
            
            h, w = frame.shape[:2]
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)
            
            # Check if we already have an active resolved embedding for this track
            if track_id in self.extracted_tracks:
                embedding = None
                quality_score = 0.0
                self.extracted_tracks[track_id] = timestamp
            else:
                crop = frame[y1:y2, x1:x2]
                if crop.shape[0] < 128 or crop.shape[1] < 64:
                    embedding = None
                    quality_score = 0.0
                else:
                    embedding = self.extractor.extract(crop)
                    quality_score = min(1.0, (crop.shape[0] * crop.shape[1]) / (256 * 128))
                    if quality_score > 0.4:
                        self.extracted_tracks[track_id] = timestamp

            telemetry_payload = {
                "store_id": self.store_id,
                "camera_id": self.camera_id,
                "track_id": track_id,
                "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                "frame_width": w,
                "frame_height": h,
                "embedding": embedding.tolist() if embedding is not None else None,
                "quality_score": quality_score,
                "timestamp": timestamp,
                "video_timestamp": video_timestamp
            }
            
            self.telemetry_client.publish(telemetry_payload)
