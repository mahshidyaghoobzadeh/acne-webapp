// 📌 1. پکیج‌های لازم را وارد می‌کنیم
const express = require('express');
const cors = require('cors');
const path = require('path');
require('dotenv').config();
const OpenAI = require('openai');

// 📌 2. اپلیکیشن Express
const app = express();
app.use(cors());
app.use(express.json());

// 📌 3. اتصال به OpenAI
const client = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY
});

// 📌 4. سرو کردن فایل‌های فرانت‌اند
app.use(express.static(path.join(__dirname, 'public')));

// 📌 5. API اصلی چت
app.post('/api/chat', async (req, res) => {
  try {
    const userMessage = req.body.message;

    // پیام را برای OpenAI ارسال می‌کنیم
    const completion = await client.chat.completions.create({
      model: "gpt-4o-mini",
      messages: [
        { role: "system", content: "You are a helpful assistant." },
        { role: "user", content: userMessage }
      ]
    });

    const reply = completion.choices[0].message.content;

    return res.json({ reply });
  } catch (err) {
    console.error("Error:", err);
    return res.status(500).json({ reply: "Server Error 😢" });
  }
});

// 📌 6. شروع سرور
const PORT = 5000;
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});


