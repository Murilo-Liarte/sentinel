"""
emotion_detector.py — Sentinel
================================
Lightweight, ultra-fast facial emotion analysis using ONNX Runtime via OpenCV DNN.

Model: emotion-ferplus-8.onnx (Microsoft FER+ ResNet architecture, ~33 MB).
Runs entirely offline via cv2.dnn in ~2 ms on CPU with zero heavy dependencies
(no TensorFlow, no PyTorch, no Keras).

Emotions detected:
    Neutral, Happy, Surprised, Sad, Angry, Disgusted, Fearful, Contempt
"""

import logging
import os
from typing import Optional, Tuple

import cv2
import numpy as np

from app_paths import get_resource

logger = logging.getLogger(__name__)

# Emotion classes from Microsoft FER+ dataset
EMOTIONS = [
    "Neutral",
    "Happy",
    "Surprised",
    "Sad",
    "Angry",
    "Disgusted",
    "Fearful",
    "Contempt",
]


class EmotionDetector:
    """
    OpenCV DNN-based emotion detector using emotion-ferplus-8.onnx.
    Initializes lazily on first call and executes in ~2ms on CPU.
    """

    def __init__(self, model_rel_path: str = "models/emotion-ferplus-8.onnx") -> None:
        self.model_path = get_resource(model_rel_path)
        self._net: Optional[cv2.dnn.Net] = None
        self._available = True

    def _load(self) -> bool:
        if self._net is not None:
            return True
        if not self._available:
            return False

        if not os.path.exists(self.model_path):
            logger.warning("Emotion model not found at %s", self.model_path)
            self._available = False
            return False

        try:
            self._net = cv2.dnn.readNetFromONNX(self.model_path)
            # Prefer fast CPU inference
            self._net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
            self._net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
            logger.info("Emotion ONNX model loaded successfully from %s", self.model_path)
            return True
        except Exception as exc:
            logger.error("Failed to load emotion ONNX model: %s", exc)
            self._available = False
            return False

    def analyze(self, face_bgr_crop: np.ndarray) -> str:
        """
        Analyze a cropped face (BGR) and return the dominant emotion string.
        """
        if face_bgr_crop is None or face_bgr_crop.size == 0:
            return "Neutral"

        if not self._load():
            return "Neutral"

        try:
            # FER+ input requirement: Grayscale 64x64 float32
            gray = cv2.cvtColor(face_bgr_crop, cv2.COLOR_BGR2GRAY)
            resized = cv2.resize(gray, (64, 64), interpolation=cv2.INTER_AREA)
            blob = resized.astype(np.float32).reshape(1, 1, 64, 64)

            self._net.setInput(blob)
            preds = self._net.forward()[0]  # Shape: (8,)

            # Softmax or argmax
            dominant_idx = int(np.argmax(preds))
            emotion = EMOTIONS[dominant_idx]
            # Map contempt to neutral if score is weak
            if emotion == "Contempt" and preds[dominant_idx] < 2.0:
                emotion = "Neutral"

            return emotion
        except Exception as exc:
            logger.debug("Emotion inference exception: %s", exc)
            return "Neutral"

    @property
    def is_available(self) -> bool:
        return self._available
