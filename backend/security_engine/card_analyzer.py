import re
from typing import Dict, Any, Optional

# O'zbekiston banklari BIN (Bank Identification Number) ma'lumotlar bazasi
UZBEK_CARD_BINS = {
    # UZCARD (8600)
    "8600": {"system": "Uzcard", "type": "Milliy to'lov tizimi (So'm)", "bank": "Uzcard milliy to'lov tizimi"},
    "860002": {"system": "Uzcard", "type": "Debet", "bank": "Xalq Banki ATB"},
    "860003": {"system": "Uzcard", "type": "Debet", "bank": "Agrobank ATB"},
    "860004": {"system": "Uzcard", "type": "Debet", "bank": "Agrobank ATB"},
    "860005": {"system": "Uzcard", "type": "Debet", "bank": "Milliy Bank (NBU)"},
    "860006": {"system": "Uzcard", "type": "Debet", "bank": "O'zsanoatqurilishbank (SQB)"},
    "860012": {"system": "Uzcard", "type": "Debet", "bank": "Asakabank ATB"},
    "860014": {"system": "Uzcard", "type": "Debet", "bank": "Kapitalbank ATB"},
    "860019": {"system": "Uzcard", "type": "Debet", "bank": "Ipoteka-bank ATIB"},
    "860020": {"system": "Uzcard", "type": "Debet", "bank": "Aloqabank ATB"},
    "860028": {"system": "Uzcard", "type": "Debet", "bank": "Qishloq Qurilish Bank (BRB)"},
    "860030": {"system": "Uzcard", "type": "Debet", "bank": "Trastbank XAB"},
    "860031": {"system": "Uzcard", "type": "Debet", "bank": "Ipak Yo'li Banki"},
    "860033": {"system": "Uzcard", "type": "Debet", "bank": "Hamkorbank ATB"},
    "860049": {"system": "Uzcard", "type": "Debet", "bank": "Anorbank AJ"},
    "860051": {"system": "Uzcard", "type": "Debet", "bank": "InfinBANK"},
    "860053": {"system": "Uzcard", "type": "Debet", "bank": "Mikrokreditbank ATB"},
    "860055": {"system": "Uzcard", "type": "Debet", "bank": "Uzum Bank (Apelsin)"},
    "860057": {"system": "Uzcard", "type": "Debet", "bank": "TBC Bank O'zbekiston"},
    "860060": {"system": "Uzcard", "type": "Debet", "bank": "Poytaxt Bank"},

    # HUMO (9860)
    "9860": {"system": "Humo", "type": "Milliy kontaktsiz to'lov tizimi (So'm)", "bank": "Humo milliy to'lov tizimi"},
    "986001": {"system": "Humo", "type": "Debet / Kontaktsiz", "bank": "Xalq Banki ATB"},
    "986002": {"system": "Humo", "type": "Debet / Kontaktsiz", "bank": "Agrobank ATB"},
    "986003": {"system": "Humo", "type": "Debet / Kontaktsiz", "bank": "Milliy Bank (NBU)"},
    "986004": {"system": "Humo", "type": "Debet / Kontaktsiz", "bank": "O'zsanoatqurilishbank (SQB)"},
    "986008": {"system": "Humo", "type": "Debet / Kontaktsiz", "bank": "Kapitalbank ATB"},
    "986009": {"system": "Humo", "type": "Debet / Kontaktsiz", "bank": "Asakabank ATB"},
    "986010": {"system": "Humo", "type": "Debet / Kontaktsiz", "bank": "Ipoteka-bank ATIB"},
    "986012": {"system": "Humo", "type": "Debet / Kontaktsiz", "bank": "Ipak Yo'li Banki"},
    "986014": {"system": "Humo", "type": "Debet / Kontaktsiz", "bank": "Aloqabank ATB"},
    "986016": {"system": "Humo", "type": "Debet / Kontaktsiz", "bank": "Hamkorbank ATB"},
    "986017": {"system": "Humo", "type": "Debet / Kontaktsiz", "bank": "Trastbank XAB"},
    "986020": {"system": "Humo", "type": "Debet / Kontaktsiz", "bank": "InfinBANK"},
    "986021": {"system": "Humo", "type": "Debet / Kontaktsiz", "bank": "Qishloq Qurilish Bank (BRB)"},
    "986024": {"system": "Humo", "type": "Debet / Kontaktsiz", "bank": "TBC Bank O'zbekiston"},
    "986035": {"system": "Humo", "type": "Debet / Kontaktsiz", "bank": "Anorbank AJ"},
    "986060": {"system": "Humo", "type": "Debet / Kontaktsiz", "bank": "Uzum Bank"}
}

# Xorijiy (MDH / Rossiya) kartalari BINlari (Ko'pincha kiber-firibgarlar mablag'larni chiqarib ketishda foydalanadi)
FOREIGN_RISK_BINS = {
    "2202": "Mir to'lov tizimi (Rossiya - Sberbank)",
    "2200": "Mir to'lov tizimi (Rossiya - Tinkoff / VTB)",
    "2204": "Mir to'lov tizimi (Rossiya)",
    "4276": "Visa (Rossiya - Sberbank)",
    "5469": "Mastercard (Rossiya - Sberbank)",
    "5213": "Mastercard (Rossiya - Tinkoff)",
    "4154": "Visa (Rossiya - Tinkoff / QIWI)",
    "4890": "Visa (Rossiya - Qiwi / YooMoney)",
    "4003": "Visa (Xorijiy virtual karta)",
    "5536": "Mastercard (Xorijiy / MDH)"
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
    """Bank kartasi raqamini tahlil qilish, emitent bankni aniqlash va yashirin xavflarni baholash."""
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
            "error_uz": f"Karta raqami uzunligi noto'g'ri ({length} ta raqam). Bank kartasi 16 ta raqam bo'lishi shart.",
            "risk_score": 60,
            "verdict": "suspicious"
        }

    is_luhn_valid = luhn_checksum_valid(clean_num)

    system = "Noma'lum"
    bank = "Noma'lum bank"
    card_type = "Standart"
    is_foreign = False

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
    elif bin_4 in FOREIGN_RISK_BINS:
        system = "Xorijiy karta (Rossiya / MDH)"
        bank = FOREIGN_RISK_BINS[bin_4]
        card_type = "Xorijiy P2P / Virtual"
        is_foreign = True
    elif clean_num.startswith("4"):
        system = "Visa International"
        bank = "Xalqaro Visa kartasi (O'zbekiston yoki xorij)"
        card_type = "Valyuta kartasi"
    elif clean_num.startswith(("51", "52", "53", "54", "55")):
        system = "Mastercard International"
        bank = "Xalqaro Mastercard kartasi"
        card_type = "Valyuta kartasi"
    elif clean_num.startswith(("2200", "2201", "2202", "2203", "2204")):
        system = "Mir (Rossiya)"
        bank = "Mir milliy to'lov tizimi (Rossiya Federatsiyasi)"
        card_type = "Xorijiy to'lov tizimi"
        is_foreign = True
    elif clean_num.startswith("62"):
        system = "UnionPay"
        bank = "UnionPay xalqaro kartasi"

    masked = f"{clean_num[:4]} {clean_num[4:6]}** **** {clean_num[-4:]}"

    risk_score = 0
    warnings = []
    recommendations = []

    if not is_luhn_valid:
        risk_score = 80
        warnings.append("🚨 Karta nazorat summasi (Luhn algoritmi) noto'g'ri! Bu sun'iy yaratilgan qalbaki karta raqami yoki tasodifiy kiritilgan xato raqam!")
    else:
        recommendations.append("Karta raqami formati va nazorat raqami to'g'ri.")

    if is_foreign:
        risk_score = max(risk_score, 65)
        warnings.append("⚠️ DIQQAT: Karta O'zbekistonga emas, xorijiy davlatga (Rossiya/MDH) tegishli! Kiber-firibgarlar o'g'irlangan pullarni O'zbekistondan olib chiqib ketish uchun ko'pincha aynan shunday kartalarga o'tkazishni so'rashadi.")

    if system == "Noma'lum":
        risk_score = max(risk_score, 45)
        warnings.append("⚠️ Karta O'zbekistonning rasmiy Uzcard yoki Humo tizimlarida ro'yxatdan o'tmagan.")
    else:
        recommendations.append(f"To'lov tizimi: {system} ({bank})")

    recommendations.append("🛡️ Yashirin o'g'irliklarga qarshi oltin qoida: Pul qabul qilish uchun FAQAT 16 talik raqamni bering. Agar xaridor yoki begona kishi sizdan kartaning amal qilish muddati, CVV kod, yoki SMS kodni so'rasa — bu 100% PUL O'G'IRLASH!")

    verdict = "safe" if risk_score < 40 else ("suspicious" if risk_score < 70 else "dangerous")

    summary_uz = f"Ushbu karta {system} tizimiga ({bank}) tegishli. Nazorat summasi: {'To`g`ri' if is_luhn_valid else 'XATO'}."
    if is_foreign:
        summary_uz += " Ogoh bo'ling: Karta xorijiy davlatga tegishli!"

    return {
        "valid_format": True,
        "is_luhn_valid": is_luhn_valid,
        "card_number_masked": masked,
        "clean_digits": clean_num,
        "payment_system": system,
        "bank_name": bank,
        "card_type": card_type,
        "is_foreign": is_foreign,
        "risk_score": risk_score,
        "verdict": verdict,
        "warnings": warnings,
        "recommendations": recommendations,
        "summary_uz": summary_uz
    }
