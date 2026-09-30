# **Peace Of Mind — AI Skin Analysis Web App**

**Computer Vision · Machine Learning · DINOv2 · FastAPI · Docker**

An AI-powered web application that combines computer vision and machine learning to analyze facial skin and provide cosmetic skincare guidance.

Peace Of Mind allows users to upload a facial image and receive an AI-assisted analysis of acne presence, skin characteristics, and several visual skin metrics.

The project combines **DINOv2-based visual feature extraction, machine learning, MediaPipe FaceMesh, OpenCV, FastAPI, and Docker** into a complete web application.

> **Disclaimer:** This is an experimental personal project for cosmetic and educational purposes. It is not a medical diagnostic system and should not be used as a substitute for professional medical advice.

## Overview

The goal of this project was to explore how computer vision and lightweight machine learning models can be combined to create a practical AI-powered skincare application.

Instead of relying entirely on a large end-to-end neural network, the system separates facial-region detection, visual feature extraction, acne classification, and skin analysis into different components.

The application supports both **English and Persian** results.

## The interesting part

I only had about **170 photos** to train on.

My first attempt used a fine-tuned CNN, but the model overfit and performed close to random-chance performance on the available data.

So I changed the approach: I used a pretrained **DINOv2** model as a frozen feature extractor and trained a lightweight **Logistic Regression** classifier on top.

This approach reached approximately **80% accuracy (AUC ~0.89)** in 5-fold cross-validation on the experimental dataset.

For inference, the model runs with **ONNX Runtime**, so the server does not need PyTorch.

## Built with

**Python · FastAPI · MediaPipe · OpenCV · DINOv2 · scikit-learn · ONNX Runtime · HTML/CSS/JavaScript · Docker**

## Run locally

The trained model is not included in the repository.

Prepare the dataset using:

```text
dataset/
├── train/
│   ├── acne/
│   └── clear/
└── test/
    ├── acne/
    └── clear/
```

Then run:

```bash
pip install -r backend/requirements-train.txt
python backend/train_v2.py
docker compose up --build
```

Open:

```text
http://localhost:8000
```

## A note

This is a personal project for cosmetic and educational purposes. It is **not a medical diagnostic tool**.

If you have a persistent or concerning skin condition, consult a qualified dermatologist.

---

Made by **Mahshid Yaghoobzadeh** · [LinkedIn](https://www.linkedin.com/in/mahshid-yaghoobzadeh-50b594140/)
