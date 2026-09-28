"""Train the acne classifier (v2): frozen DINOv2 backbone + logistic-regression head.

Why: with ~170 photos, fine-tuning a CNN overfits. A strong pretrained
backbone used as a frozen feature extractor + a tiny linear head generalises
far better (5-fold CV ~80% accuracy / ~0.89 AUC vs. ~chance for the old CNN).

Dev-only dependencies (NOT needed by the server):  pip install -r requirements-train.txt

Run from the project root or backend/:
    python backend/train_v2.py

Outputs (loaded by main.py through acne_classifier.py):
    backend/model/acne_v2.onnx        backbone
    backend/model/acne_v2_head.json   scaler + logistic-regression head + threshold
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
import numpy as np
import timm
import torch
from PIL import Image
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, roc_auc_score
from sklearn.model_selection import RepeatedStratifiedKFold, StratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
import skin_analysis  # noqa: E402  (same face crop as the server uses)

DATASET = BASE.parent / "dataset"
MODEL_DIR = BASE / "model"
BACKBONE = "vit_small_patch14_dinov2.lvd142m"
SIZE = 336          # multiple of 14
C = 0.03            # regularisation (chosen by CV)


def load_crops():
    crops, y, names = [], [], []
    for split in ("train", "test"):            # pool everything; CV does the splitting
        for cls, label in (("clear", 0), ("acne", 1)):
            for f in sorted((DATASET / split / cls).iterdir()):
                try:
                    got = skin_analysis.extract_skin(Image.open(f))
                except Exception as e:  # unreadable file
                    print("skip", f.name, e)
                    continue
                if got is None:
                    print("no face:", f.name)
                    continue
                crops.append(got[0]); y.append(label); names.append(f.name)
    return crops, np.array(y), names


def to_tensor(crop, mean, std):
    im = cv2.resize(crop, (SIZE, SIZE), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
    return torch.from_numpy(((im - mean) / std).transpose(2, 0, 1)).float()[None]


def main():
    torch.set_num_threads(8)
    model = timm.create_model(BACKBONE, pretrained=True, num_classes=0, img_size=SIZE).eval()
    cfg = timm.data.resolve_data_config({}, model=model)
    mean, std = np.array(cfg["mean"], dtype=np.float32), np.array(cfg["std"], dtype=np.float32)

    crops, y, names = load_crops()
    print(f"{len(y)} images, {int(y.sum())} acne / {int((1 - y).sum())} clear")

    feats = []
    with torch.no_grad():
        for crop in crops:
            x = to_tensor(crop, mean, std)
            feats.append(((model(x) + model(torch.flip(x, [3]))) / 2)[0].numpy())  # flip TTA
    X = np.array(feats)

    # ---- honest evaluation: repeated stratified 5-fold on ALL data
    pipe = make_pipeline(StandardScaler(), LogisticRegression(C=C, class_weight="balanced", max_iter=2000))
    accs, aucs, oof_all = [], [], []
    for seed in range(5):
        oof = cross_val_predict(pipe, X, y, cv=StratifiedKFold(5, shuffle=True, random_state=seed),
                                method="predict_proba")[:, 1]
        oof_all.append(oof)
        accs.append(((oof > 0.5) == y).mean()); aucs.append(roc_auc_score(y, oof))
    oof = np.mean(oof_all, axis=0)
    print("majority-class baseline acc: %.3f" % (1 - y.mean()))
    print("CV accuracy %.3f  balanced %.3f  AUC %.3f" % (np.mean(accs), balanced_accuracy_score(y, oof > 0.5), np.mean(aucs)))

    # threshold: the widest "confident" bands are handled in main.py; 0.5 is the decision boundary
    threshold = 0.5

    # ---- final fit on everything
    pipe.fit(X, y)
    scaler, lr = pipe[0], pipe[1]
    head = {
        "backbone": BACKBONE, "img_size": SIZE, "mean": mean.tolist(), "std": std.tolist(),
        "scaler_mean": scaler.mean_.tolist(), "scaler_scale": scaler.scale_.tolist(),
        "coef": lr.coef_[0].tolist(), "intercept": float(lr.intercept_[0]),
        "threshold": threshold,
        "cv": {"accuracy": float(np.mean(accs)), "auc": float(np.mean(aucs)), "n": int(len(y))},
    }
    MODEL_DIR.mkdir(exist_ok=True)
    (MODEL_DIR / "acne_v2_head.json").write_text(json.dumps(head))

    dummy = torch.zeros(1, 3, SIZE, SIZE)
    torch.onnx.export(model, dummy, str(MODEL_DIR / "acne_v2.onnx"), input_names=["x"], output_names=["emb"],
                      opset_version=17, dynamo=False)
    print("saved", MODEL_DIR / "acne_v2.onnx", "and acne_v2_head.json")


if __name__ == "__main__":
    main()
