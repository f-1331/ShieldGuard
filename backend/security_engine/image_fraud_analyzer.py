import io
import json
import logging
from typing import Dict, Any, Optional
from PIL import Image
from backend.config import settings

logger = logging.getLogger(__name__)

VISION_FRAUD_SYSTEM_PROMPT = """
Sen — O'zbekiston kiber-xavfsizlik eksperti va fotosuratlar bo'yicha mustaqil adolatli auditor "ShieldGuard Vision AI"san.
Foydalanuvchi taqdim etgan fotorasm yoki skrinshotni chuqur tahlil qil.

Tekshirish yo'nalishlari:
1. TO'LOV CHEKI (Click, Payme, Uzum Bank, Humo, Uzcard cheklari):
   - Chekdagi shriftlar bir-biriga mosmi yoki Photoshop/montaj qilinganmi?
   - Tranzaksiya vaqti, sana, to'lovchi va qabul qiluvchi rekvizitlari haqiqiymi?
   - "Soxta chek generatori" (Fake Check Bot) belgilari bormi?
2. SHARTNOMA MATNI (Kredit, lizing, ijara, xizmat ko'rsatish):
   - Asossiz kunlik penya (0.5%+), bir tomonlama foiz oshirish, akseptsiz yechib olish yoki garovni sudsiz tortib olish tuzoqlari bormi?
3. CHAT / SMS SKRINSHOTI (Telegram, SMS, OLX yozishmalari):
   - Yashirin avtospisanie, soxta yetkazib berish (dostavka), 1 so'mlik obuna, Telegram sessiya o'g'irlash yoki karta kodi so'ralganmi?
4. QR KOD YOKI BOSHQA TIZIMLAR:
   - Xavfli havolalar yoki fishing chaqiriqlari mavjudmi?

Javobni FAQAT quyidagi JSON formatida qaytar:
{
  "detected_type": "fake_receipt / legitimate_receipt / contract / chat_screenshot / other",
  "risk_score": 85, // 0-100 (0: Xavfsiz, 100: Kritik xavfli firibgarlik)
  "verdict": "dangerous / suspicious / safe",
  "title_uz": "Qisqa tushunarli sarlavha (masalan: Soxta Click to'lov cheki!)",
  "summary_uz": "Oddiy xalq tilida 2-3 jumlada tahlil xulosasi.",
  "red_flags": [
    "Aniqlangan shubhali belgilar (masalan: Montaj qilingan shrift, nostandart vaqt formati)"
  ],
  "recommendations": [
    "Foydalanuvchiga aniq maslahat (masalan: Kartangiz balansini tekshiring, bu soxta chek!)"
  ]
}
Barcha javoblar O'ZBEK TILIDA (Lotin) bo'lsin.
"""

def inspect_image_basic_metadata(img_bytes: bytes) -> Dict[str, Any]:
    """PIL orqali rasmning o'lchami, formati va asosiy parametrlarini tekshiradi."""
    try:
        with Image.open(io.BytesIO(img_bytes)) as img:
            width, height = img.size
            img_format = img.format or "JPEG"
            is_screenshot = (width in (1080, 720, 1440, 1170, 1284, 1290, 1179) or 
                             (height / max(width, 1)) > 1.8)
            return {
                "valid_image": True,
                "width": width,
                "height": height,
                "format": img_format,
                "is_likely_screenshot": is_screenshot
            }
    except Exception as e:
        return {
            "valid_image": False,
            "error": str(e)
        }

async def analyze_fraud_image(filename: str, img_bytes: bytes, mime_type: Optional[str] = "image/jpeg") -> Dict[str, Any]:
    """Multimodal fotosurat tahlili: Soxta cheklar, chat skrinshotlari, QR kodlar va shartnomalar."""
    meta = inspect_image_basic_metadata(img_bytes)
    if not meta.get("valid_image"):
        return {
            "detected_type": "unknown",
            "risk_score": 50,
            "verdict": "suspicious",
            "title_uz": "Noma'lum yoki shikastlangan fayl",
            "summary_uz": "Fayl haqiqiy tasvir emas yoki ochib bo'lmadi.",
            "red_flags": ["Tasvir formatini o'qib bo'lmadi."],
            "recommendations": ["Iltimos, ekrandan olingan toza skrinshot yoki aniq fotosurat yuboring."]
        }

    # 1. Agar Gemini API mavjud bo'lsa - Gemini Vision chaqiriladi
    from backend.security_engine.llm_engine import call_gemini_api, get_active_gemini_api_key
    active_api_key = await get_active_gemini_api_key()
    if active_api_key:
        try:
            prompt = (
                "Ushbu tasvirni diqqat bilan tekshir: bu soxta to'lov chekimi (Click, Payme, Uzum), "
                "yozishma/SMS skrinshotimi, shartnoma varag'imi yoki QR-kodmi? "
                "Undagi yashirin pul o'g'irlash yoki firibgarlik belgilarini aniqla."
            )
            ai_resp = await call_gemini_api(prompt, VISION_FRAUD_SYSTEM_PROMPT, image_bytes=img_bytes)
            if ai_resp:
                parsed = json.loads(ai_resp)
                return parsed
        except Exception as e:
            logger.warning(f"Vision API xatosi, evristik tahlilga o'tilmoqda: {e}")

    # 2. Heuristic Fallback (Offline rejim)
    # Tasvir parametrlariga qarab birlamchi xulosa
    is_shot = meta.get("is_likely_screenshot", False)
    
    return {
        "detected_type": "chat_screenshot" if is_shot else "document_photo",
        "risk_score": 35 if is_shot else 20,
        "verdict": "suspicious" if is_shot else "safe",
        "title_uz": "Ekran skrinshoti / Tasvir qabul qilindi",
        "summary_uz": "Fotosurat muvaffaqiyatli qabul qilindi. Agar bu to'lov cheki bo'lsa — mahsulotni berishdan oldin doimo bank ilovangizda (Click/Payme/Uzum) hisobingizga haqiqatda pul tushganini tekshiring!",
        "red_flags": [
            "⚠️ Soxta chekdan ehtiyot bo'ling: Xaridor ko'rsatgan rasmga emas, faqat bank ilovangizdagi haqiqiy balansga ishoning."
        ],
        "recommendations": [
            "Bank kartangizdagi kirim tarixini Click yoki Payme orqali tekshiring.",
            "Agar rasmda havolalar bo'lsa, ularni matn sifatida botga yuboring."
        ]
    }
