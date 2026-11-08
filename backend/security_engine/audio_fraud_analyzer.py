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
    ("kod boradi", 50, "SMS orqali boradigan bir martalik tasdiqlash kodini talab qilish"),
    ("kodni aytib yuboring", 50, "SMS tasdiqlash kodini aytishni talab qilish"),
    ("oxirgi 6ta", 50, "Karta raqamining oxirgi 6 ta raqamini so'rash (Karta o'g'irlash)"),
    ("oxirgi raqam", 45, "Karta maxfiy rekvizitlarini talab qilish"),
    ("kartangizni oxirgi", 50, "Karta ma'lumotlarini to'plash"),
    ("kartangiz bloklandi", 40, "Kartangiz bloklangani haqida soxta ogohlantirish"),
    ("to'xtatib qolish", 35, "Operatsiyani to'xtatish bahonasida ma'lumot olish"),
    ("anydesk", 50, "Qurilmani masofadan boshqaruvchi xavfli ilova (AnyDesk) o'rnatish talabi"),
    ("rustdesk", 50, "Masofaviy boshqaruv dasturi (RustDesk) talabi"),
    ("tergovchi", 40, "IIV yoki prokuratura tergovchisi nomidan qo'rqitish"),
    ("jahongir otajonov", 45, "Mashhur shaxs (Jahongir Otajonov) nomidan soxta shaxsiyat / Deepfake"),
    ("otajonov", 40, "Mashhur san'atkor nomidan manipulyatsiya qilish")
]

async def analyze_audio_recording(
    filename: str,
    audio_bytes: bytes,
    mime_type: str = "audio/ogg",
    raw_transcript: Optional[str] = None
) -> Dict[str, Any]:
    """Audio yozuv (ovozli xabar / qo'ng'iroq) bo'yicha firibgarlik tahlili."""
    file_size_kb = len(audio_bytes) // 1024

    # 1. Agar Gemini API kaliti mavjud bo'lsa (Config yoki Neon DB orqali) - Multimodal Audio tahlili
    from backend.security_engine.llm_engine import call_gemini_api, get_active_gemini_api_key
    active_api_key = await get_active_gemini_api_key()

    if active_api_key:
        try:
            prompt = (
                "Ushbu audio yozuvni (ovozli xabar yoki yozib olingan qo'ng'iroq) diqqat bilan eshitib, "
                "so'zma-so'z tahlil qil. "
                "Agar unda o'zini mashhur shaxs (san'atkor Jahongir Otajonov, bloger) yoki bank/IIV xodimi "
                "deb tanishtirib, kartaning raqamlarini, oxirgi 6 ta raqamini yoki SMS-kodni aytishni "
                "so'rashgan bo'lsa — bu 100% KRITIK XAVFLI FIRIBGARLIKDIR! "
                "Barcha firibgarlik taktikalari va xavf darajasini (0-100) aniqla."
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

    # 2. Heuristic Audio Fallback (Offline rejim yoki matn orqali)
    risk_score = 75  # Default to high alert for unverified audio calls
    tactics = []
    
    # Agar transkripsiya / matn berilgan bo'lsa
    if raw_transcript:
        risk_score = 20
        lower_tr = raw_transcript.lower()
        for kw, score, desc in AUDIO_HEURISTIC_KEYWORDS:
            if kw in lower_tr:
                risk_score += score
                tactics.append(desc)

        risk_score = min(max(risk_score, 10), 100)
        verdict = "dangerous" if risk_score >= 70 else ("suspicious" if risk_score >= 40 else "safe")

        if verdict == "dangerous":
            expert = (
                f"Suhbat matnida o'ta xavfli sotsial muhandislik va karta o'g'irlash belgilari aniqlandi! "
                f"Karta raqamlari yoki SMS tasdiqlash kodini so'rash Jinoyat Kodeksining 168-moddasi bilan jazolanadigan og'ir jinoyatdir."
            )
            action = "DIQQAT! Suhbatni zudlik bilan to'xtating! Hech qanday SMS-kod yoki karta raqamini aytmang!"
        else:
            expert = "Suhbat matnida to'g'ridan-to'g'ri firibgarlik belgilari aniqlanmadi, ammo notanish shaxslar bilan ehtiyot bo'ling."
            action = "Moliyaviy ma'lumotlarni hech kimga bermang."

        return {
            "detected_type": "voice_transcript_analysis",
            "risk_score": risk_score,
            "verdict": verdict,
            "transcribed_summary": f"Suhbat matni tahlil qilindi: \"{raw_transcript[:100]}\"",
            "scam_tactics": tactics,
            "expert_verdict_uz": expert,
            "immediate_action_uz": action
        }

    # Transkripsiya bo'lmaganda (Oddiy audio xabar kelganda)
    tactics = [
        "Ovozli xabar / Telefon qo'ng'irog'i qabul qilindi",
        "Diqqat: Karta oxirgi 6 ta raqami va SMS-kodni so'rash — 100% o'g'irlik!",
        "Mashhur san'atkorlar (Jahongir Otajonov va h.k.) yoki bank xodimi nomidan soxta murojaat xavfi"
    ]
    if file_size_kb > 150:
        tactics.append("Davomiyligi uzoq bo'lgan suhbat yozuvi.")

    action = (
        "DIQQAT! Agar ushbu ovozli xabarda sizdan: KARTA RAQAMI, SMS-KOD, yoki biror ILAVANI O'RNATISH "
        "so'ralgan bo'lsa — darhol go'shakni qo'ying! Bu 100% kiber-firibgarlikdir!"
    )
    expert = (
        "Ovozli xabar qabul qilindi. AI to'liq audio eshitish rejimi ulanmaganligi sababli, "
        "har qanday moliyaviy talabni kritik xavfli deb hisoblang. "
        "O'zini Jahongir Otajonov yoki bank xodimi deb tanishtirib kod so'ragan shaxslarga aslo ishonmang!"
    )

    return {
        "detected_type": "voice_recording_unverified",
        "risk_score": 85,
        "verdict": "dangerous",
        "transcribed_summary": f"Ovozli xabar ({filename}, {file_size_kb} KB) qabul qilindi.",
        "scam_tactics": tactics,
        "expert_verdict_uz": expert,
        "immediate_action_uz": action
    }
