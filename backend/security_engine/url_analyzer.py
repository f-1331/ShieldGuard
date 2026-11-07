import re
import socket
import urllib.parse
from datetime import datetime
from typing import Dict, Any, List, Optional
import httpx

# Taniqli rasmiy o'zbek brendlari va davlat saytlari
TRUSTED_UZ_DOMAINS = {
    "click.uz": "Click O'zbekiston (Rasmiy to'lov tizimi)",
    "payme.uz": "Payme O'zbekiston (Rasmiy to'lov tizimi)",
    "uzum.uz": "Uzum (Rasmiy ekotizim)",
    "uzumbank.uz": "Uzum Bank (Rasmiy bank)",
    "uzumnasiya.uz": "Uzum Nasiya",
    "humocard.uz": "Humo to'lov tizimi",
    "uzcard.uz": "Uzcard to'lov tizimi",
    "agrobank.uz": "Agrobank ATB",
    "xb.uz": "Xalq Banki ATB",
    "kapitalbank.uz": "Kapitalbank ATB",
    "ipakyulibank.uz": "Ipak Yo'li Banki",
    "nbu.uz": "O'zmilliybank (NBU)",
    "infinbank.com": "InfinBANK",
    "hamkorbank.uz": "Hamkorbank",
    "tbcbank.uz": "TBC Bank O'zbekiston",
    "anorbank.uz": "Anorbank",
    "gov.uz": "O'zbekiston Hukumat portali",
    "my.gov.uz": "Yagona interaktiv davlat xizmatlari portali (YAIDXP)",
    "soliq.uz": "Davlat Soliq Qo'mitasi",
    "sud.uz": "Oliy Sud portali",
    "lex.uz": "Qonunchilik ma'lumotlari milliy bazasi",
    "mib.gov.uz": "Majburiy ijro byurosi"
}

# Himoyalangan brend kalit so'zlari (Typosquatting tekshiruvi uchun)
PROTECTED_BRAND_NAMES = [
    "click", "payme", "uzum", "humo", "uzcard",
    "agrobank", "kapital", "xalqbank", "anorbank", "tbcbank"
]

# Shubhali yuqori darajali domenlar (Scam & Phishingda ko'p ishlatiladigan bepul/arzon zonalar)
SUSPICIOUS_TLDS = {
    "xyz", "top", "tk", "buzz", "site", "cfd", "vip", "icu",
    "sbs", "ml", "ga", "cf", "gq", "work", "click", "link",
    "pw", "fun", "monster", "rest", "surf", "cam", "loan", "live"
}

# Ijtimoiy muhandislik & Fishing kalit so'zlari (O'zbek va Rus tillarida)
SCAM_KEYWORDS = [
    ("prezident yordam", 35, "Prezident nomidan moddiy yordam va'dasi (Soxta to'lovlar tuzog'i)"),
    ("bir martalik to'lov", 30, "Tasdiqlanmagan bir martalik kompensatsiya haqida xabar"),
    ("yordam puli", 30, "Moddiy yordam puli tarqatilishi haqida soxta e'lon"),
    ("yutib oldingiz", 35, "Soxta yutuq yoki sovg'a va'dasi (Fishing sxemasi)"),
    ("iphone yutdingiz", 40, "Qimmatbaho texnika yutug'i bilan aldash usuli"),
    ("telegram premium bepul", 35, "Telegram hisobni o'g'irlash uchun soxta Premium tuzog'i"),
    ("ovoz bering", 25, "Bolalar tanlovida ovoz berish bahonasida Telegram kodini o'g'irlash"),
    ("kartangiz bloklandi", 40, "Vahima uyg'otish: Karta bloklangani haqida soxta ogohlantirish"),
    ("karta raqam", 20, "Bank karta ma'lumotlarini so'rash belgisi"),
    ("sms kod", 35, "SMS orqali kelgan xavfsizlik kodini talab qilish (Kritik xavf!)"),
    ("tasdiqlash kodi", 35, "Bir martalik tasdiqlash kodini kiritish talabi"),
    ("shoshiling", 20, "Shoshiltirish va psixologik bosim o'tkazish usuli"),
    ("oxirgi imkoniyat", 20, "Psixologik manipulyatsiya va sun'iy shoshilinchlik"),
    ("bepul bonus", 25, "Soxta bonus va keshbek va'dasi"),
    ("subsidiyani olish", 35, "Soxta davlat subsidiyasi e'loni"),
    ("инвест", 20, "Soxta investitsiya va kafolatlangan daromad va'dasi"),
    ("выплата", 25, "Tasdiqlanmagan to'lov va'dasi")
]


def levenshtein_distance(s1: str, s2: str) -> int:
    """Ikki so'z orasidagi tahrir masofasini (Levenshtein) hisoblaydi."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def extract_urls(text: str) -> List[str]:
    """Matn ichidagi barcha URL va domenlarni aniqlab ajratib oladi."""
    url_pattern = r'(?:https?:\/\/|www\.)[^\s<>"]+|[a-zA-Z0-9.-]+\.(?:uz|com|ru|org|net|xyz|top|site|online|info|me|io|buzz|biz|store)(?:\/[^\s<>"]*)?'
    raw_urls = re.findall(url_pattern, text, re.IGNORECASE)
    
    cleaned_urls = []
    for u in raw_urls:
        # Nuqta yoki vergul kabi chekka belgilarni tozalash
        u = u.strip().rstrip('.,;:!?)')
        if not u.startswith("http://") and not u.startswith("https://"):
            u = "https://" + u
        if u not in cleaned_urls:
            cleaned_urls.append(u)
    return cleaned_urls


def check_typosquatting(domain: str) -> Optional[Dict[str, Any]]:
    """O'zbekistonning mashhur brendlari nomini qalbakilashtirish (Typosquatting) tekshiruvi."""
    domain_clean = domain.lower()
    if domain_clean.startswith("www."):
        domain_clean = domain_clean[4:]

    # Agar domen to'liq rasmiy ro'yxatda bo'lsa - xavfsiz
    if domain_clean in TRUSTED_UZ_DOMAINS:
        return None

    # TLD ajratish
    parts = domain_clean.split(".")
    domain_body = parts[0] if len(parts) > 1 else domain_clean

    # 1. To'g'ridan-to'g'ri brend nomini qamrab olgan gibrid soxta domenlar
    # Masalan: c1ick-uz.com, payme-bonus.ru, uzum-market.site, click-online.me
    for brand in PROTECTED_BRAND_NAMES:
        # L33t speak almashtirishlar (c1ick -> click, paym3 -> payme)
        normalized_body = (
            domain_body.replace("1", "l")
            .replace("0", "o")
            .replace("3", "e")
            .replace("4", "a")
            .replace("-", "")
            .replace("_", "")
        )

        if brand in normalized_body and domain_clean not in TRUSTED_UZ_DOMAINS:
            return {
                "target_brand": brand.capitalize(),
                "type": "Brand Spoofing (Brend nomidan foydalanish)",
                "detail": f"Ushbu domen rasmiy '{brand}.uz' ga aloqador emas, lekin foydalanuvchini chalg'itish uchun uning nomidan foydalanmoqda!"
            }

        # 2. Levenshtein masofasi (masalan, clik.uz, paymme.uz)
        dist = levenshtein_distance(domain_body, brand)
        if 1 <= dist <= 2 and len(domain_body) >= 4:
            return {
                "target_brand": brand.capitalize(),
                "type": "Typosquatting (O'xshash xato yozuv)",
                "detail": f"Domen nomi rasmiy '{brand}' brendiga ataylab juda o'xshatib yozilgan (masofa: {dist}). Bu fishing tuzog'i belgisi!"
            }

    return None


async def inspect_webpage_content(url: str) -> Dict[str, Any]:
    """Havolaga xavfsiz murojaat qilib, qayta yo'naltirish zanjiri va sahifa shaklini tahlil qiladi."""
    result = {
        "final_url": url,
        "status_code": None,
        "redirect_chain": [],
        "has_password_field": False,
        "has_card_field": False,
        "has_otp_field": False,
        "suspicious_scripts": False,
        "page_title": "",
        "fetch_success": False
    }

    parsed = urllib.parse.urlparse(url)
    hostname = parsed.hostname or ""

    # SSRF va ichki tarmoqqa murojaatlarni bloklash
    if hostname in ("localhost", "127.0.0.1", "0.0.0.0", "::1") or hostname.startswith("192.168.") or hostname.startswith("10."):
        return result

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 ShieldGuard/1.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "uz,ru;q=0.9,en;q=0.8"
    }

    try:
        async with httpx.AsyncClient(timeout=6.0, follow_redirects=True, verify=False) as client:
            response = await client.get(url, headers=headers)
            result["fetch_success"] = True
            result["status_code"] = response.status_code
            result["final_url"] = str(response.url)
            
            # Redirect zanjirini yozish
            for hist in response.history:
                result["redirect_chain"].append(str(hist.url))

            content = response.text.lower()

            # Sarlavhani olish
            title_match = re.search(r'<title[^>]*>(.*?)</title>', response.text, re.IGNORECASE | re.DOTALL)
            if title_match:
                result["page_title"] = title_match.group(1).strip()[:100]

            # HTML ichidagi haqiqiy <input> teglari bo'yicha aniq tahlil (soxta pozitivlarni oldini olish)
            input_tags = re.findall(r'<input\b[^>]*>', response.text, re.IGNORECASE)

            # 1. Parol maydoni (type="password")
            result["has_password_field"] = any(re.search(r'type=["\']?password["\']?', inp, re.IGNORECASE) for inp in input_tags)

            # 2. Bank kartasi kiritish maydonlari (aniq regex)
            card_name_re = re.compile(r'\b(card[-_]?num|card[-_]?number|karta[-_]?raqam|pan[-_]?num|cc[-_]?number|card[-_]?pan|credit[-_]?card)\b', re.IGNORECASE)
            card_placeholder_re = re.compile(r'(?:karta\s*raqam|номер\s*карты|card\s*number|8600\s*\d{4}|9860\s*\d{4})', re.IGNORECASE)
            cvv_name_re = re.compile(r'\b(cvv\d?|cvc\d?|card[-_]?cvv|security[-_]?code)\b', re.IGNORECASE)
            cvv_placeholder_re = re.compile(r'\b(cvv|cvc)\b', re.IGNORECASE)

            result["has_card_field"] = any(
                card_name_re.search(inp) or card_placeholder_re.search(inp) or cvv_name_re.search(inp) or cvv_placeholder_re.search(inp)
                for inp in input_tags
            )

            # 3. SMS orqali keladigan bir martalik tasdiqlash kodi (OTP)
            otp_name_re = re.compile(r'\b(sms[-_]?kod|sms[-_]?code|tasdiqlash[-_]?kod|otp[-_]?code|sms[-_]?otp)\b', re.IGNORECASE)
            otp_placeholder_re = re.compile(r'(?:sms\s*kod|tasdiqlash\s*kodi|код\s*из\s*смс|bir\s*martalik\s*kod|sms-kod)', re.IGNORECASE)

            result["has_otp_field"] = any(
                otp_name_re.search(inp) or otp_placeholder_re.search(inp)
                for inp in input_tags
            )

    except Exception:
        # Sahifa yuklanmasa yoki tarmoq xatosi bo'lsa xavfsiz davom etamiz
        result["fetch_success"] = False

    return result


async def analyze_url_or_text(raw_input: str) -> Dict[str, Any]:
    """URL yoki shubhali xabarni kompleks tekshirish (Evristika + Fishing + Ma'lumot yig'ish)."""
    urls = extract_urls(raw_input)
    risk_score = 0
    red_flags: List[str] = []
    positive_flags: List[str] = []
    detected_brand = None
    inspected_data = None
    target_display = raw_input[:100]

    # Matndagi fishing so'zlarini tekshirish
    lower_input = raw_input.lower()
    for phrase, score_add, explanation in SCAM_KEYWORDS:
        if phrase in lower_input:
            risk_score += score_add
            red_flags.append(f"⚠️ {explanation}")

    # Agar havolalar aniqlangan bo'lsa
    if urls:
        first_url = urls[0]
        target_display = first_url
        parsed = urllib.parse.urlparse(first_url)
        domain = parsed.hostname or ""
        domain = domain.lower()
        if domain.startswith("www."):
            domain = domain[4:]

        # 1. Rasmiy ishonchli domen tekshiruvi
        if domain in TRUSTED_UZ_DOMAINS:
            risk_score = 0
            positive_flags.append(f"✅ Rasmiy va tasdiqlangan manzil: {TRUSTED_UZ_DOMAINS[domain]}")
            return {
                "input": raw_input,
                "target": domain,
                "risk_score": 0,
                "verdict": "safe",
                "verdict_uz": "Xavfsiz va Ishonchli",
                "summary_uz": f"Ushbu havola rasmiy va xavfsiz tizimga tegishli: {TRUSTED_UZ_DOMAINS[domain]}.",
                "red_flags": [],
                "positive_flags": positive_flags,
                "details": {
                    "is_official": True,
                    "official_name": TRUSTED_UZ_DOMAINS[domain],
                    "extracted_urls": urls
                }
            }

        # 2. Typosquatting & Brend o'g'irlash
        typo_result = check_typosquatting(domain)
        if typo_result:
            risk_score += 55
            detected_brand = typo_result["target_brand"]
            red_flags.append(f"🚨 {typo_result['type']}: {typo_result['detail']}")

        # 3. Shubhali TLD (domen hududi)
        tld = domain.split(".")[-1] if "." in domain else ""
        if tld in SUSPICIOUS_TLDS:
            risk_score += 30
            red_flags.append(f"⚠️ Shubhali domen hududi (. {tld}): Bu zona odatda bir kunlik fishing saytlar uchun ishlatiladi.")

        # 4. Havolaning tuzilishi (IP-manzil, ko'p qatlamli subdomenlar)
        if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', domain):
            risk_score += 45
            red_flags.append("🚨 To'g'ridan-to'g'ri IP-manzilga yo'naltirilgan: Rasmiy kompaniyalar bunday manzildan foydalanmaydi.")
        
        if domain.count(".") >= 3:
            risk_score += 20
            red_flags.append("⚠️ Murakkab ko'p bosqichli subdomen: Firibgarlar haqiqiy manzilni yashirish uchun qo'llaydi.")

        # 5. Sahifani real vaqtda xavfsiz tekshirish (HTML skanerlash)
        inspected_data = await inspect_webpage_content(first_url)
        if inspected_data["fetch_success"]:
            # Agar norasmiy saytda karta yoki SMS so'ralsa
            if inspected_data["has_card_field"]:
                risk_score += 40
                red_flags.append("🚨 Saytda bank kartasi ma'lumotlarini (PAN/CVV) kiritish shakli mavjud!")
            if inspected_data["has_otp_field"]:
                risk_score += 45
                red_flags.append("🚨 Saytda SMS orqali keladigan maxfiy tasdiqlash kodini so'rash maydoni topildi! (Hisobingizni o'g'irlash xavfi)")
            if inspected_data["has_password_field"] and typo_result:
                risk_score += 35
                red_flags.append("🚨 Qalbaki sahifada login va parol talab qilinmoqda!")

            if len(inspected_data["redirect_chain"]) >= 2:
                risk_score += 25
                red_flags.append(f"⚠️ Ko'p bosqichli qayta yo'naltirish (Redirect chain: {len(inspected_data['redirect_chain'])} ta sakrash).")

    # Xavf darajasini chegaralash (0 - 100)
    risk_score = min(max(risk_score, 0), 100)

    # Yakuniy hukm
    if risk_score >= 70:
        verdict = "dangerous"
        verdict_uz = "Xavfli! (Firibgarlik yoki Fishing)"
        summary_uz = "Ushbu manzil yoki xabar katta ehtimol bilan kiber-firibgarlar tomonidan pul yoki ma'lumotlarni o'g'irlash uchun tuzilgan. Hech qanday ma'lumot kiritmang!"
    elif risk_score >= 40:
        verdict = "suspicious"
        verdict_uz = "Shubhali (Ehtiyot bo'ling)"
        summary_uz = "Xabarda yoki havolada bir nechta xavfli belgilar aniqlandi. Tasdiqlanmagan manbalardan kelgan havola bo'lsa ochmaslik tavsiya etiladi."
    else:
        verdict = "safe"
        verdict_uz = "Xavfsiz ko'rinadi"
        summary_uz = "Xabarda ochiq firibgarlik belgilari aniqlanmadi. Biroq har doim hushyor bo'ling va begonalarga SMS-kodlarni bermang."

    return {
        "input": raw_input,
        "target": target_display,
        "risk_score": risk_score,
        "verdict": verdict,
        "verdict_uz": verdict_uz,
        "summary_uz": summary_uz,
        "red_flags": red_flags,
        "positive_flags": positive_flags,
        "detected_brand": detected_brand,
        "details": {
            "extracted_urls": urls,
            "web_inspection": inspected_data
        }
    }
