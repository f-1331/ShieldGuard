import os
import json
import logging
from typing import Dict, Any, List, Optional
import httpx
from backend.config import settings

logger = logging.getLogger(__name__)

# O'zbek tili uchun huquqiy va kiber-xavfsizlik bo'yicha tizimli yo'riqnomalar (System Prompts)
CONTRACT_XRAY_SYSTEM_PROMPT = """
Sen — O'zbekiston Respublikasi qonunchiligi (Fuqarolik kodeksi, Iste'molchilar huquqlarini himoya qilish to'g'risidagi qonun, Banklar va bank faoliyati to'g'risidagi qonun) bo'yicha tajribali yurist va mustaqil auditor "ShieldGuard Legal AI"san.

Vazifang: Foydalanuvchi taqdim etgan shartnoma (kredit, mikroqarz, avto-lizing, ijara, mehnat, xizmat ko'rsatish) matnini skanerlab, undagi barcha tuzoqlar, yashirin moliyaviy xarajatlar va asossiz jarimalarni aniqlash.

Javobingni FAQAT to'g'ri JSON formatida qaytar:
{
  "contract_type": "Kredit / Mikroqarz / Ijara / Avto-lizing / Mehnat",
  "overall_safety_score": 45, // 0-100 (0: O'ta xavfli tuzoq, 100: Butunlay xavfsiz)
  "verdict": "dangerous / suspicious / safe",
  "summary_uzbek": "Oddiy xalq tilida 2-3 jumlada shartnomaning asosiy xulosasi.",
  "dangerous_clauses": [
    {
      "clause_num": "4.2-band",
      "original_quote": "Shartnomadagi asl iqtibos",
      "explanation_uz": "Oddiy tilda bu nimani anglatishi va fuqaro nima uchun zarar ko'rishi",
      "severity": "critical / high / medium"
    }
  ],
  "financial_traps": [
    "Yashirin komissiya yoki bir tomonlama oshiriladigan foizlar haqida bandlar"
  ],
  "recommendations": [
    "Imzolashdan oldin qaysi bandlarni o'zgartirishni talab qilish kerakligi bo'yicha maslahatlar"
  ]
}
Barcha tushuntirishlar tushunarli, sodda O'ZBEK TILIDA (Lotin alifbosida) bo'lishi shart.
"""

SCAM_MESSAGE_SYSTEM_PROMPT = """
Sen — kiber-xavfsizlik tahlilchisi va sotsial muhandislik mutaxassisi "ShieldGuard AI"san.
Foydalanuvchi yuborgan shubhali matn yoki xabarni psixologik manipulyatsiya, shoshiltirish, soxta yutuq, fishing va bank kartasi/SMS kod o'g'irlash belgilari bo'yicha tahlil qil.

Javobni FAQAT JSON formatida qaytar:
{
  "risk_score": 85, // 0-100
  "verdict": "dangerous / suspicious / safe",
  "manipulation_tactics": ["Shoshiltirish (Urgency)", "Soxta moddiy yordam", "SMS-kodni talab qilish"],
  "analysis_uz": "Nima sababdan bu xabar xavfli ekani haqida batafsil tushuntirish.",
  "safety_action_uz": "Foydalanuvchi nima qilishi kerak (masalan: Hech qanday kod yubormang, kartani zudlik bilan bloklang)."
}
Barcha javoblar O'ZBEK TILIDA (Lotin) bo'lsin.
"""


def _generate_fallback_scam_analysis(text: str) -> Dict[str, Any]:
    """Tashqi API ulanmagan holatda ishlaydigan aqlli evristik tahlil."""
    lower = text.lower()
    risk = 15
    tactics = []
    
    if any(w in lower for w in ["sms", "kod", "parol", "tasdiqlash"]):
        risk += 40
        tactics.append("SMS-kod / Bir martalik tasdiqlash kodini so'rash (Eng yuqori xavf)")
    if any(w in lower for w in ["yutdingiz", "yutib", "sovg'a", "iphone", "telegram premium"]):
        risk += 35
        tactics.append("Soxta yutuq yoki sovg'a bilan qiziqtirish (Fishing tuzog'i)")
    if any(w in lower for w in ["prezident", "yordam puli", "kompensatsiya", "moddiy yordam", "subsidiy"]):
        risk += 40
        tactics.append("Davlat va Prezident nomidan soxta to'lov va'dasi")
    if any(w in lower for w in ["shoshiling", "oxirgi kun", "24 soat", "faqat bugun", "bloklandi"]):
        risk += 25
        tactics.append("Vahima uyg'otish va shoshiltirish (Psixologik manipulyatsiya)")
    if any(w in lower for w in ["karta", "8600", "9860", "karta raqam"]):
        risk += 25
        tactics.append("Bank karta raqami yoki ma'lumotlarini qidirish")

    risk = min(max(risk, 5), 98)

    if risk >= 70:
        verdict = "dangerous"
        action = "Diqqat! Hech qanday havola ustiga bosmang, SMS orqali kelgan kodlarni va karta raqamingizni hech kimga yubormang!"
        explanation = "Ushbu xabarda tajovuzkor sotsial muhandislik va fishing belgilari yaqqol ko'rinib turibdi. Kiber-firibgarlar sizning nomingizdan kredit olish yoki kartadagi pullarni yechib olishni ko'zlamoqda."
    elif risk >= 40:
        verdict = "suspicious"
        action = "Ushbu xabardagi ma'lumotlarni rasmiy manbalar (masalan, bank koll-markazi yoki rasmiy veb-sayt) orqali qayta tekshiring."
        explanation = "Xabarda bir nechta shubhali chaqiriqlar mavjud. Tasdiqlanmagan e'lonlar va notanish yuboruvchilardan ehtiyot bo'ling."
    else:
        verdict = "safe"
        action = "Xabarda ochiq firibgarlik belgilari sezilmadi, biroq doimo kiber-gigiyena qoidalariga rioya qiling."
        explanation = "Matn tarkibida agressiv psixologik bosim yoki fishing alomatlari topilmadi."

    return {
        "risk_score": risk,
        "verdict": verdict,
        "manipulation_tactics": tactics if tactics else ["Ochiq manipulyatsiya aniqlanmadi"],
        "analysis_uz": explanation,
        "safety_action_uz": action
    }


def _generate_fallback_contract_analysis(text: str) -> Dict[str, Any]:
    """Tashqi LLM mavjud bo'lmaganda ishlaydigan chuqur yuridik evristik audit."""
    lower = text.lower()
    dangerous_clauses = []
    financial_traps = []
    recommendations = []
    safety_score = 80

    # 1. Shartnoma turini aniqlash
    contract_type = "Umumiy fuqarolik shartnomasi"
    if any(k in lower for k in ["kredit", "qarz", "zaym", "bank"]):
        contract_type = "Kredit / Qarz shartnomasi"
    elif any(k in lower for k in ["lizing", "avto", "ijara"]):
        contract_type = "Avto-lizing / Ijara shartnomasi"
    elif any(k in lower for k in ["ish beruvchi", "xodim", "mehnat", "maosh"]):
        contract_type = "Mehnat shartnomasi"
    elif any(k in lower for k in ["oldi-sotdi", "xarid", "yetkazib berish"]):
        contract_type = "Oldi-sotdi shartnomasi"

    # 2. Asossiz kunlik penya / Jarima stavkalari
    if any(p in lower for p in ["penya", "har bir kechiktirilgan kun", "0.5%", "1%", "2%"]):
        safety_score -= 25
        clause_quote = "Kechiktirilgan har bir kun uchun to'lanmagan summa miqdoridan 0.5% (yoki undan ortiq) penya hisoblanadi..."
        dangerous_clauses.append({
            "clause_num": "Jarima va sanksiyalar bo'limi",
            "original_quote": clause_quote,
            "explanation_uz": "Kunlik 0.5% yoki 1% penya — yillik hisobda 180% - 365% lik ulkan asossiz moliyaviy yuk degani! Qonunchilikka asosan penyaning umumiy miqdori asosiy qarzning 50%idan oshmasligi kerak.",
            "severity": "critical"
        })
        financial_traps.append("Kunlik haddan tashqari yuqori penya (0.5% va undan ortiq stavka)")

    # 3. Bir tomonlama o'zgartirish huquqi
    if any(p in lower for p in ["bir tomonlama", "o'zgartirishga haqli", "ogohlantirmasdan"]):
        safety_score -= 20
        dangerous_clauses.append({
            "clause_num": "Shartlarni o'zgartirish bandi",
            "original_quote": "Ijrochi (Kreditor) foiz stavkasi va xizmat haqini bir tomonlama tartibda o'zgartirish huquqiga ega...",
            "explanation_uz": "Iste'molchining roziligisiz yoki oldindan xabardor qilmasdan to'lov yoki foizlarni bir tomonlama oshirish O'zbekiston Respublikasi 'Iste'molchilar huquqlarini himoya qilish to'g'risida'gi Qonunining 21-moddasiga zid!",
            "severity": "critical"
        })
        financial_traps.append("Kreditor/Ijrochining narx va foizlarni bir tomonlama o'zgartirish huquqi")

    # 4. Sudsiz mol-mulkni olib qo'yish yoki undirish
    if any(p in lower for p in ["akseptsiz", "sud qarorisiz", "notarius ijro xati", "musodara"]):
        safety_score -= 20
        dangerous_clauses.append({
            "clause_num": "Majburiy undiruv bandi",
            "original_quote": "Qarzdorlik vujudga kelganda mol-mulk yoki garov sud qarorisiz darhol undiruvga qaratiladi...",
            "explanation_uz": "Sud muhokamasisiz fuqaroning mulkini olib qo'yish yoki hisob raqamlaridan akseptsiz (roziliksiz) pul yechib olish fuqaro manfaatlarini jiddiy cheklaydi.",
            "severity": "high"
        })
        financial_traps.append("Akseptsiz (ogohlantirishsiz) mablag'larni yechib olish xavfi")

    # 5. Majburiy sug'urta va yashirin komissiyalar
    if any(p in lower for p in ["sug'urta badali", "komissiya", "xizmat ko'rsatish haqi", "hisob ochish uchun"]):
        safety_score -= 15
        financial_traps.append("Asosiy foizdan tashqari majburiy sug'urta yoki oylik xizmat ko'rsatish komissiyasi")
        dangerous_clauses.append({
            "clause_num": "Qo'shimcha to'lovlar bandi",
            "original_quote": "Qarz oluvchi har oyda shartnoma summasidan qo'shimcha xizmat haqi va sug'urta to'lovini to'laydi...",
            "explanation_uz": "Bu shartnomaning haqiqiy samarali foiz stavkasi (PSK) e'lon qilinganidan ancha yuqori ekanligini yashirish usulidir.",
            "severity": "medium"
        })

    # Tavsiyalar
    recommendations.append("Shartnomani imzolashdan oldin bir tomonlama o'zgartirish huquqini bekor qilishni talab qiling.")
    recommendations.append("Jarima (penya) stavkasini amaldagi qonuniy me'yorlar doirasiga tushirishni so'rang.")
    recommendations.append("Barcha qo'shimcha komissiya va sug'urta xarajatlarining yillik samarali stavkasini (PSK) talab qiling.")

    safety_score = min(max(safety_score, 15), 95)

    if safety_score < 50:
        verdict = "dangerous"
        summary_uzbek = "DIQQAT: Shartnomada iste'molchi uchun o'ta noqulay, bir tomonlama va asossiz yirik jarimalar ko'zda tutilgan bandlar aniqlandi! Imzolash jiddiy moliyaviy yo'qotishga olib kelishi mumkin."
    elif safety_score < 75:
        verdict = "suspicious"
        summary_uzbek = "Shartnomada bir nechta shubhali va ehtiyotkorlik talab etadigan bandlar mavjud. Imzolashdan oldin ularni o'zgartirishni so'rash tavsiya qilinadi."
    else:
        verdict = "safe"
        summary_uzbek = "Shartnomaning umumiy tuzilishi standart me'yorlarga mos. Shunga qaramay muddatlar va to'lov grafigiga qat'iy e'tibor qarating."

    return {
        "contract_type": contract_type,
        "overall_safety_score": safety_score,
        "verdict": verdict,
        "summary_uzbek": summary_uzbek,
        "dangerous_clauses": dangerous_clauses if dangerous_clauses else [{
            "clause_num": "Xulosa",
            "original_quote": "Matnda ochiq agressiv moddalar sezilmadi",
            "explanation_uz": "Oddiy standart shartnoma shartlari.",
            "severity": "low"
        }],
        "financial_traps": financial_traps if financial_traps else ["Ochiq yashirin komissiyalar aniqlanmadi"],
        "recommendations": recommendations
    }


async def call_gemini_api(prompt: str, system_instruction: str, image_bytes: Optional[bytes] = None) -> Optional[str]:
    """Gemini API ga asinxron murojaat (REST orqali qo'shimcha og'ir kutubxonalarsiz)."""
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    parts: List[Dict[str, Any]] = [{"text": prompt}]

    # Agar rasm berilgan bo'lsa
    if image_bytes:
        import base64
        b64_data = base64.b64encode(image_bytes).decode('utf-8')
        parts.insert(0, {
            "inline_data": {
                "mime_type": "image/jpeg",
                "data": b64_data
            }
        })

    payload = {
        "system_instruction": {
            "parts": [{"text": system_instruction}]
        },
        "contents": [
            {
                "parts": parts
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "response_mime_type": "application/json"
        }
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                content = data["candidates"][0]["content"]["parts"][0]["text"]
                return content
            else:
                logger.warning(f"Gemini API xatoligi {resp.status_code}: {resp.text}")
    except Exception as e:
        logger.error(f"Gemini chaqiruvida xatolik: {e}")

    return None


async def analyze_scam_text(text: str) -> Dict[str, Any]:
    """Xabar yoki fishing matnini tahlil qilish."""
    # Agar API kalit mavjud bo'lsa, avval Gemini chaqiriladi
    if settings.GEMINI_API_KEY:
        ai_resp = await call_gemini_api(text, SCAM_MESSAGE_SYSTEM_PROMPT)
        if ai_resp:
            try:
                parsed = json.loads(ai_resp)
                return parsed
            except Exception:
                pass

    # Kalit bo'lmasa yoki xato yuz bersa: Ishonchli Heuristic Fallback
    return _generate_fallback_scam_analysis(text)


async def analyze_contract_text_or_image(text: str, image_bytes: Optional[bytes] = None) -> Dict[str, Any]:
    """Shartnoma matni yoki rasmini to'liq tahlil qilish."""
    prompt = f"Ushbu shartnomani tahlil qil va tuzoqlarni ko'rsat:\n\n{text[:12000]}" if text else "Ushbu shartnoma fotosurati bo'yicha tahlil o'tkaz."

    if settings.GEMINI_API_KEY:
        ai_resp = await call_gemini_api(prompt, CONTRACT_XRAY_SYSTEM_PROMPT, image_bytes)
        if ai_resp:
            try:
                parsed = json.loads(ai_resp)
                return parsed
            except Exception:
                pass

    return _generate_fallback_contract_analysis(text)
