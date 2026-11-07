import re
from typing import Dict, Any, Optional

# O'zbekiston banklari BIN (Bank Identification Number) ma'lumotlar bazasi
UZBEK_CARD_BINS = {
    "8600": {"system": "Uzcard", "type": "Milliy to'lov tizimi (So'm)", "bank": "Uzcard to'lov tizimi (O'zbekiston)"},
    "860002": {"system": "Uzcard", "type": "Debet", "bank": "Xalq Banki ATB"},
    "860004": {"system": "Uzcard", "type": "Debet", "bank": "Agrobank ATB"},
    "860005": {"system": "Uzcard", "type": "Debet", "bank": "Milliy Bank (NBU)"},
    "860006": {"system": "Uzcard", "type": "Debet", "bank": "Sanoat Qurilish Bank (SQB)"},
    "860014": {"system": "Uzcard", "type": "Debet", "bank": "Kapitalbank ATB"},
    "860031": {"system": "Uzcard", "type": "Debet", "bank": "Ipak Yo'li Banki"},
    "860033": {"system": "Uzcard", "type": "Debet", "bank": "Hamkorbank ATB"},
    "860049": {"system": "Uzcard", "type": "Debet", "bank": "Anorbank AJ"},
    "860055": {"system": "Uzcard", "type": "Debet", "bank": "Uzum Bank (Apelsin)"},
    "9860": {"system": "Humo", "type": "Milliy kontaktsiz to'lov tizimi (So'm)", "bank": "Humo to'lov tizimi (O'zbekiston)"},
    "986001": {"system": "Humo", "type": "Debet / Kontaktsiz", "bank": "Xalq Banki ATB"},
    "986002": {"system": "Humo", "type": "Debet / Kontaktsiz", "bank": "Agrobank ATB"},
    "986003": {"system": "Humo", "type": "Debet / Kontaktsiz", "bank": "Milliy Bank (NBU)"},
    "986008": {"system": "Humo", "type": "Debet / Kontaktsiz", "bank": "Kapitalbank ATB"},
    "986012": {"system": "Humo", "type": "Debet / Kontaktsiz", "bank": "Ipak Yo'li Banki"},
    "986016": {"system": "Humo", "type": "Debet / Kontaktsiz", "bank": "Hamkorbank ATB"},
    "986024": {"system": "Humo", "type": "Debet / Kontaktsiz", "bank": "TBC Bank O'zbekiston"},
    "986035": {"system": "Humo", "type": "Debet / Kontaktsiz", "bank": "Anorbank AJ"},
    "986060": {"system": "Humo", "type": "Debet / Kontaktsiz", "bank": "Uzum Bank"},
}


def luhn_checksum_valid(card_number: str) -> bool:
    """Luhn algoritmi orqali bank kartasi raqamining matematik to'g'riligini tekshirish."""
    digits = [int(d) for d in card_number if d.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False

    checksum = 0
    reverse_digits = digits[::-1]
    for i, d in enumerate(reverse_digits):
        if i % 2 == 1:
            doubled = d * 2
            checksum += doubled - 9 if doubled > 9 else doubled
        else:
            checksum += d

    return checksum % 10 == 0


def analyze_card_number(raw_card: str) -> Dict[str, Any]:
    """Bank kartasi raqamini tahlil qilish, emitent bankni aniqlash va xavfni baholash."""
    # Probel va tire belgilarini tozalash
    clean_num = re.sub(r'[\s\-_]', '', raw_card)

    if not clean_num.isdigit():
        return {
            "valid_format": False,
            "error_uz": "Karta raqami faqat raqamlardan iborat bo'lishi kerak.",
            "risk_score": 50,
            "verdict": "suspicious"
        }

    length = len(clean_num)
    if length != 16:
        return {
            "valid_format": False,
            "error_uz": f"Karta raqami uzunligi noto'g'ri ({length} ta raqam). Odatda 16 ta raqam bo'ladi.",
            "risk_score": 60,
            "verdict": "suspicious"
        }

    is_luhn_valid = luhn_checksum_valid(clean_num)

    # Tizim va bankni aniqlash
    system = "Noma'lum"
    bank = "Noma'lum bank"
    card_type = "Standart"

    # 6 talik BIN tekshirish
    bin_6 = clean_num[:6]
    bin_4 = clean_num[:4]

    if bin_6 in UZBEK_CARD_BINS:
        info = UZBEK_CARD_BINS[bin_6]
        system = info["system"]
        bank = info["bank"]
        card_type = info["type"]
    elif bin_4 in UZBEK_CARD_BINS:
        info = UZBEK_CARD_BINS[bin_4]
        system = info["system"]
        bank = info["bank"]
        card_type = info["type"]
    elif clean_num.startswith("4"):
        system = "Visa International"
        bank = "Xalqaro Visa kartasi (O'zbekiston yoki xorij)"
        card_type = "Xalqaro valyuta"
    elif clean_num.startswith(("51", "52", "53", "54", "55", "22", "23", "24", "25", "26", "27")):
        system = "Mastercard"
        bank = "Xalqaro Mastercard kartasi"
        card_type = "Xalqaro valyuta"
    elif clean_num.startswith("62"):
        system = "UnionPay"
        bank = "UnionPay xalqaro kartasi"

    # Maskalangan ko'rinish: 8600 12** **** 9012
    masked = f"{clean_num[:4]} {clean_num[4:6]}** **** {clean_num[-4:]}"

    risk_score = 0
    warnings = []
    recommendations = []

    if not is_luhn_valid:
        risk_score = 75
        warnings.append("🚨 Karta nazorat summasi (Luhn algoritmi) mos kelmadi! Bu sun'iy yaratilgan qalbaki karta raqami bo'lishi mumkin.")
    else:
        recommendations.append("Karta raqami formati va nazorat raqami to'g'ri.")

    if system == "Noma'lum":
        risk_score = max(risk_score, 45)
        warnings.append("⚠️ Karta O'zbekistonning rasmiy Uzcard yoki Humo tizimlariga mos kelmadi.")
    else:
        recommendations.append(f"To'lov tizimi: {system} ({bank})")

    recommendations.append("Eslatma: Begona shaxsga pul o'tkazishdan oldin uning ism-sharifini bank ilovasida (Click, Payme, Uzum) tekshiring.")

    verdict = "safe" if risk_score < 40 else ("suspicious" if risk_score < 70 else "dangerous")

    return {
        "valid_format": True,
        "is_luhn_valid": is_luhn_valid,
        "card_number_masked": masked,
        "payment_system": system,
        "bank_name": bank,
        "card_type": card_type,
        "risk_score": risk_score,
        "verdict": verdict,
        "warnings": warnings,
        "recommendations": recommendations,
        "summary_uz": f"Ushbu karta {system} tizimiga ({bank}) tegishli. Nazorat kodi: {'To`g`ri' if is_luhn_valid else 'XATO'}."
    }
