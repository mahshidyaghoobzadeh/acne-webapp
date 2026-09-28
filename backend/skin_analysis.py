"""Classical-CV skin analysis (no pretrained weights needed).

Uses MediaPipe FaceMesh to isolate real skin (face oval minus eyes, brows and
lips), then measures redness, oiliness/shine, texture, blemish blobs and
unevenness. All numbers are heuristics for cosmetic guidance, not diagnosis.
"""
from __future__ import annotations

import cv2
import mediapipe as mp
import numpy as np
from PIL import Image

_mesh_mod = mp.solutions.face_mesh
_conn = mp.solutions.face_mesh_connections

_mesh = _mesh_mod.FaceMesh(
    static_image_mode=True,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
)


def _idx(connections) -> list[int]:
    return sorted({i for pair in connections for i in pair})


_OVAL = _idx(_conn.FACEMESH_FACE_OVAL)
_EXCLUDE = [
    _idx(_conn.FACEMESH_LIPS),
    _idx(_conn.FACEMESH_LEFT_EYE),
    _idx(_conn.FACEMESH_RIGHT_EYE),
    _idx(_conn.FACEMESH_LEFT_EYEBROW),
    _idx(_conn.FACEMESH_RIGHT_EYEBROW),
]

WORK_WIDTH = 384          # every face is analysed at the same scale
MAX_INPUT_SIDE = 1024


def _hull_mask(pts: np.ndarray, shape, value: int, mask: np.ndarray) -> None:
    cv2.fillConvexPoly(mask, cv2.convexHull(pts.astype(np.int32)), value)


def extract_skin(image: Image.Image):
    """Return (rgb_crop, skin_mask) at a fixed working scale, or None."""
    rgb = np.array(image.convert("RGB"))
    h, w = rgb.shape[:2]
    scale = min(1.0, MAX_INPUT_SIDE / max(h, w))
    if scale < 1.0:
        rgb = cv2.resize(rgb, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
        h, w = rgb.shape[:2]

    res = _mesh.process(rgb)
    if not res.multi_face_landmarks:
        return None
    lm = res.multi_face_landmarks[0].landmark
    pts = np.array([[p.x * w, p.y * h] for p in lm], dtype=np.float32)

    mask = np.zeros((h, w), np.uint8)
    _hull_mask(pts[_OVAL], (h, w), 255, mask)
    for group in _EXCLUDE:
        _hull_mask(pts[group], (h, w), 0, mask)

    x1, y1 = np.maximum(pts[_OVAL].min(0).astype(int), 0)
    x2, y2 = pts[_OVAL].max(0).astype(int)
    x2, y2 = min(x2, w), min(y2, h)
    if x2 - x1 < 40 or y2 - y1 < 40:
        return None

    crop, m = rgb[y1:y2, x1:x2], mask[y1:y2, x1:x2]
    f = WORK_WIDTH / crop.shape[1]
    crop = cv2.resize(crop, (WORK_WIDTH, int(crop.shape[0] * f)), interpolation=cv2.INTER_AREA)
    m = cv2.resize(m, (crop.shape[1], crop.shape[0]), interpolation=cv2.INTER_NEAREST)
    m = cv2.erode(m, np.ones((5, 5), np.uint8))  # drop hairline / edge pixels
    return crop, m > 0


def _blob_count(binary: np.ndarray, min_area: int, max_area: int) -> int:
    n, _, stats, _ = cv2.connectedComponentsWithStats(binary.astype(np.uint8), connectivity=8)
    areas = stats[1:, cv2.CC_STAT_AREA]
    return int(((areas >= min_area) & (areas <= max_area)).sum())


FEATURE_NAMES = [
    "a_mean", "a_std", "b_mean", "L_mean", "L_std",
    "red_frac", "red_blobs", "dark_blobs", "shine_frac",
    "texture", "unevenness",
]


def measure(image: Image.Image) -> dict | None:
    """Raw skin measurements (unit-free, comparable across photos)."""
    got = extract_skin(image)
    return None if got is None else measure_skin(*got)


def measure_skin(rgb: np.ndarray, skin: np.ndarray) -> dict | None:
    """Same as measure() but for an already extracted (crop, skin_mask)."""
    n_skin = int(skin.sum())
    if n_skin < 3000:
        return None

    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    L, a, b = lab[..., 0], lab[..., 1], lab[..., 2]
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)

    # local background = heavy blur of the image; blemishes stand out from it
    a_bg = cv2.GaussianBlur(a, (0, 0), 12)
    L_bg = cv2.GaussianBlur(L, (0, 0), 12)
    red_delta = (a - a_bg) * skin
    dark_delta = (L_bg - L) * skin

    red_mask = red_delta > 6
    dark_mask = dark_delta > 14
    per10k = 10000.0 / n_skin

    L_fine = cv2.GaussianBlur(L, (0, 0), 1.0)
    texture = np.abs(L - cv2.GaussianBlur(L, (0, 0), 3.0))[skin].mean()

    return {
        "a_mean": float(a[skin].mean()),
        "a_std": float(a[skin].std()),
        "b_mean": float(b[skin].mean()),
        "L_mean": float(L[skin].mean()),
        "L_std": float(L_fine[skin].std()),
        "red_frac": float(red_mask[skin].mean()),
        "red_blobs": _blob_count(red_mask & skin, 6, 500) * per10k,
        "dark_blobs": _blob_count(dark_mask & skin, 6, 500) * per10k,
        "shine_frac": float(((hsv[..., 1] < 50) & (hsv[..., 2] > 235))[skin].mean()),
        "texture": float(texture),
        "unevenness": float(cv2.GaussianBlur(L, (0, 0), 8)[skin].std()),
    }
