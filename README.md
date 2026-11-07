# 🛡️ SHIELDGUARD AI (Anti-Scam & Legal Shield)
> **Kiber-xavfsizlik, fishing filtri, APK troyan tahlili va yuridik shartnomalar rentgeni**
> Telegram Bot: **[@ShieldGuard_Pro_bot](https://t.me/ShieldGuard_Pro_bot)** | Telegram Mini App (WebApp)

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Ff-1331%2FShieldGuard)
[![GitHub Repository](https://img.shields.io/badge/GitHub-Repository-blue?logo=github)](https://github.com/f-1331/ShieldGuard)

---

## 📌 Loyiha haqida
**ShieldGuard AI** — O'zbekiston fuqarolarini va ularning oila a'zolarini onlayn firibgarliklar (fishing, ijtimoiy muhandislik), zararli APK ilovalar (troyanlar, soxta taklifnomalar) va iste'molchi uchun asossiz og'ir bo'lgan yuridik shartnoma tuzoqlaridan (kredit, nasiya, ijara, lizing) himoya qilish uchun ishlab chiqilgan keng qamrovli kiber-qalqondir.

Barcha foydalanuvchi interfeysi, bot xabarlari, tahlil va ogohlantirishlar **O'zbek tilida (Lotin alifbosida)** tayyorlangan.

---

## 🚀 ASOSIY IMKONIYATLAR (CORE FEATURES)

### 1. 🔍 Chuqur Havola va Fishing Skaneri (`/api/scan/url-or-text`)
- **Typosquatting & Brend soxtalashtirish:** O'zbekistonning mashhur to'lov tizimlari (`Click`, `Payme`, `Uzum`, `Humo`, `Uzcard`) va davlat portallarini (`gov.uz`, `my.gov.uz`, `soliq.uz`) qalbakilashtiruvchi soxta domenlarni (masalan: `c1ick-uz.com`, `payme-bonus.ru`, `uzum-market.site`) aniqlaydi.
- **Xavfsiz redirect monitoringi:** Qisqartirilgan havolalarni (bit.ly, t.me, tinyurl) xavfsiz ochib, oxirgi manzilni tekshiradi.
- **HTML Shakllar Inspeksiyasi:** Norasmiy saytda parol, bank karta raqami yoki eng xavflisi — **SMS tasdiqlash kodini** kiritish maydoni mavjudligini aniqlab, darhol bloklaydi.
- **Psixologik manipulyatsiya tahlili:** "Prezident yordam puli", "10,000,000 so'm yutdingiz", "Shoshiling, hisobingiz bloklandi" kabi soxta vijdonsiz chaqiriqlarni fosh qiladi.

### 2. 📦 APK & Fayllar Malvar Tahlili (`/api/scan/file`)
- **Ikki qavatli kengaytmalar:** Telegramda rasm yoki PDFdek ko'rinuvchi xavfli fayllarni (masalan: `To'y taklifnomasi.pdf.apk`, `foto.jpg.exe`) fosh qiladi.
- **Android Ruxsatlari Rentgeni:** `.apk` fayli ichidan `AndroidManifest.xml` ruxsatlarini o'qib, o'ta xavfli troyan belgilarini ochib beradi:
  - `BIND_ACCESSIBILITY_SERVICE` (Ekrandagi barcha ma'lumotlarni o'qish va foydalanuvchisiz pul o'tkazish);
  - `RECEIVE_SMS` / `READ_SMS` (Bankdan kelgan bir martalik tasdiqlash kodlarini o'g'irlash);
  - `SYSTEM_ALERT_WINDOW` (Click/Payme ustiga soxta ekran chiqarib karta ma'lumotlarini o'g'irlash).

### 3. 📄 Shartnoma Rentgeni — Legal X-Ray (`/api/scan/contract`)
- Kredit, mikroqarz, muddatli to'lov (nasiya), avto-lizing yoki ijara shartnomalarining **PDF** fayllari yoki suratlarini skanerlaydi.
- **Predator (Yirtqich) moddalar:**
  - Kunlik haddan tashqari yuqori penya (masalan, 0.5% - 1% kunlik jarima);
  - Bank yoki ijrochining narx va foizlarni bir tomonlama oshirish huquqi;
  - Sud qarorisiz mol-mulkni akseptsiz musodara qilish moddalari;
  - Yashirin sug'urta va oylik xizmat ko'rsatish komissiyalari.
- Natijani sodda, oddiy xalq tilida O'zbekcha xulosa va aniq tavsiyalar bilan taqdim etadi.

### 4. 👨‍👩‍👧‍👦 Oila Qalqoni (Family Shield)
- Oila a'zolarini (masalan, keksaroq ota-onangizni) Telegram ID orqali himoyaga ulash imkoniyati.
- Agar ota-onangiz xavfli fishing havolani yoki virusli `.apk` faylini skanerlasa yoki unga duch kelsa, vasiyga (farzandiga) bot orqali **zudlik bilan shoshilinch signal (Alert)** yuboriladi!

### 5. 🚫 Umumiy Qora Ro'yxat (Community Blacklist)
- Foydalanuvchilar duch kelgan yangi firibgar manzil, bot yoki fishing saytlarni xabar qilishlari mumkin.
- Tasdiqlangan barcha scam manbalar real vaqtda umumiy ma'lumotlar bazasida saqlanadi.

---

## 🛠️ TEXNOLOGIK STACK
- **Backend:** Python 3.11+, FastAPI, Uvicorn, Aiogram 3.x, Pydantic v2, HTTPX.
- **Database:** SQLite (Asyncio / aiosqlite, SQLAlchemy 2.0).
- **Security Engine:**
  - Heuristic Regex & Domain Typosquatting / Levenshtein Distance Calculator.
  - APK Binary XML / Manifest Inspector.
  - Multi-provider AI Engine (Google Gemini API / OpenAI API / Uzbek Heuristic Fallback Engine).
- **Frontend / Mini App:** HTML5, TailwindCSS, Vanilla JS, Telegram WebApp SDK, SVG Risk Gauges.

---

## 📂 LOYIHA TUZILISHI
```
ShieldGuard/
├── backend/
│   ├── config.py                 # Sozlamalar va .env yuklagich
│   ├── database.py               # SQLite Async ulanishi
│   ├── models.py                 # User, FamilyLink, ScanHistory, CommunityBlacklist modellari
│   ├── utils.py                  # Telegram API orqali tezkor oila signallari
│   ├── telegram_bot.py           # Aiogram 3 Telegram Bot boshqaruvi
│   ├── main.py                   # FastAPI server va WebApp integratsiyasi
│   ├── run.py                    # Server va Botni birgalikda ishga tushiruvchi skript
│   ├── routers/
│   │   ├── scan.py               # Tekshiruv API (URL, Fayl, Shartnoma)
│   │   ├── family.py             # Oila a'zolarini ulash va boshqarish API
│   │   ├── community.py          # Firibgarliklarni xabar qilish va qora ro'yxat
│   │   └── history.py            # Foydalanuvchi tarixi va umumiy statistika
│   └── security_engine/
│       ├── url_analyzer.py       # Typosquatting, fishing, domenlar tahlili
│       ├── apk_analyzer.py       # APK troyanlar va xavfli ruxsatlar detektori
│       ├── contract_analyzer.py  # PDF/Matn shartnomalar rentgeni
│       └── llm_engine.py         # Gemini API / Fallback aqlli tahlil
├── frontend/
│   ├── index.html                # Telegram Mini App asosiy oynasi (Dark Cyber UI)
│   ├── css/
│   │   └── style.css             # Neon, shisha effekti (glassmorphism) va animatsiyalar
│   ├── js/
│   │   ├── app.js                # Telegram WebApp SDK va tablar boshqaruvi
│   │   ├── scanner.js            # Havola va fayl skaneri, risk o'lchagich
│   │   ├── legal.js              # Shartnoma rentgeni vizualizatsiyasi
│   │   └── family.js             # Oila qalqoni, tarix va qora ro'yxat
│   └── assets/
│       └── logo.svg              # ShieldGuard logotipi
├── test_shieldguard.py           # Avtomatlashtirilgan to'liq test ssenariylari
├── .env                          # Muhit o'zgaruvchilari (Bot token kiritilgan)
├── .env.example                  # Namuna konfiguratsiya
└── requirements.txt              # Kutubxonalar ro'yxati
```

---

## ⚙️ O'RNATISH VA ISHGA TUSHIRISH (INSTALLATION & RUN)

### 1. Talablar:
- Python 3.11 yoki undan yuqori versiya.

### 2. Kutubxonalarni o'rnatish:
Terminalda loyiha papkasiga kiring va buyruqni bajaring:
```bash
pip install -r requirements.txt
```

### 3. Konfiguratsiya (.env):
Loyiha papkasidagi `.env` faylida Telegram bot tokeni allaqachon sozlangan:
```env
TELEGRAM_BOT_TOKEN=9237470345:AAFK862jqEqgWrgXCAqZ2TAL6EZLnC8tC_w
TELEGRAM_BOT_USERNAME=ShieldGuard_Pro_bot
WEBAPP_URL=http://localhost:8000

# Agar Gemini API kalitingiz bo'lsa kiriting (kiritilmasa ham Demo Heuristic rejimida to'liq ishlaydi):
GEMINI_API_KEY=
```

### 4. Testlarni ishga tushirib tekshirish:
```bash
python test_shieldguard.py
```

### 5. Server va Telegram Botni ishga tushirish:
Yagona buyruq orqali ham FastAPI Web server, ham Telegram Bot fonga ulanadi:
```bash
python backend/run.py
```

Ishga tushgach:
- **API va WebApp manzili:** `http://localhost:8000` (yoki `http://localhost:8000/webapp`)
- **API Swagger Hujjatlari:** `http://localhost:8000/docs`
- **Telegram Bot:** Telegram ilovasida **[@ShieldGuard_Pro_bot](https://t.me/ShieldGuard_Pro_bot)** ni oching va `/start` tugmasini bosing!

---

## 🌐 TELEGRAM MINI APP (WEBAPP) SOZLASH
Agar bot ichidagi "🛡️ Ilovada ochish (Mini App)" tugmasini real telefoningizda ochmoqchi bo'lsangiz:
1. Serverni tashqi internetga ochish uchun `ngrok` yoki bepul tunnellardan foydalaning:
   ```bash
   ngrok http 8000
   ```
2. Olingan `https://xxxx.ngrok-free.app` manzilini `.env` faylidagi `WEBAPP_URL` qatoriga yozing:
   ```env
   WEBAPP_URL=https://xxxx.ngrok-free.app
   ```
3. `@BotFather` orqali o'z botingizga Menu Button yoki Web App URL sifatida ushbu manzilni belgilang.

---

## 📡 ASOSIY REST API NUQTALARI

| Metod | Yo'l | Tavsif |
|---|---|---|
| `POST` | `/api/scan/url-or-text` | Havola yoki matnli firibgarlikni skanerlash |
| `POST` | `/api/scan/file` | APK yoki shubhali fayllarni tekshirish |
| `POST` | `/api/scan/contract` | Shartnomani (PDF/Surat/Matn) rentgen qilish |
| `POST` | `/api/family/link` | Oila a'zosini himoyaga ulash |
| `GET` | `/api/family/{telegram_id}` | Ulangan yaqinlar ro'yxati |
| `GET` | `/api/history/{telegram_id}` | Tekshiruvlar tarixi |
| `GET` | `/api/community/blacklist` | Umumiy firibgarliklar qora ro'yxati |
| `POST` | `/api/community/report` | Yangi firibgarlikni hisobot qilish |
| `GET` | `/api/stats` | Tizim statistikasi |

---
**ShieldGuard AI** — Siz va oilangiz xavfsizligi ishonchli himoya ostida! 🇺🇿🛡️
