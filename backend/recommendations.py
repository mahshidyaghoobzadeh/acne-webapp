"""Rule-based skincare guidance (bilingual: "en" / "fa").

Turns the measurements from skin_analysis.measure() plus the acne flag into:
skin type + per-dimension levels, cream/ingredient suggestions, a routine and
one homemade mask. Cosmetic guidance only - never a diagnosis.
"""
from __future__ import annotations

# (low_cut, high_cut) - roughly the 33rd / 67th percentile of the project's
# own dataset, so "high" means "high compared with the sample photos".
CUTS = {
    "oiliness": ("shine_frac", 0.001, 0.01),
    "redness": ("a_mean", 141.3, 145.6),
    "blemishes": ("red_blobs", 0.3, 1.06),
    "texture": ("texture", 2.3, 3.0),
    "tone": ("unevenness", 25.0, 32.5),
}

LEVEL_TEXT = {
    "low": {"en": "low", "fa": "کم"},
    "moderate": {"en": "moderate", "fa": "متوسط"},
    "high": {"en": "high", "fa": "زیاد"},
}
DIM_TEXT = {
    "oiliness": {"en": "Oiliness / shine", "fa": "چربی و براقی"},
    "redness": {"en": "Redness", "fa": "قرمزی"},
    "blemishes": {"en": "Blemish spots", "fa": "لکه‌های جوشی"},
    "texture": {"en": "Roughness / texture", "fa": "زبری و بافت"},
    "tone": {"en": "Tone evenness", "fa": "یکنواختی رنگ"},
}
TYPE_TEXT = {
    "oily": {"en": "Oily", "fa": "چرب"},
    "dry": {"en": "Dry", "fa": "خشک"},
    "combination": {"en": "Combination", "fa": "مختلط"},
    "normal": {"en": "Normal", "fa": "معمولی"},
}


def _level(dim: str, m: dict) -> str:
    key, lo, hi = CUTS[dim]
    v = m[key]
    return "low" if v < lo else "high" if v > hi else "moderate"


def _skin_type(lv: dict) -> str:
    if lv["oiliness"] == "high":
        return "oily"
    if lv["oiliness"] == "low" and lv["texture"] == "high":
        return "dry"
    if lv["oiliness"] == "moderate" and lv["texture"] == "high":
        return "combination"
    return "normal"


# --------------------------------------------------------------------------
# Content
# --------------------------------------------------------------------------
def _p(en, fa):
    return {"en": en, "fa": fa}


PRODUCTS = {
    "cleanser_acne": {
        "type": _p("Cleanser", "شوینده"),
        "pick": _p("Gentle gel cleanser with 0.5–2% salicylic acid (BHA), used once a day in the evening",
                   "ژل شوینده ملایم حاوی ۰.۵ تا ۲٪ سالیسیلیک اسید (BHA)، یک بار در روز (شب)"),
        "why": _p("Unclogs pores without stripping the skin.", "منافذ را باز می‌کند بدون اینکه پوست را خشک کند."),
    },
    "cleanser_gentle": {
        "type": _p("Cleanser", "شوینده"),
        "pick": _p("Mild, fragrance-free, sulfate-free cream or gel cleanser, morning and evening",
                   "شوینده ملایم بدون عطر و بدون سولفات (ژلی یا کرمی)، صبح و شب"),
        "why": _p("Keeps the skin barrier intact.", "سد محافظ پوست را حفظ می‌کند."),
    },
    "treat_acne": {
        "type": _p("Spot / treatment cream", "کرم درمانی موضعی"),
        "pick": _p("Benzoyl peroxide 2.5% gel or adapalene 0.1% (start every 2–3 nights); never both on the same night at first",
                   "ژل بنزوئیل پراکسید ۲.۵٪ یا آداپالن ۰.۱٪ (ابتدا هر ۲–۳ شب یک بار)؛ در ابتدا هر دو را در یک شب استفاده نکنید"),
        "why": _p("The best-studied over-the-counter options for inflamed and clogged-pore acne.",
                  "بهترین گزینه‌های بدون‌نسخه برای جوش‌های التهابی و منافذ مسدود."),
    },
    "serum_niacinamide": {
        "type": _p("Serum", "سرم"),
        "pick": _p("Niacinamide 4–5% serum (up to 10% if tolerated)", "سرم نیاسینامید ۴ تا ۵٪ (در صورت تحمل تا ۱۰٪)"),
        "why": _p("Calms redness, regulates oil and evens tone.", "قرمزی را کم می‌کند، چربی را تنظیم و رنگ پوست را یکدست می‌کند."),
    },
    "azelaic": {
        "type": _p("Treatment cream", "کرم درمانی"),
        "pick": _p("Azelaic acid 10% cream/gel in the evening", "کرم یا ژل آزلائیک اسید ۱۰٪ در شب"),
        "why": _p("Helps acne, redness and dark marks at once, and is gentle.",
                  "روی جوش، قرمزی و لکه‌های تیره هم‌زمان اثر دارد و ملایم است."),
    },
    "moist_gel": {
        "type": _p("Moisturizer", "مرطوب‌کننده"),
        "pick": _p("Light oil-free gel moisturizer with hyaluronic acid", "ژل مرطوب‌کننده سبک و بدون روغن حاوی هیالورونیک اسید"),
        "why": _p("Hydrates without clogging pores.", "بدون مسدود کردن منافذ رطوبت می‌دهد."),
    },
    "moist_rich": {
        "type": _p("Moisturizer", "مرطوب‌کننده"),
        "pick": _p("Ceramide + hyaluronic acid cream (add glycerin / squalane for very dry skin)",
                   "کرم حاوی سرامید و هیالورونیک اسید (برای پوست خیلی خشک گلیسیرین یا اسکوالان)"),
        "why": _p("Rebuilds the moisture barrier and smooths rough texture.", "سد رطوبتی را ترمیم و زبری را کم می‌کند."),
    },
    "soothing": {
        "type": _p("Soothing cream", "کرم آرام‌بخش"),
        "pick": _p("Cream with centella (cica), panthenol or allantoin", "کرم حاوی سنتلا (سیکا)، پانتنول یا آلانتوئین"),
        "why": _p("Reduces visible redness and irritation.", "قرمزی و التهاب ظاهری را کاهش می‌دهد."),
    },
    "vitc": {
        "type": _p("Brightening serum", "سرم روشن‌کننده"),
        "pick": _p("Vitamin C 10–15% serum in the morning, under sunscreen", "سرم ویتامین C ۱۰ تا ۱۵٪ صبح‌ها، زیر ضدآفتاب"),
        "why": _p("Fades dark marks and evens tone over weeks.", "طی چند هفته لکه‌های تیره را کم‌رنگ و رنگ پوست را یکدست می‌کند."),
    },
    "spf": {
        "type": _p("Sunscreen", "ضدآفتاب"),
        "pick": _p("Broad-spectrum SPF 30–50, non-comedogenic, every morning", "ضدآفتاب SPF ۳۰ تا ۵۰ (طیف وسیع، غیرمسدودکننده منافذ)، هر صبح"),
        "why": _p("Prevents acne marks from darkening and protects results.",
                  "از تیره‌شدن جای جوش جلوگیری می‌کند و نتیجه را حفظ می‌کند."),
    },
}

MASKS = {
    "clay": {
        "name": _p("Green tea & clay mask (oil control)", "ماسک خاک رس و چای سبز (کنترل چربی)"),
        "ingredients": [_p("1 tbsp kaolin or bentonite clay", "۱ قاشق غذاخوری خاک رس کائولین یا بنتونیت"),
                        _p("2 tbsp cooled strong green tea", "۲ قاشق غذاخوری چای سبز پررنگ سرد‌شده"),
                        _p("1 tsp honey (optional)", "۱ قاشق چای‌خوری عسل (اختیاری)")],
        "steps": [_p("Mix into a smooth paste (not runny).", "را به شکل خمیر یکدست مخلوط کنید."),
                  _p("Apply a thin layer on clean, dry skin, avoiding eyes and lips.", "لایه نازکی روی پوست تمیز و خشک بمالید (دور چشم و لب نه)."),
                  _p("Leave 10 minutes; rinse before it fully cracks.", "۱۰ دقیقه بگذارید؛ قبل از خشک و ترک‌خوردن کامل بشویید."),
                  _p("Follow with a light moisturizer.", "بعد از آن مرطوب‌کننده سبک بزنید.")],
        "frequency": _p("Once a week", "هفته‌ای یک بار"),
    },
    "soothing": {
        "name": _p("Honey, aloe & oat calming mask", "ماسک آرام‌بخش عسل، آلوئه‌ورا و جو دوسر"),
        "ingredients": [_p("1 tbsp raw honey", "۱ قاشق غذاخوری عسل خام"),
                        _p("1 tbsp pure aloe vera gel", "۱ قاشق غذاخوری ژل خالص آلوئه‌ورا"),
                        _p("1 tbsp finely ground oats", "۱ قاشق غذاخوری جو دوسر آسیاب‌شده ریز")],
        "steps": [_p("Blend into a spreadable paste.", "را تا رسیدن به خمیر قابل‌پخش مخلوط کنید."),
                  _p("Apply on clean skin and relax for 15 minutes.", "روی پوست تمیز بمالید و ۱۵ دقیقه صبر کنید."),
                  _p("Rinse with lukewarm water and pat dry.", "با آب ولرم بشویید و خشک کنید.")],
        "frequency": _p("1–2 times a week", "هفته‌ای ۱ تا ۲ بار"),
    },
    "brightening": {
        "name": _p("Yogurt & honey brightening mask", "ماسک روشن‌کننده ماست و عسل"),
        "ingredients": [_p("2 tbsp plain unsweetened yogurt", "۲ قاشق غذاخوری ماست ساده بدون شکر"),
                        _p("1 tsp honey", "۱ قاشق چای‌خوری عسل"),
                        _p("1 tsp ground oats (optional, for body)", "۱ قاشق چای‌خوری جو دوسر (اختیاری)")],
        "steps": [_p("Mix well.", "را خوب مخلوط کنید."),
                  _p("Apply on clean skin for 10–15 minutes.", "۱۰ تا ۱۵ دقیقه روی پوست تمیز بمالید."),
                  _p("Rinse gently with lukewarm water.", "به آرامی با آب ولرم بشویید.")],
        "frequency": _p("Once or twice a week", "هفته‌ای یک یا دو بار"),
    },
    "hydrating": {
        "name": _p("Banana, yogurt & honey hydrating mask", "ماسک مرطوب‌کننده موز، ماست و عسل"),
        "ingredients": [_p("½ ripe banana, mashed", "نصف موز رسیده له‌شده"),
                        _p("1 tbsp plain yogurt", "۱ قاشق غذاخوری ماست ساده"),
                        _p("1 tsp honey", "۱ قاشق چای‌خوری عسل")],
        "steps": [_p("Mash until completely smooth.", "را کاملاً صاف له کنید."),
                  _p("Apply on clean skin for 15 minutes.", "۱۵ دقیقه روی پوست تمیز بمالید."),
                  _p("Rinse with lukewarm water, then moisturize.", "با آب ولرم بشویید و مرطوب‌کننده بزنید.")],
        "frequency": _p("1–2 times a week", "هفته‌ای ۱ تا ۲ بار"),
    },
    "fresh": {
        "name": _p("Cucumber & aloe refresh mask", "ماسک شاداب‌کننده خیار و آلوئه‌ورا"),
        "ingredients": [_p("¼ cucumber, blended", "یک‌چهارم خیار، میکس‌شده"),
                        _p("1 tbsp aloe vera gel", "۱ قاشق غذاخوری ژل آلوئه‌ورا"),
                        _p("1 tsp honey", "۱ قاشق چای‌خوری عسل")],
        "steps": [_p("Mix into a light paste.", "را مخلوط کنید."),
                  _p("Apply for 15 minutes, rinse with cool water.", "۱۵ دقیقه بمالید و با آب خنک بشویید.")],
        "frequency": _p("Once a week", "هفته‌ای یک بار"),
    },
}

ROUTINE = {
    "am": [_p("Gentle cleanser", "شوینده ملایم"), _p("Serum (niacinamide / vitamin C)", "سرم (نیاسینامید / ویتامین C)"),
           _p("Moisturizer", "مرطوب‌کننده"), _p("Sunscreen SPF 30+", "ضدآفتاب SPF ۳۰+")],
    "pm": [_p("Cleanser", "شوینده"), _p("Treatment (if any)", "کرم درمانی (در صورت نیاز)"),
           _p("Moisturizer", "مرطوب‌کننده")],
}

SAFETY = {
    "en": [
        "Patch-test any new product or mask on your inner forearm or behind the ear 24 hours before using it on your face.",
        "Skip masks on open, bleeding or very inflamed skin, and rinse off immediately if it burns.",
        "Avoid picking, harsh scrubs and alcohol toners.",
        "Pregnant or breastfeeding? Ask a doctor before using salicylic acid, adapalene or benzoyl peroxide.",
        "See a dermatologist for painful deep bumps, scarring, or acne that doesn't improve after 8–12 weeks.",
    ],
    "fa": [
        "هر محصول یا ماسک جدید را ۲۴ ساعت قبل روی ساعد یا پشت گوش تست کنید.",
        "روی پوست زخمی، خونریزی‌دار یا بسیار ملتهب ماسک نگذارید و در صورت سوزش فوراً بشویید.",
        "از دست‌زدن به جوش‌ها، اسکراب‌های خشن و تونر الکلی پرهیز کنید.",
        "در بارداری یا شیردهی قبل از سالیسیلیک اسید، آداپالن یا بنزوئیل پراکسید با پزشک مشورت کنید.",
        "برای جوش‌های عمیق و دردناک، جای زخم، یا نبود بهبودی بعد از ۸ تا ۱۲ هفته به متخصص پوست مراجعه کنید.",
    ],
}

DISCLAIMER = {
    "en": "This is an automatic, cosmetic analysis of one photo (lighting and camera affect it). It is not a medical diagnosis.",
    "fa": "این یک تحلیل خودکار و آرایشی از یک عکس است (نور و دوربین روی آن اثر می‌گذارند) و تشخیص پزشکی نیست.",
}

SUMMARY = {
    "en": {
        "acne": "Acne-prone signs detected. Your skin looks {type}; main focus: {focus}.",
        "clear": "No significant acne detected. Your skin looks {type}; main focus: {focus}.",
    },
    "fa": {
        "acne": "نشانه‌های جوش دیده شد. پوست شما {type} به نظر می‌رسد؛ تمرکز اصلی: {focus}.",
        "clear": "جوش قابل‌توجهی دیده نشد. پوست شما {type} به نظر می‌رسد؛ تمرکز اصلی: {focus}.",
    },
}
FOCUS = {
    "oil": _p("oil control and clearing pores", "کنترل چربی و پاک‌سازی منافذ"),
    "acne": _p("calming blemishes and preventing new ones", "آرام‌کردن جوش‌ها و پیشگیری از جوش جدید"),
    "redness": _p("reducing redness", "کاهش قرمزی"),
    "tone": _p("evening out skin tone", "یکدست‌کردن رنگ پوست"),
    "dry": _p("hydration and barrier repair", "آبرسانی و ترمیم سد محافظ"),
    "maintain": _p("gentle maintenance and sun protection", "نگهداری ملایم و محافظت در برابر آفتاب"),
}


def _t(x, lang):
    return x.get(lang) or x["en"]


def build(measurements: dict, has_acne: bool, lang: str = "en") -> dict:
    """Return the structured analysis + recommendations for the frontend."""
    lang = lang if lang in ("en", "fa") else "en"
    lv = {d: _level(d, measurements) for d in CUTS}
    skin_type = _skin_type(lv)

    acne_like = has_acne or lv["blemishes"] == "high"
    oily = skin_type == "oily"
    red = lv["redness"] == "high"
    uneven = lv["tone"] == "high"
    dry = skin_type == "dry"

    # ---- products (ordered: cleanse -> treat -> moisturize -> protect)
    keys: list[str] = []
    keys.append("cleanser_acne" if acne_like and (oily or skin_type == "combination") else "cleanser_gentle")
    if acne_like:
        keys.append("treat_acne")
    if acne_like or oily or red or uneven:
        keys.append("serum_niacinamide")
    if (acne_like and (red or uneven)) and "azelaic" not in keys:
        keys.append("azelaic")
    if uneven and not acne_like:
        keys.append("vitc")
    if red and not acne_like:
        keys.append("soothing")
    keys.append("moist_rich" if dry else "moist_gel" if (oily or acne_like) else "moist_rich")
    keys.append("spf")

    products = [{"type": _t(PRODUCTS[k]["type"], lang), "pick": _t(PRODUCTS[k]["pick"], lang),
                 "why": _t(PRODUCTS[k]["why"], lang)} for k in keys]

    # ---- one homemade mask
    if acne_like and oily:
        mask_key, focus = "clay", "oil"
    elif acne_like or red:
        mask_key, focus = "soothing", ("acne" if acne_like else "redness")
    elif uneven:
        mask_key, focus = "brightening", "tone"
    elif dry:
        mask_key, focus = "hydrating", "dry"
    else:
        mask_key, focus = "fresh", "maintain"
    m = MASKS[mask_key]
    mask = {
        "name": _t(m["name"], lang),
        "ingredients": [_t(i, lang) for i in m["ingredients"]],
        "steps": [_t(s, lang) for s in m["steps"]],
        "frequency": _t(m["frequency"], lang),
    }

    summary = SUMMARY[lang]["acne" if has_acne else "clear"].format(
        type=_t(TYPE_TEXT[skin_type], lang), focus=_t(FOCUS[focus], lang))

    return {
        "summary": summary,
        "skin": {
            "type": _t(TYPE_TEXT[skin_type], lang),
            "levels": [{"name": _t(DIM_TEXT[d], lang), "level": lv[d], "label": _t(LEVEL_TEXT[lv[d]], lang)} for d in CUTS],
        },
        "products": products,
        "mask": mask,
        "routine": {k: [_t(s, lang) for s in v] for k, v in ROUTINE.items()},
        "safety": SAFETY[lang],
        "disclaimer": DISCLAIMER[lang],
    }
