import io
import json
import logging
from typing import Dict, Any, Optional
from backend.config import settings

logger = logging.getLogger(__name__)

AUDIO_VISHING_SYSTEM_PROMPT = """
Sen — O'zbekiston kiber-xavfsizlik eksperti "ShieldGuard Voice AI"san.
Foydalanuvchi yuborgan audio yozuv (ovozli xabar yoki yozib olingan telefon qo'ng'irog'i)ni diqqat bilan eshitib, so'zma-so'z tahlil qil.

Tekshirish mezonlari:
1. SOTSIAL MUHANDISLIK VA SPOOFING:
   - O'zini bank xavfsizlik xizmati, to'lov tizimi (Click/Payme), tergovchi yoki mashhur shaxs deb tanishtirish;
2. KARTA VA SMS KOD TALAB QILISH:
   - Bank kartasi raqami, uning oxirgi raqamlari, CVV yoki SMS orqali kelgan tasdiqlash kodini aytishni so'rash;
3. SHOSHILINCH BOSIM VA VAHIMA:
   - "Kredit rasmiylashtirilmoqda", "Kartadan pul yechilmoqda", "Zudlik bilan to'xtatish kerak" deyish;
4. XAVFLI ILOVA:
   - AnyDesk, RustDesk, TeamViewer yoki APK o'rnatish talabi.

Agar audio shunchaki oddiy do'stona suhbat, oilaviy salom-alik yoki xavfsiz gaplar bo'lsa:
- risk_score: 0-15
- verdict: "safe"

Agar unda karta ma'lumotlari yoki SMS-kod so'ralgan bo'lsa:
- risk_score: 85-100
- verdict: "dangerous"

Javobni FAQAT to'g'ri JSON formatida qaytar:
{
  "transcribed_text": "Audioda aytilgan so'zlarning to'liq matni (O'zbek tilida)",
  "detected_type": "fake_bank_call / vishing / trojan_demand / normal_conversation",
  "risk_score": 0,
  "verdict": "safe / suspicious / dangerous",
  "scam_tactics": [
    "Aniqlangan tuzoqlar ro'yxati (agar mavjud bo'lsa)"
  ],
  "expert_verdict_uz": "Oddiy xalq tilida tahlil xulosasi.",
  "immediate_action_uz": "Tavsiya."
}
Barcha javoblar O'ZBEK TILIDA (Lotin) bo'lsin.
"""

AUDIO_HEURISTIC_KEYWORDS = [
    ("markaziy bank", 40, "Markaziy Bank nomidan soxta vakolat bilan gapirish"),
    ("xavfsizlik xizmati", 45, "Bank xavfsizlik xizmati niqobidan foydalanish"),
    ("nomingizga kredit", 45, "Nomingizga kredit rasmiylashtirilayotgani haqida vahima uyg'otish"),
    ("sms kod", 50, "SMS orqali kelgan tasdiqlash kodini aytishni talab qilish"),
    ("kodni ayting", 50, "Maxfiy bir martalik kodni so'rash"),
    ("kod boradi", 50, "SMS orqali boradigan tasdiqlash kodini so'rash"),
    ("kodni aytib yuboring", 50, "SMS tasdiqlash kodini aytishni talab qilish"),
    ("oxirgi 6ta", 50, "Karta raqamining oxirgi raqamlarini so'rash"),
    ("oxirgi raqam", 45, "Karta maxfiy rekvizitlarini talab qilish"),
    ("kartangizni oxirgi", 50, "Karta ma'lumotlarini to'plash"),
    ("kartangiz bloklandi", 40, "Kartangiz bloklangani haqida soxta ogohlantirish"),
    ("to'xtatib qolish", 35, "Operatsiyani to'xtatish bahonasida ma'lumot olish"),
    ("anydesk", 50, "AnyDesk masofaviy boshqaruv ilovasi talabi"),
    ("rustdesk", 50, "RustDesk masofaviy boshqaruv dasturi talabi"),
    ("tergovchi", 40, "IIV yoki prokuratura tergovchisi nomidan qo'rqitish")
]


async def analyze_audio_recording(
    filename: str,
    audio_bytes: bytes,
    mime_type: str = "audio/ogg",
    raw_transcript: Optional[str] = None
) -> Dict[str, Any]:
    """Audio yozuv (ovozli xabar / qo'ng'iroq) bo'yicha haqiqiy firibgarlik tahlili."""
    file_size_kb = len(audio_bytes) // 1024

    # 1. Agar Gemini API kaliti mavjud bo'lsa - Gemini Multimodal Audio tahlili
    from backend.security_engine.llm_engine import call_gemini_api, get_active_gemini_api_key
    active_api_key = await get_active_gemini_api_key()

    if active_api_key:
        try:
            prompt = (
                "Ushbu audio yozuvni (ovozli xabar yoki qo'ng'iroq yozuvi) diqqat bilan eshitib, "
                "so'zma-so'z to'liq transkripsiyasini qil va unda moliyaviy firibgarlik, karta raqami yoki "
                "SMS-kod o'g'irlash belgilari bor-yo'qligini aniqla."
            )
            ai_resp = await call_gemini_api(
                prompt=prompt,
                system_instruction=AUDIO_VISHING_SYSTEM_PROMPT,
                image_bytes=audio_bytes,
                mime_type=mime_type
            )
            if ai_resp:
                parsed = json.loads(ai_resp)
                return parsed
        except Exception as e:
            logger.warning(f"Audio AI tahlilida xatolik: {e}. Evristik tahlilga o'tilmoqda.")

    # 2. Agar transkripsiya / matn berilgan bo'lsa (yozma xabar yoki caption)
    if raw_transcript:
        risk_score = 0
        tactics = []
        lower_tr = raw_transcript.lower()
        for kw, score, desc in AUDIO_HEURISTIC_KEYWORDS:
            if kw in lower_tr:
                risk_score += score
                tactics.append(desc)

        risk_score = min(max(risk_score, 0), 100)
        verdict = "dangerous" if risk_score >= 70 else ("suspicious" if risk_score >= 40 else "safe")

        if verdict == "dangerous":
            expert = (
                "Suhbat matnida o'ta xavfli sotsial muhandislik va karta o'g'irlash belgilari fosh etildi! "
                "Karta raqamlari yoki SMS tasdiqlash kodini aytishni so'rash 100% kiber-o'g'irlikdir."
            )
            action = "DIQQAT! Suhbatni zudlik bilan to'xtating! Hech qanday SMS-kod yoki karta ma'lumotlarini bermang!"
        elif verdict == "suspicious":
            expert = "Suhbatda shubhali so'zlar qayd etildi. Moliyaviy masalalarda hushyor bo'ling."
            action = "Karta ma'lumotlarini begona shaxslarga bermang."
        else:
            expert = "Suhbat matnida hech qanday firibgarlik yoki shubhali belgilar aniqlanmadi. Audio xavfsiz."
            action = "Xavf yo'q."

        return {
            "detected_type": "voice_transcript_analysis",
            "transcribed_text": raw_transcript,
            "risk_score": risk_score,
            "verdict": verdict,
            "transcribed_summary": f"Matn tahlili: \"{raw_transcript[:120]}\"",
            "scam_tactics": tactics,
            "expert_verdict_uz": expert,
            "immediate_action_uz": action
        }

    # 3. AI kaliti yo'q va transkripsiya berilmagan holat:
    return {
        "detected_type": "audio_pending_ai_key",
        "transcribed_text": "",
        "risk_score": 0,
        "verdict": "untranscribed",
        "transcribed_summary": f"Ovozli xabar ({filename}, {file_size_kb} KB) qabul qilindi.",
        "scam_tactics": [],
        "expert_verdict_uz": (
            "⚠️ Ovozli xabarni so'zma-so'z o'qish (Speech-to-Text) uchun Google Gemini API kaliti ulanmagan.\n\n"
            "Bot egasi /setgemini <kalit> buyrug'i orqali bepul API kalitini kiritishi mumkin.\n"
            "Yoki audioda aytilgan gaplarni matn ko'rinishida yuborsangiz, bot darhol aniq tahlil qilib beradi."
        ),
        "immediate_action_uz": "Eslatma: Notanish qo'ng'iroqlarda hech kimga karta raqami yoki SMS-kod bermang."
    }
