from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

client = QdrantClient("qdrant:6333")  # داخل شبکه docker، اسم سرویس qdrant
model = SentenceTransformer('all-MiniLM-L6-v2')

products = [
    "ماسک عسل و دارچین: ضدالتهاب قوی، مناسب جوش‌های ملایم. ۱ قاشق عسل + کمی دارچین، ۱۵ دقیقه روی پوست.",
    "ماسک خاک رس (بنتونیت) و سرکه سیب: کنترل چربی اضافی، مناسب پوست چرب و جوش‌دار.",
    "ژل آلوئه‌ورا خالص: آرام‌بخش و ضدالتهاب، عالی برای پس از جوش.",
    "سرم نیاسینامید ۱۰٪: کاهش قرمزی، تنظیم چربی و کوچک کردن منافذ.",
    "ماسک زردچوبه و ماست: روشن‌کننده و ضدجوش، هفته‌ای ۲ بار.",
    "کرم رتینول ملایم: برای جلوگیری از جوش‌های جدید و بهبود جای جوش.",
    "ماسک چای سبز و عسل: آنتی‌اکسیدان بالا، مناسب پوست حساس و جوش‌دار.",
    "روغن درخت چای (تی تری): ضدباکتریایی قوی، نقطه‌ای روی جوش‌ها استفاده شود.",
    "ماسک خیار و گلاب: خنک‌کننده و کاهش التهاب، عالی برای پوست قرمز شده.",
    "سرم ویتامین C: روشن‌کننده جای جوش و تقویت پوست.",
]

vectors = model.encode(products).tolist()

points = [
    {"id": i, "vector": vector, "payload": {"text": text}}
    for i, (vector, text) in enumerate(zip(vectors, products))
]

client.upsert(collection_name="skin_products", points=points)
print("داده‌های اولیه با موفقیت به Qdrant اضافه شد!")