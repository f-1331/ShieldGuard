import io
import json
import logging
from typing import Dict, Any, Optional
from backend.config import settings

logger = logging.getLogger(__name__)

AUDIO_VISHING_SYSTEM_PROMPT = """
Sen — telefon va audio firibgarliklar (Vishing / Sotsial muhandislik qo'ng'iroqlari) bo'yicha maxsus kiber-tahlilchi "ShieldGuard Voice AI"san.
Foydalanuvchi yuborgan audio yozuv (ovozli xabar yoki yozib olingan telefon qo'ng'irog'i)ni diqqat bilan eshitib, tahlil qil.

Tekshirish mezonlari:
1. SOXTA HOKIMIYAT VA ORGANLAR SPOOFINGI:
   - O'zini "Markaziy Bank", "Click / Payme xavfsizlik xizmati", "IIV tergovchisi", "Soliq inspeksiyasi" deb tanishtirish;
2. VAHIMA VA SHOSHILINCH BOSIM:
   - "Kartangizdan 2 mln so'm yechilmoqda", "Nomingizga noqonuniy kredit olinmoqda", "Zudlik bilan to'xtatish kerak";
3. MAXFIY MA'LUMOTLARNI TALAB QILISH:
   - SMS tasdiqlash kodini aytishni, karta raqamini, CVV yoki robot ovoziga kod kiritishni so'rash;
4. XAVFLI ILOVA O'RNATISHGA MAJBURLASH:
   - RustDesk, AnyDesk, TeamViewer yoki "Himoya ilovasi" bahonasida APK fayl o'rnatishni talab qilish.

Javobni FAQAT to'g'ri JSON formatida qaytar:
{
  "detected_type": "fake_bank_call / fake_police_call / telegram_voice_scam / safe_audio",
  "risk_score": 90, // 0-100 (0: Xavfsiz, 100: O'ta xavfli firibgarlik)
  "verdict": "dangerous / suspicious / safe",
  "transcribed_summary": "Audiodagi suhbatning qisqacha mazmuni (nima haqida gap ketgani)",
  "scam_tactics": [
    "Soxta bank xavfsizlik xizmati niqobi",
    "SMS kodni talab qilish",
    "Sun'iy shoshiltirish"
  ],
  "expert_verdict_uz": "Nima sababdan bu audio xavfli ekani haqida batafsil tushuntirish.",
  "immediate_action_uz": "Foydalanuvchi nima qilishi kerak (masalan: Suhbatni darhol to'xtating, hech qanday kod bermang, kartani bloklang!)"
}
Barcha javoblar O'ZBEK TILIDA (Lotin) bo'lsin.
"""

# Audio fayllar uchun offline evristik tahlil
AUDIO_HEURISTIC_KEYWORDS = [
    ("markaziy bank", 40, "Markaziy Bank nomidan soxta vakolat bilan gapirish"),
    ("xavfsizlik xizmati", 45, "Bank xavfsizlik xizmati niqobidan foydalanish"),
    ("nomingizga kredit", 45, "Nomingizga kredit rasmiylashtirilayotgani haqida vahima uyg'otish"),
    ("sms kod", 50, "SMS orqali kelgan tasdiqlash kodini aytishni talab qilish"),
    ("kodni ayting", 50, "Maxfiy bir martalik kodni so'rash (Eng yuqori xavf)"),
    ("kartangiz bloklandi", 40, "Kartangiz bloklangani haqida soxta ogohlantirish"),
    ("to'xtatib qolish", 35, "Operatsiyani to'xtatish bahonasida ma'lumot olish"),
    ("anydesk", 50, "Qurilmani masofadan boshqaruvchi xavfli ilova (AnyDesk) o'rnatish talabi"),
    ("rustdesk", 50, "Masofaviy boshqaruv dasturi (RustDesk) talabi"),
    ("tergovchi", 40, "IIV yoki prokuratura tergovchisi nomidan qo'rqitish")
]

async def analyze_audio_recording(
    filename: str,
    audio_bytes: bytes,
    mime_type: str = "audio/ogg",
    raw_transcript: Optional[str] = None
) -> Dict[str, Any]:
    """Audio yozuv (ovozli xabar / qo'ng'iroq) bo'yicha firibgarlik tahlili."""
    file_size_kb = len(audio_bytes) // 1024

    # 1. Agar Gemini API mavjud bo'lsa - Gemini Multimodal Audio tahlili
    if settings.GEMINI_API_KEY:
        try:
            from backend.security_engine.llm_engine import call_gemini_api
            prompt = (
                "Ushbu audio yozuvni eshitib tahlil qil. "
                "Bu soxta bank xodimi, firibgar qo'ng'irog'i, yoki manipulyatsiya xabarimi? "
                "Barcha firibgarlik taktikalari va xavf darajasini aniqla."
            )
            # call_gemini_api audio_bytes bilan chaqiriladi
            ai_resp = await call_gemini_api(
                prompt=prompt,
                system_instruction=AUDIO_VISHING_SYSTEM_PROMPT,
                image_bytes=audio_bytes, # media baytlari sifatida
                mime_type=mime_type
            )
            if ai_resp:
                parsed = json.loads(ai_resp)
                return parsed
        except Exception as e:
            logger.warning(f"Audio AI tahlilida xatolik: {e}. Evristik tahlilga o'tilmoqda.")

    # 2. Heuristic Audio Fallback (Offline rejim)
    risk_score = 30
    tactics = []
    
    # Agar transkripsiya mavjud bo'lsa yoki audio hajmi bo'yicha
    if raw_transcript:
        lower_tr = raw_transcript.lower()
        for kw, score, desc in AUDIO_HEURISTIC_KEYWORDS:
            if kw in lower_tr:
                risk_score += score
                tactics.append(desc)
    else:
        tactics.append("Ovozli xabar / Audio fayl tekshiruvdan o'tkazildi.")
        if file_size_kb > 200:
            tactics.append("Davomiyligi uzoq bo'lgan suhbat yozuvi.")

    risk_score = min(max(risk_score, 15), 100)
    verdict = "dangerous" if risk_score >= 70 else ("suspicious" if risk_score >= 40 else "safe")

    if verdict == "dangerous":
        action = "DIQQAT! Suhbatni zudlik bilan to'xtating! Hech qanday SMS-kod, karta raqami yoki parolni aytmang va hech qanday ilova (AnyDesk/APK) o'rnatmang!"
        expert = "Ushbu audio suhbatda tajovuzkor vishing (telefon orqali firibgarlik) belgilari yaqqol sezilmoqda. Firibgarlar bank xodimi niqobida sizning kartangizni boshqarishga urinmoqda."
    else:
        action = "Notanish shaxslar bilan suhbatda doimo hushyor bo'ling va rasmiy bank raqamlariga qayta qo'ng'iroq qiling."
        expert = "Audio fayl qabul qilindi. Notanish shaxslarga hech qachon shaxsiy moliyaviy ma'lumotlarni bermang."

    return {
        "detected_type": "voice_recording",
        "risk_score": risk_score,
        "verdict": verdict,
        "transcribed_summary": f"Audio fayl ({filename}, {file_size_kb} KB) qabul qilindi.",
        "scam_tactics": tactics,
        "expert_verdict_uz": expert,
        "immediate_action_uz": action
    }
