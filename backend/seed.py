from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from qdrant_client.http.models import PointStruct


client = QdrantClient("http://localhost:6333")
model = SentenceTransformer('all-MiniLM-L6-v2')

products = [
    {"text": "ماسک عسل و دارچین: ضد التهاب قوی، مناسب آکنه ملایم. ۱ قاشق عسل + کمی دارچین، ۱۵ دقیقه روی پوست."},
    {"text": "کرم بنزوئیل پراکسید ۵٪: بهترین برای جوش‌های التهابی، روزی یک بار استفاده شود."},
    {"text": "ماسک خاک رس و چای سبز: جذب چربی اضافی، مناسب پوست چرب و جوش‌دار."},
    {"text": "آلوئه‌ورا خالص: آرام‌بخش و مرطوب‌کننده، برای پوست حساس پس از آکنه."},
    {"text": "سرم نیاسینامید ۱۰٪: کاهش التهاب و تنظیم چربی پوست."},
]

vectors = model.encode([p["text"] for p in products]).tolist()

points = [
    PointStruct(id=i, vector=vector, payload={"text": text})
    for i, (vector, text) in enumerate(zip(vectors, [p["text"] for p in products]))
]

client.upsert(collection_name="skin_products", points=points)
print("داده‌های اولیه به Qdrant اضافه شد!")
