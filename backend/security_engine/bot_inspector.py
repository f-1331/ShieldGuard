import re
from typing import Dict, Any, List

OFFICIAL_UZ_BOTS = {
    "@clickuz": "Click O'zbekiston (Rasmiy bot)",
    "@paymeuz": "Payme O'zbekiston (Rasmiy bot)",
    "@uzumbank_bot": "Uzum Bank (Rasmiy)",
    "@soliq_uz_bot": "Davlat Soliq Qo'mitasi",
    "@mvd_uz_bot": "IIV Rasmiy boti",
    "@shieldguard_pro_bot": "ShieldGuard AI (Rasmiy himoya boti)"
}

SUSPICIOUS_BOT_PATTERNS = [
    (r"c[1l]ick[_\s-]*pay|c[1l]ick[_\s-]*bonus", "Click nomi bilan niqoblangan soxta to'lov boti"),
    (r"payme[_\s-]*bonus|payme[_\s-]*kredit|payme[_\s-]*yordam", "Payme nomidan soxta bonus yoki qarz va'da qiluvchi bot"),
    (r"uzum[_\s-]*aksiya|uzum[_\s-]*promokod", "Uzum nomidan soxta aksiya va'da qiluvchi bot"),
    (r"prezident[_\s-]*yordam|subsid[iy]", "Prezident nomidan bir martalik pul tarqatuvchi soxta bot"),
    (r"telegram[_\s-]*premium[_\s-]*bepul", "Telegram hisobni o'g'irlash uchun yaratilgan soxta bot"),
    (r"ovoz[_\s-]*berish|tanlov[_\s-]*ovoz", "Ovoz berish niqobida Telegram sessiya kodini o'g'irlash tuzog'i")
]


def analyze_telegram_bot_or_username(username: str) -> Dict[str, Any]:
    """Shubhali Telegram boti yoki foydalanuvchi nomini tahlil qilish."""
    clean = username.strip()
    if not clean.startswith("@"):
        clean = "@" + clean

    lower = clean.lower()

    if lower in OFFICIAL_UZ_BOTS:
        return {
            "target": clean,
            "is_official": True,
            "risk_score": 0,
            "verdict": "safe",
            "verdict_uz": "Rasmiy va Tasdiqlangan Bot",
            "summary_uz": f"Bu Telegramdagi rasmiy va tasdiqlangan bot: {OFFICIAL_UZ_BOTS[lower]}.",
            "flags": []
        }

    risk_score = 15
    flags = []

    for pattern, warning in SUSPICIOUS_BOT_PATTERNS:
        if re.search(pattern, lower):
            risk_score += 65
            flags.append(f"🚨 {warning}")

    if not lower.endswith("bot") and not lower.endswith("_bot"):
        flags.append("ℹ️ Bu Telegram bot emas, oddiy foydalanuvchi yoki guruh/kanal useri.")

    risk_score = min(max(risk_score, 0), 100)

    if risk_score >= 70:
        verdict = "dangerous"
        verdict_uz = "Kritik Xavfli! (Fishing Bot)"
        summary_uz = "Ushbu bot taniqli bank yoki davlat xizmatlari nomidan soxta tarzda foydalanmoqda. Unga telefon raqamingizni, Telegram orqali kelgan kodni yoki bank kartangizni ASLO kiritmang!"
    elif risk_score >= 40:
        verdict = "suspicious"
        verdict_uz = "Shubhali Bot"
        summary_uz = "Bot nomida shubhali belgilar mavjud. Foydalanishda hushyor bo'ling."
    else:
        verdict = "safe"
        verdict_uz = "Oddiy Bot"
        summary_uz = "Bot nomida ochiq firibgarlik belgilari topilmadi."

    return {
        "target": clean,
        "is_official": False,
        "risk_score": risk_score,
        "verdict": verdict,
        "verdict_uz": verdict_uz,
        "summary_uz": summary_uz,
        "flags": flags
    }
