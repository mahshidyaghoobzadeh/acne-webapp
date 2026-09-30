**Peace Of Mind — AI Skin Analysis**

Upload a photo of your face, and this app tells you whether it sees acne, what your skin type looks like, and how you might take care of it. Results come in English or Persian.

**What it does**

- Finds your face with **MediaPipe FaceMesh** and looks only at skin, leaving out eyes, brows, and lips
- Checks for acne with a small ML model, and says "not sure" when it honestly isn't
- Measures oiliness, redness, spots, texture, and tone with **OpenCV**
- Suggests a simple routine, useful ingredients, and one homemade mask

## The interesting part

I only had about 170 photos to train on. My first attempt, a fine-tuned CNN, over-fit and did no better than guessing.

So I changed approach: I used a pretrained **DINOv2** model as a frozen feature extractor and trained just a small logistic-regression layer on top. That reached about **80% accuracy (AUC ~0.89)** in 5-fold cross-validation. The model runs with **ONNX Runtime**, so the server doesn't need PyTorch.

## Built with

Python · Fast-API · MediaPipe · Open-CV · DINOv2 · scikit-learn · ONNX Runtime · HTML/CSS/JS · Docker

## Run it

The trained model isn't in the repo. Put your photos in `dataset/train|test/{acne,clear}/`, then:

```bash
pip install -r backend/requirements-train.txt
python backend/train_v2.py      # creates backend/model/
docker compose up --build       # open http://localhost:8000
```

## A note

This is a personal project for cosmetic guidance. It isn't a medical tool. If your skin is bothering you, see a dermatologist.

---

Made by **Mahshid Yaghoobzadeh** · [LinkedIn](https://www.linkedin.com/in/mahshid-yaghoobzadeh-50b594140/)
