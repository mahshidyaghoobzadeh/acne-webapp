document.addEventListener("DOMContentLoaded", () => {
  const fileInput = document.getElementById("camera");
  const previewImage = document.getElementById("preview");
  const resultContainer = document.getElementById("result");
  const sendBtn = document.getElementById("sendBtn");

  // Only the Services page has the upload widget.
  if (!fileInput || !previewImage || !resultContainer || !sendBtn) return;

  const MAX_BYTES = 10 * 1024 * 1024;
  const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"];

  // Same origin when served by the backend (port 8000 or behind a proxy);
  // otherwise (file://, live-server, ...) talk to the local backend.
  // Override with: <script>window.API_BASE = "https://example.com"</script>
  const API_BASE =
    window.API_BASE ??
    (location.protocol !== "file:" && (location.port === "8000" || location.port === "")
      ? ""
      : "http://localhost:8000");

  function showMessage(text, isError = false) {
    resultContainer.replaceChildren();
    const p = document.createElement("p");
    if (isError) p.className = "error";
    p.textContent = text;
    resultContainer.append(p);
  }

  function validate(file) {
    if (!file) return "Please choose a photo first.";
    if (!ALLOWED_TYPES.includes(file.type)) return "Please use a JPG, PNG or WebP image.";
    if (file.size > MAX_BYTES) return "That image is larger than 10 MB. Please choose a smaller one.";
    return null;
  }

  // Preview
  fileInput.addEventListener("change", () => {
    const file = fileInput.files?.[0];
    if (previewImage.src.startsWith("blob:")) URL.revokeObjectURL(previewImage.src);

    const problem = file && validate(file);
    if (!file || problem) {
      previewImage.removeAttribute("src");
      previewImage.classList.remove("show");
      if (problem) showMessage(problem, true);
      return;
    }

    resultContainer.replaceChildren();
    previewImage.src = URL.createObjectURL(file);
    previewImage.classList.add("show");
  });

  const LANG = window.SITE_LANG || "en";
  const UI = {
    en: { skin: "Your skin", type: "Skin type", creams: "Creams & products to use", mask: "Homemade mask for you",
          ingredients: "You need", steps: "How to", freq: "How often", routine: "Simple routine", am: "Morning", pm: "Evening",
          safety: "Please note", confidence: "Confidence" },
    fa: { skin: "پوست شما", type: "نوع پوست", creams: "کرم‌ها و محصولات پیشنهادی", mask: "ماسک خانگی پیشنهادی",
          ingredients: "مواد لازم", steps: "طرز تهیه و استفاده", freq: "تناوب", routine: "روتین ساده", am: "صبح", pm: "شب",
          safety: "نکات مهم", confidence: "اطمینان" },
  }[LANG] || UI.en;

  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function list(tag, items) {
    const node = el(tag);
    items.forEach((t) => node.append(el("li", "", t)));
    return node;
  }

  function section(title, ...children) {
    const wrap = el("section", "ai-section-block");
    wrap.append(el("h4", "", title), ...children);
    return wrap;
  }

  function renderResult(data) {
    const box = el("div", "ai-result");
    box.append(el("h3", "", data.result));
    if (data.confidence) {
      const c = el("p", "ai-confidence");
      c.append(el("strong", "", `${UI.confidence}: `), String(data.confidence));
      box.append(c);
    }

    const a = data.analysis;
    if (!a) {
      box.append(document.createElement("hr"), el("p", "", data.recommendation));
      resultContainer.replaceChildren(box);
      return;
    }

    box.append(el("p", "ai-summary", a.summary));

    // Skin analysis
    const chips = el("div", "level-chips");
    a.skin.levels.forEach((l) => {
      const chip = el("span", `chip chip-${l.level}`);
      chip.append(el("span", "chip-name", l.name), el("span", "chip-val", l.label));
      chips.append(chip);
    });
    const typeLine = el("p", "");
    typeLine.append(el("strong", "", `${UI.type}: `), a.skin.type);
    box.append(section(UI.skin, typeLine, chips));

    // Creams / products
    const prods = el("ul", "product-list");
    a.products.forEach((p) => {
      const li = el("li");
      li.append(el("strong", "", `${p.type}: `), p.pick, el("small", "", p.why));
      prods.append(li);
    });
    box.append(section(UI.creams, prods));

    // Homemade mask
    const m = a.mask;
    const maskCard = el("div", "mask-card");
    maskCard.append(
      el("h5", "", m.name),
      el("p", "", UI.ingredients + ":"), list("ul", m.ingredients),
      el("p", "", UI.steps + ":"), list("ol", m.steps),
    );
    const f = el("p");
    f.append(el("strong", "", `${UI.freq}: `), m.frequency);
    maskCard.append(f);
    box.append(section(UI.mask, maskCard));

    // Routine
    const routine = el("div", "routine");
    [["am", UI.am], ["pm", UI.pm]].forEach(([key, label]) => {
      const col = el("div");
      col.append(el("h5", "", label), list("ol", a.routine[key]));
      routine.append(col);
    });
    box.append(section(UI.routine, routine));

    box.append(section(UI.safety, list("ul", a.safety)), el("p", "ai-disclaimer", a.disclaimer));

    resultContainer.replaceChildren(box);
    resultContainer.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  async function send() {
    const file = fileInput.files?.[0];
    const problem = validate(file);
    if (problem) {
      showMessage(problem, true);
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    formData.append("lang", LANG);

    showMessage("⏳ Analyzing your photo...");
    sendBtn.disabled = true;

    try {
      const response = await fetch(`${API_BASE}/predict`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data?.detail || "Server error");

      renderResult(data);
    } catch (error) {
      console.error(error);
      showMessage("Something went wrong while contacting the server or analyzing the image. Please try again.", true);
    } finally {
      sendBtn.disabled = false;
    }
  }

  sendBtn.addEventListener("click", send);
});
