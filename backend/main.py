import os
import io
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from PIL import Image

# Skin analysis + recommendations
import skin_analysis
import recommendations


# ===============================
# PATHS مطابق ساختار پروژه شما
# acne-webapp/backend/main.py  <-- این فایل
# acne-webapp/frontend/...
# acne-webapp/backend/model/acne_v2.onnx
# ===============================
BASE_DIR = Path(__file__).resolve().parent          # acne-webapp/backend
PROJECT_DIR = BASE_DIR.parent                      # acne-webapp
FRONTEND_DIR = PROJECT_DIR / "frontend"            # acne-webapp/frontend

# ===============================
# APP
# ===============================
app = FastAPI(title="Acne Predictor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===============================
# LOAD MODEL (v2: ONNX backbone + linear head; see train_v2.py)
# ===============================
import acne_classifier

classifier = acne_classifier.AcneClassifier()

# ===============================
# API
# ===============================
NO_FACE = {
    "en": ("No clear face found in the photo. Please upload a clear, front-facing photo 🙂",
           "Face the camera, use good even light, no filters, and keep your whole face in the frame."),
    "fa": ("صورت واضحی در تصویر پیدا نشد. لطفاً عکس واضح از صورت ارسال کنید 🙂",
           "عکس رو‌به‌رو، نور مناسب، بدون فیلتر، صورت داخل کادر باشد."),
}
RESULT_TEXT = {
    "en": {"acne": "Acne detected 😕", "clear": "Your skin looks clear 😊",
           "unsure": "Not sure 😕 please upload a clearer photo with better light."},
    "fa": {"acne": "جوش صورت تشخیص داده شد 😕", "clear": "پوست سالمه 😊",
           "unsure": "تشخیص نامطمئن است 😕 لطفاً عکس واضح‌تر با نور بهتر ارسال کنید."},
}


@app.post("/predict")
async def predict(file: UploadFile = File(...), lang: str = Form("en")):
    lang = lang if lang in ("en", "fa") else "en"
    try:
        content = await file.read()
        image = Image.open(io.BytesIO(content)).convert("RGB")

        # 1) Face gate + skin extraction (FaceMesh)
        got = skin_analysis.extract_skin(image)
        measurements = skin_analysis.measure_skin(*got) if got is not None else None
        if got is None or measurements is None:
            result, rec = NO_FACE[lang]
            return {"result": result, "confidence": 0.0, "recommendation": rec}

        # 2) Predict acne
        p_acne = classifier.predict(got[0])
        confidence = max(p_acne, 1.0 - p_acne)

        # 3) Uncertain zone: still give skin-care guidance, based on the measurements
        unsure = 0.4 <= p_acne <= 0.6
        has_acne = p_acne > 0.5
        analysis = recommendations.build(measurements, has_acne and not unsure, lang)
        result = RESULT_TEXT[lang]["unsure" if unsure else "acne" if has_acne else "clear"]

        return {
            "result": result,
            "confidence": round(confidence, 2),
            "recommendation": analysis["summary"],
            "analysis": analysis,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===============================
# FRONTEND SERVE (بدون تغییر مسیر پروژه)
# ===============================
# کل پوشه acne-webapp/frontend رو روی /static سرو می‌کنیم
# یعنی فایل‌های شما سر جاشون می‌مونن
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.get("/")
async def root():
    # صفحه اصلی: Home
    return FileResponse(str(FRONTEND_DIR / "index.html"))

@app.get("/{path:path}")
async def frontend(path: str):
    # اجازه بده فایل‌های واقعی فرانت باز بشن
    file_path = FRONTEND_DIR / path
    if file_path.is_file():
        return FileResponse(str(file_path))
    # اگر مسیر ناشناخته بود، باز هم AIsystem
    return FileResponse(str(FRONTEND_DIR / "AIsystem.html"))
