import os
import cv2
import numpy as np
from typing import Dict, Any, List, Optional
from pathlib import Path

class FaceTracker:
    """
    Intelligent subject positioning and multi-layout crop analyzer:
    1. center_zoom: 0.96:1 Center-Region Zoom Crop with Blurred Background
    2. smart_crop: Full-frame 9:16 vertical smart crop with face tracking
    3. split_screen: 50/50 Dual Stack (top gameplay + bottom facecam)
    4. blurred_bg: Classic 16:9 on full blurred background canvas
    5. auto: AI auto-selection based on detected content
    """

    def __init__(self):
        cascade_dir = cv2.data.haarcascades
        self.frontal_cascade = cv2.CascadeClassifier(os.path.join(cascade_dir, 'haarcascade_frontalface_default.xml'))
        self.profile_cascade = cv2.CascadeClassifier(os.path.join(cascade_dir, 'haarcascade_profileface.xml'))

    def analyze_clip_visuals(
        self,
        video_path: Path,
        start_time: float,
        end_time: float,
        user_crop_mode: str = "center_zoom"
    ) -> Dict[str, Any]:
        """
        Samples keyframes across the clip duration to analyze faces, streamer webcams,
        and gameplay action to calculate exact crop coordinates for the requested layout.
        """
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            return {
                "layout": "center_zoom_blurred_bg",
                "crop_width": 1036,
                "crop_height": 1080,
                "crop_x": 442,
                "crop_aspect_ratio": 0.96,
                "face_detected": False,
                "face_y_ratio": 0.5,
                "has_bottom_facecam": False,
                "orig_width": 1920,
                "orig_height": 1080
            }

        orig_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 1920)
        orig_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 1080)

        duration = end_time - start_time
        step = max(2.0, duration / 12.0)
        sample_times = np.arange(start_time, end_time, step)

        face_samples = []
        streamer_faces = []

        for t in sample_times:
            cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000.0)
            ret, frame = cap.read()
            if not ret or frame is None:
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.frontal_cascade.detectMultiScale(
                gray, scaleFactor=1.15, minNeighbors=4, minSize=(50, 50)
            )

            if len(faces) == 0:
                faces = self.profile_cascade.detectMultiScale(
                    gray, scaleFactor=1.15, minNeighbors=3, minSize=(50, 50)
                )

            if len(faces) > 0:
                # Detect streamer facecam overlay (lower region y > 0.35 * H, x < 0.65 * W)
                cam_faces = [f for f in faces if f[1] > (orig_height * 0.35) and f[0] < (orig_width * 0.65)]
                if cam_faces:
                    dominant = max(cam_faces, key=lambda f: f[2] * f[3])
                    streamer_faces.append(dominant)
                else:
                    dominant = max(faces, key=lambda f: f[2] * f[3])

                fx, fy, fw, fh = dominant
                face_samples.append({
                    "time": t,
                    "center_x": fx + (fw / 2.0),
                    "center_y": fy + (fh / 2.0),
                    "x": fx,
                    "y": fy,
                    "w": fw,
                    "h": fh
                })

        cap.release()

        has_bottom_facecam = len(streamer_faces) >= 2
        avg_face_y = float(np.mean([f["center_y"] for f in face_samples])) / orig_height if face_samples else 0.5

        # Resolve mode
        mode = user_crop_mode.lower()
        if mode in ["auto", ""]:
            if has_bottom_facecam:
                mode = "center_zoom"
            elif len(face_samples) > 0:
                mode = "smart_crop"
            else:
                mode = "center_zoom"

        # 1. Full-frame 9:16 Smart Face Crop
        if mode == "smart_crop":
            crop_width = int(round(orig_height * 9.0 / 16.0))
            crop_width = crop_width if crop_width % 2 == 0 else crop_width + 1  # 608px
            max_x = max(0, orig_width - crop_width)

            if face_samples:
                med_cx = float(np.median([f["center_x"] for f in face_samples]))
                target_x = int(round(med_cx - (crop_width / 2.0)))
            else:
                target_x = max_x // 2

            target_x = max(0, min(int(target_x), int(max_x)))
            target_x = target_x if target_x % 2 == 0 else target_x - 1

            return {
                "layout": "smart_crop",
                "crop_width": int(crop_width),
                "crop_height": int(orig_height),
                "crop_x": int(target_x),
                "crop_aspect_ratio": round(float(crop_width) / float(orig_height), 2),
                "face_detected": len(face_samples) > 0,
                "face_y_ratio": round(float(avg_face_y), 2),
                "has_bottom_facecam": has_bottom_facecam,
                "orig_width": orig_width,
                "orig_height": orig_height
            }

        # 2. Split Screen Dual Stack (50/50 Top & Bottom)
        elif mode == "split_screen":
            # Top crop (gameplay / action center)
            top_w = 960
            top_h = 540
            top_x = int(round((orig_width - top_w) / 2.0))
            top_y = 60

            # Bottom crop (streamer facecam / speaker)
            bot_w = 540
            bot_h = 540
            if streamer_faces:
                med_cx = float(np.median([f[0] + f[2] / 2.0 for f in streamer_faces]))
                med_cy = float(np.median([f[1] + f[3] / 2.0 for f in streamer_faces]))
                bot_x = int(round(med_cx - bot_w / 2.0))
                bot_y = int(round(med_cy - bot_h / 2.0))
            elif face_samples:
                med_cx = float(np.median([f["center_x"] for f in face_samples]))
                med_cy = float(np.median([f["center_y"] for f in face_samples]))
                bot_x = int(round(med_cx - bot_w / 2.0))
                bot_y = int(round(med_cy - bot_h / 2.0))
            else:
                bot_x = int(round((orig_width - bot_w) / 2.0))
                bot_y = orig_height - bot_h

            # Clamping
            top_x = max(0, min(top_x, orig_width - top_w))
            top_y = max(0, min(top_y, orig_height - top_h))
            bot_x = max(0, min(bot_x, orig_width - bot_w))
            bot_y = max(0, min(bot_y, orig_height - bot_h))

            return {
                "layout": "split_screen",
                "top_crop": {"x": int(top_x), "y": int(top_y), "w": int(top_w), "h": int(top_h)},
                "bot_crop": {"x": int(bot_x), "y": int(bot_y), "w": int(bot_w), "h": int(bot_h)},
                "crop_aspect_ratio": 0.56,
                "face_detected": len(face_samples) > 0,
                "face_y_ratio": round(float(avg_face_y), 2),
                "has_bottom_facecam": has_bottom_facecam,
                "orig_width": orig_width,
                "orig_height": orig_height
            }

        # 3. Classic 16:9 Letterbox on Blurred Canvas
        elif mode == "blurred_bg":
            return {
                "layout": "blurred_bg",
                "crop_width": orig_width,
                "crop_height": orig_height,
                "crop_x": 0,
                "crop_aspect_ratio": round(float(orig_width) / float(orig_height), 2),
                "face_detected": len(face_samples) > 0,
                "face_y_ratio": round(float(avg_face_y), 2),
                "has_bottom_facecam": has_bottom_facecam,
                "orig_width": orig_width,
                "orig_height": orig_height
            }

        # 4. Default: Center-Region Zoom Crop with Blurred Background (~0.96:1)
        else:
            crop_width = int(round(orig_height * 0.96))
            crop_width = crop_width if crop_width % 2 == 0 else crop_width + 1  # 1036px for 1080p
            max_x = max(0, orig_width - crop_width)
            default_center_x = max_x // 2

            if streamer_faces:
                min_cam_left = min(f[0] for f in streamer_faces)
                target_x = min_cam_left - 70
                target_x = max(0, min(target_x, default_center_x))
            elif face_samples:
                med_cx = float(np.median([f["center_x"] for f in face_samples]))
                target_x = int(round(med_cx - (crop_width / 2.0)))
            else:
                target_x = default_center_x

            target_x = max(0, min(int(target_x), int(max_x)))
            target_x = target_x if target_x % 2 == 0 else target_x - 1

            return {
                "layout": "center_zoom_blurred_bg",
                "crop_width": int(crop_width),
                "crop_height": int(orig_height),
                "crop_x": int(target_x),
                "crop_aspect_ratio": round(float(crop_width) / float(orig_height), 2),
                "face_detected": len(face_samples) > 0,
                "face_y_ratio": round(float(avg_face_y), 2),
                "has_bottom_facecam": has_bottom_facecam,
                "orig_width": orig_width,
                "orig_height": orig_height
            }
