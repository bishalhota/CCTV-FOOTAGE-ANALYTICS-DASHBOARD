import os
import logging
import time
from src.pipeline import VisionPipeline

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("edge-node.main")

def main():
    logger.info("Starting Edge Node Service...")
    
    redis_uri = os.getenv("REDIS_URI", "redis://redis:6379/0")
    store_id = os.getenv("STORE_ID", "a1b2c3d4-0001-4000-8000-000000000001")
    
    # Support two modes:
    # 1. Single camera mode (original) via CAMERA_ID + VIDEO_PATH env vars
    # 2. Sequential multi-camera mode via CAMERA_LIST env var (comma-separated cam_id:video_path pairs)
    camera_list_env = os.getenv("CAMERA_LIST", "")
    
    if camera_list_env:
        # Sequential mode: process multiple cameras one by one
        pairs = [p.strip() for p in camera_list_env.split(",") if p.strip()]
        cameras = []
        for pair in pairs:
            parts = pair.split(":", 1)
            if len(parts) == 2:
                cameras.append((parts[0].strip(), parts[1].strip()))
            else:
                logger.warning(f"Invalid camera pair format: {pair}. Expected 'cam_id:/path/to/video'")
        
        logger.info(f"Sequential processing mode: {len(cameras)} cameras to process")
        
        while True:
            for i, (camera_id, video_path) in enumerate(cameras):
                logger.info(f"=== Processing Camera {i+1}/{len(cameras)}: {camera_id} ===")
                
                pipeline = VisionPipeline(
                    store_id=store_id,
                    camera_id=camera_id,
                    video_source=video_path,
                    redis_uri=redis_uri
                )
                
                success = pipeline.run()
                
                if success:
                    logger.info(f"Camera {camera_id} completed successfully.")
                else:
                    logger.error(f"Camera {camera_id} failed.")
                
                # Brief pause between cameras to let the ReID service catch up
                logger.info("Pausing 5 seconds before next camera...")
                time.sleep(5)
            
            logger.info("=== Finished one full cycle. Restarting camera loop. ===")
    else:
        # Single camera mode (backward compatible)
        camera_id = os.getenv("CAMERA_ID", "cam-1")
        video_path = os.getenv("VIDEO_PATH", "")
        rtsp_url = os.getenv("RTSP_URL", "")
        
        source = video_path if video_path else rtsp_url
        if not source:
            logger.critical("No VIDEO_PATH or RTSP_URL provided!")
            return
        
        pipeline = VisionPipeline(
            store_id=store_id,
            camera_id=camera_id,
            video_source=source,
            redis_uri=redis_uri
        )
        
        pipeline.run()

if __name__ == "__main__":
    main()
