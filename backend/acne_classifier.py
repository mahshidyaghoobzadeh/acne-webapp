"""Runtime for the v2 acne classifier (ONNX backbone + linear head, no TensorFlow/PyTorch)."""
from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort

MODEL_DIR = Path(__file__).resolve().parent / "model"


class AcneClassifier:
    def __init__(self, model_dir: Path = MODEL_DIR):
        head = json.loads((model_dir / "acne_v2_head.json").read_text())
        self.size = head["img_size"]
        self.mean = np.array(head["mean"], dtype=np.float32)
        self.std = np.array(head["std"], dtype=np.float32)
        self.s_mean = np.array(head["scaler_mean"])
        self.s_scale = np.array(head["scaler_scale"])
        self.coef = np.array(head["coef"])
        self.intercept = head["intercept"]
        self.cv = head.get("cv", {})
        self.session = ort.InferenceSession(str(model_dir / "acne_v2.onnx"), providers=["CPUExecutionProvider"])

    def _embed(self, crop_rgb: np.ndarray) -> np.ndarray:
        im = cv2.resize(crop_rgb, (self.size, self.size), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
        x = ((im - self.mean) / self.std).transpose(2, 0, 1)[None].astype(np.float32)
        a = self.session.run(None, {"x": x})[0]
        b = self.session.run(None, {"x": x[..., ::-1].copy()})[0]  # horizontal-flip TTA (as in training)
        return ((a + b) / 2)[0]

    def predict(self, crop_rgb: np.ndarray) -> float:
        """Probability that the face crop shows acne (0..1)."""
        z = (self._embed(crop_rgb) - self.s_mean) / self.s_scale
        return float(1.0 / (1.0 + np.exp(-(z @ self.coef + self.intercept))))
