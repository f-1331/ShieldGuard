import hashlib
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

def generate_evidence_hash(data: str) -> str:
    """Raqamli dalillarning kriptografik butunlik xeshini (SHA-256) hisoblaydi."""
    return hashlib.sha256(data.encode('utf-8')).hexdigest().upper()

def create_forensic_dossier(
    scan_id: Optional[int],
    user_id: int,
    target_name: str,
    threat_type: str,
    risk_score: float,
    details: Dict[str, Any]
) -> Dict[str, Any]:
    """IIV va Sud organlari uchun rasmiy Kiber-Ekspertiza Dalolatnomasini tuzadi."""
    tashkent_tz = timezone(timedelta(hours=5))
    now = datetime.now(tashkent_tz)
    timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S UTC+5")
    dossier_id = f"SG-EXP-{now.strftime('%Y%m%d')}-{scan_id or abs(hash(target_name)) % 100000:05d}"

    # Yuridik malakalash (O'zbekiston Respublikasi qonunchiligi bo'yicha)
    if risk_score >= 70:
        legal_qualification = (
            "O'zbekiston Respublikasi Jinoyat Kodeksining 168-moddasi (Firibgarlik) "
            "va 278-prim 1-moddasi (Axborot texnologiyalaridan foydalanib o'zganing mulkini talon-toroj qilish) "
            "alomatlari mavjud deb hisoblanadi."
        )
        recommendation_level = "CRITICAL / ZUDLIK BILAN HUQUQIY CHORA KO'RISH ZARUR"
    else:
        legal_qualification = (
            "O'zbekiston Respublikasi Ma'muriy Javobgarlik to'g'risidagi Kodeks yoki "
            "Iste'molchilar huquqlarini himoya qilish qonunchiligi buzilishi belgilari mavjud."
        )
        recommendation_level = "MONITORING VA EHTIYOTKORLIK"

    evidence_payload = f"{dossier_id}|{user_id}|{target_name}|{risk_score}|{timestamp_str}"
    integrity_hash = generate_evidence_hash(evidence_payload)

    # Rasmiy matn shakllantirish
    dossier_text = f"""
🏛️ <b>O'ZBEKISTON RESPUBLIKASI KIBERXAVFSIZLIK STANDARTLARI ASOSIDAGI DASTLABKI EKSPERTIZA DALOLATNOMASI</b>
═══════════════════════════════════════════
📄 <b>Hujjat raqami:</b> <code>{dossier_id}</code>
🕒 <b>Tuzilgan vaqti:</b> {timestamp_str}
🛡️ <b>Tahliliy tizim:</b> ShieldGuard AI Automated Forensic Engine v2.0
🔐 <b>Kriptografik SHA-256 xeshi:</b>
<code>{integrity_hash}</code>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 <b>1. KIBER-TAHDID NISHONI VA PARAMETRLARI:</b>
• Nishon obyekti: <code>{target_name[:80]}</code>
• Tahdid toifasi: <b>{threat_type.upper()}</b>
• Hisoblangan xavf darajasi: <b>{int(risk_score)}% / 100%</b>
• Jabrlanuvchi/Foydalanuvchi ID: <code>{user_id}</code>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚖️ <b>2. HUQUQIY MALAKALASH VA QONUN MODDALARI:</b>
{legal_qualification}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 <b>3. ANIQLANGAN RAQAMLI ISBOTLAR (IOCs):</b>
"""

    red_flags = details.get("red_flags", [])
    if red_flags:
        for idx, flag in enumerate(red_flags[:5], 1):
            dossier_text += f"{idx}. {flag}\n"
    else:
        dossier_text += "• Shubhali xatti-harakatlar va fishing andozalari qayd etildi.\n"

    # Agar karta ma'lumotlari bo'lsa
    if "card" in details or "clean_digits" in details:
        c_num = details.get("clean_digits") or details.get("card", {}).get("clean_digits", "")
        if c_num:
            dossier_text += f"\n💳 <b>Aloqador bank kartasi:</b> <code>{c_num[:4]} **** **** {c_num[-4:]}</code>\n"

    dossier_text += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 <b>4. TERGOV ORGANLARI VA BANKLAR UCHUN XULOSA:</b>
Ushbu dalolatnoma IIV Tezkor-qidiruv departamenti Kiberxavfsizlik markazi (cyber102.uz), tuman prokuraturasi yoki tijorat banklariga to'lovni bekor qilish (chargeback/bloklash) arizasiga ilova qilinishi mumkin.
Dalolatnomaning raqamli butunligi SHA-256 xeshi orqali kafolatlangan.
═══════════════════════════════════════════
"""

    return {
        "dossier_id": dossier_id,
        "timestamp": timestamp_str,
        "integrity_hash": integrity_hash,
        "target_name": target_name,
        "threat_type": threat_type,
        "risk_score": risk_score,
        "recommendation_level": recommendation_level,
        "legal_qualification": legal_qualification,
        "formatted_text": dossier_text.strip()
    }
