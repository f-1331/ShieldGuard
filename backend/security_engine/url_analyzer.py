import re
import socket
import urllib.parse
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import httpx

# =========================================================================
# 1. ISHONCHLI RASMIY DOMENLAR VA DAVLAT PORTALLARI (WHITELIST)
# =========================================================================

TRUSTED_UZ_DOMAINS = {
    "click.uz": "Click O'zbekiston (Rasmiy to'lov tizimi)",
    "payme.uz": "Payme O'zbekiston (Rasmiy to'lov tizimi)",
    "uzum.uz": "Uzum (Rasmiy milliy ekotizim)",
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
    "anorbank.uz": "Anorbank AJ",
    "sqb.uz": "O'zsanoatqurilishbank (SQB)",
    "asakabank.uz": "Asakabank ATB",
    "ipotekabank.uz": "Ipoteka-bank ATIB",
    "aloqabank.uz": "Aloqabank ATB",
    "gov.uz": "O'zbekiston Hukumat portali",
    "my.gov.uz": "Yagona interaktiv davlat xizmatlari portali (YAIDXP)",
    "soliq.uz": "Davlat Soliq Qo'mitasi",
    "sud.uz": "Oliy Sud portali",
    "lex.uz": "Qonunchilik ma'lumotlari milliy bazasi",
    "mib.gov.uz": "Majburiy ijro byurosi",
    "iiv.uz": "Ichki Ishlar Vazirligi (IIV)",
    "olx.uz": "OLX O'zbekiston (Rasmiy e'lonlar portali)"
}

PROTECTED_BRAND_NAMES = [
    "click", "payme", "uzum", "humo", "uzcard",
    "agrobank", "kapital", "xalqbank", "anorbank", "tbcbank",
    "olx", "cdek", "mygov"
]

SUSPICIOUS_TLDS = {
    "xyz", "top", "tk", "buzz", "site", "cfd", "vip", "icu",
    "sbs", "ml", "ga", "cf", "gq", "work", "click", "link",
    "pw", "fun", "monster", "rest", "surf", "cam", "loan", "live",
    "cc", "ws", "su", "shop", "cyou", "fit", "beauty", "hair"
}

# =========================================================================
# 2. XAVF VA FIRIBGARLIK ANDOZALARI (HEURISTIC ATTACK PATTERNS)
# =========================================================================

# Format: (pattern_regex, risk_score_addition, description_uz, threat_category)
THREAT_PATTERNS: List[Tuple[str, int, str, str]] = [
    # --- 1. YASHIRIN AVTOSPISANIE VA OBUNA TUZOQLARI (Hidden Subscriptions) ---
    (
        r"(?:1\s*so['`]?m|1\s*som|1\s*rub|1\s*rubl|100\s*so['`]?m|1000\s*so['`]?m)\b.*?(?:to['`]?lab|evaziga|sinov|obuna|kiriting)",
        85,
        "Yashirin obuna va avtospisanie tuzog'i! 1 so'm to'lov ko'rsatib, keyinchalik kartangizdan har oy/hafta 100 000 - 300 000 so'mgacha pulni avtomatik yechib oladigan xizmat.",
        "hidden_subscription"
    ),
    (
        r"\b(?:avtospisanie|avto-spisanie|avtomatik\s*to['`]?lov|har\s*oy\s*yechiladi|har\s*oy\s*yechib|har\s*hafta\s*yechiladi|rekurrent|podpiska|avtoplatej|avto-uzaytirish|sinov\s*muddati\s*tugagach)\b",
        80,
        "Avtomatik pul yechish (avtospisanie/obuna) sharti aniqlandi! Roziligingizsiz kartangizdan doimiy to'lov yechib olinishi mumkin.",
        "hidden_subscription"
    ),
    (
        r"\b(?:sinov\s*muddati|sinov\s*davri|probnyy\s*period|trial\s*period)\b",
        45,
        "Sinov muddati taklifi: Ko'p hollarda sinov muddati tugagach, foydalanuvchiga bildirmasdan kartadan yirik summa yechiladi.",
        "hidden_subscription"
    ),

    # --- 2. SOXTA YETKAZIB BERISH & PULNI QABUL QILISH (Fake Deliveries) ---
    (
        r"\b(?:olx[-_\s]*dostavk[a-z]*|olx[-_\s]*delivery|uzum[-_\s]*delivery|cdek[-_\s]*dostavk[a-z]*|yandex[-_\s]*delivery)\b",
        85,
        "Soxta yetkazib berish (OLX / Uzum / CDEK delivery) fishing tuzog'i belgisi!",
        "fake_delivery"
    ),
    (
        r"\b(?:(?:pul|mablag['`]?|to['`]?lov|summa)\w*\s*(?:o['`]?tkazdim|to['`]?lab\s*qo['`]?ydim|to['`]?ladim)|qabul\s*qilib\s*oling|qabul\s*qiling|kartangizga\s*qabul|to['`]?lovni\s*qabul|pulni\s*olish\s*tugmasi|kuryer\s*orqali\s*to['`]?lov|poluchit\s*dengi|priem\s*plateja|priyem\s*platezhey|xaridor\s*to['`]?lovni\s*amalga\s*oshirdi|kartangizga\s*pul\s*o['`]?tkazildi)\b",
        90,
        "Soxta 'Pulni qabul qilib oling' tuzog'i! Pul qabul qilish uchun FAQAT 16 talik karta raqami kifoya. Agar CVV, amal qilish muddati yoki SMS-kod so'ralsa — bu 100% PUL O'G'IRLASH!",
        "fake_delivery"
    ),

    # --- 3. SOXTA KREDIT VA AVANS BADALLARI (Fake Loan Upfront Fees) ---
    (
        r"\b(?:sug['`]?urta\s*badali|kredit\s*komissiyasi|faollashtirish\s*to['`]?lovi|kredit\s*ochish\s*uchun\s*to['`]?lov|tasdiqlangan\s*kreditni\s*olish|komissiya\s*to['`]?lang\s*va\s*kredit|notarial\s*to['`]?lov\s*qiling|hisobni\s*faollashtirish\s*uchun)\b",
        90,
        "Kredit olish uchun oldindan to'lov (sug'urta badali/komissiya) talab qilish firibgarligi! Rasmiy banklar hech qachon kredit berishdan oldin boshqa kartaga to'lov talab qilmaydi.",
        "fake_loan"
    ),
    (
        r"\b(?:garovsiz\s*(?:va\s*kafilsiz)?\s*kredit|garovsiz\s*\d+\s*(?:million|mln)|qora\s*ro['`]?yxatdagilarga\s*(?:ham)?\s*kredit|tezkor\s*qarz\s*beramiz|100%\s*tasdiqlanadigan\s*kredit)\b",
        70,
        "Shubhali 'Kafilsiz va garovsiz tezkor kredit' e'loni: Fuqarolarni aldab, sug'urta to'lovi bahonasida pul undirish sxemasi.",
        "fake_loan"
    ),

    # --- 4. WILDBERRIES / AMAZON / ONLAYN ISH PIRAMIDASI (Task Scams) ---
    (
        r"\b(?:wildberries\s*(?:buyurtma|layk|topshiriq|vazifa)|amazon\s*(?:tovar|topshiriq)|vazifani\s*bajaring|tovarga\s*layk\s*bosing|kuniga\s*\d{2,3}\s*000\s*so['`]?m|kunlik\s*daromad\s*kafolatlangan|skrinshot\s*yuboring|vip\s*daraja\s*sotib|topshiriqni\s*bajaring\s*va\s*pul|to['`]?lovni\s*muzlatishdan\s*chiqarish|depozit\s*kiritish|depozit\s*to['`]?lang)\b",
        85,
        "Soxta onlayn ish va layk bosish piramidasi (Wildberries/Amazon tuzog'i)! Avval arzimas pul berib ishonchga kirishadi, keyin katta depozit talab qilib barcha pulingizni muzlatib qo'yishadi.",
        "task_scam"
    ),

    # --- 5. TELEGRAM AKKAUNTNI O'G'IRLASH (Session Phishing) ---
    (
        r"\b(?:ovoz\s*bering|singlimga\s*ovoz|jiyanimga\s*ovoz|bolamga\s*ovoz|tanlovda\s*ovoz|gimnastika\s*tanlovi|rasm\s*tanlovida|bolalar\s*tanlovi|eng\s*yaxshi\s*rasm)\b",
        80,
        "Telegram hisobni o'g'irlash (ovoz berish bahonasi)! Tanlovda ovoz berish niqobi ostida Telegram tasdiqlash kodini yoki telefon raqamingizni o'g'irlashadi.",
        "telegram_phishing"
    ),
    (
        r"\b(?:telegram\s*premium\s*bepul|telegram\s*premium\s*tekin|3\s*oylik\s*premium|bepul\s*premium\s*tarqatilmoqda|qr\s*kod\s*orqali\s*kiring|telegram\s*akkauntni\s*tasdiqlang|akkountingiz\s*24\s*soatda\s*o['`]?chiriladi|telegram\s*xavfsizlik\s*xizmati|sessiyani\s*tasdiqlang|telegram\s*kodini\s*yuboring)\b",
        90,
        "Telegram sessiyasini qo'lga kiritish (Session Hijacking) fishingi! Hisobingiz boshqa shaxslar qo'liga o'tishi va barcha yaqinlaringizdan nomingizdan pul so'ralishi xavfi bor.",
        "telegram_phishing"
    ),

    # --- 6. SOXTA DAVLAT YORDAMI VA KOMPENSATSIYALAR ---
    (
        r"\b(?:prezident\s*(?:nomidan)?\s*yordam|moddiy\s*yordam\s*puli|bir\s*martalik\s*to['`]?lov|yordam\s*puli\s*tarqatilmoqda|subsidiyani\s*olish|bolalar\s*uchun\s*pul\s*beriladi|pensiya\s*kompensatsiya|gaz\s*va\s*elektr\s*kompensatsiya|davlat\s*tomonidan\s*to['`]?lov|portal\s*orqali\s*yordam)\b",
        85,
        "Davlat va Prezident nomidan soxta moddiy yordam va'dasi! Fuqarolarning bank kartalaridagi barcha pullarni bo'shatib olish uchun tuzilgan soxta sahifa.",
        "fake_subsidy"
    ),

    # --- 7. VAHIMA, SHOSHILTIRISH VA SOXTA BLOKLASH ---
    (
        r"\b(?:kartangiz\s*bloklandi|hisobingiz\s*bloklanadi|kartangizdan\s*pul\s*yechilmoqda|shubhali\s*operatsiya\s*to['`]?xtatildi|zudlik\s*bilan\s*tasdiqlang|24\s*soat\s*ichida\s*to['`]?lang|xavfsizlik\s*xizmati\s*qo['`]?ng['`]?irog['`]?i)\b",
        80,
        "Vahima uyg'otish va soxta bank blokirovkasi tahdidi! Foydalanuvchini shoshiltirib, o'ylab ko'rmasdan karta kodlarini aytishga majburlash usuli.",
        "urgency_fear"
    ),

    # --- 8. SOXTA JARIMA VA MIB / SUD TAHDIDI ---
    (
        r"\b(?:mib\s*qarzdorlik|sud\s*qarori\s*chiqdi|soliq\s*qarzi|jarimani\s*24\s*soatda|kartangiz\s*xatlanadi|kartangiz\s*hibsga\s*olindi|jinoyat\s*ishi\s*qo['`]?zg['`]?atildi|sudga\s*chaqiruv\s*qog['`]?ozi)\b",
        80,
        "Soxta jarima va MIB/Sud nomidan qo'rqitish! Fuqaroni jarima bilan vahimaga solib, soxta sahifa orqali pulini o'g'irlashga qaratilgan.",
        "fake_fine"
    ),

    # --- 9. SOXTA INVESTITSIYA, P2P VA KRIPTO ALDOVI ---
    (
        r"\b(?:kunlik\s*10%|kunlik\s*5%|kafolatlangan\s*daromad|p2p\s*arbitraj|treyding\s*signallari|pulni\s*2\s*barobar\s*ko['`]?paytirish|daromadli\s*platforma|kuniga\s*100\$|passiv\s*daromad\s*kafolati)\b",
        80,
        "Moliyaviy piramida va soxta investitsiya aldovi! Kafolatlangan yuqori daromad va'da qilib, omonatlarni o'zlashtirish sxemasi.",
        "investment_scam"
    ),

    # --- 10. KRITIK MAXFIY MA'LUMOTLARNI SO'RASH (SMS, CVV, OTP) ---
    (
        r"\b(?:sms[-_\s]*kod|tasdiqlash\s*kodi|bir\s*martalik\s*kod|cvv\d?|cvc\d?|amal\s*qilish\s*muddati|kod\s*iz\s*sms|maxfiy\s*kod|karta\s*paroli|pin[-_\s]*kod)\b",
        85,
        "Kritik maxfiy ma'lumotlar (SMS-kod, CVV, amal qilish muddati) talab qilinmoqda! Bularni bilgan firibgar hisobingizdagi pullarni darhol yechib oladi.",
        "credential_harvesting"
    ),

    # --- 11. SOXTA SOVG'A VA YUTUQLAR ---
    (
        r"\b(?:yutib\s*oldingiz|iphone\s*yutdingiz|sovg['`]?a\s*yutdingiz|bepul\s*bonus|yutuqli\s*o['`]?yin|omadli\s*raqam|avtomobil\s*yutib)\b",
        75,
        "Soxta yutuq va sovg'a va'dasi! Sovg'ani olish bahonasida yetkazib berish haqi yoki komissiya to'lashni so'rab aldashadi.",
        "lottery_scam"
    )
]


def levenshtein_distance(s1: str, s2: str) -> int:
    """Ikki so'z orasidagi Levenshtein masofasini hisoblaydi."""
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
    """Matn ichidagi barcha URL va domenlarni aniqlaydi."""
    url_pattern = r'(?:https?:\/\/|www\.)[^\s<>"]+|[a-zA-Z0-9.-]+\.(?:uz|com|ru|org|net|xyz|top|site|online|info|me|io|buzz|biz|store|shop|cc|ws|fun)(?:\/[^\s<>"]*)?'
    raw_urls = re.findall(url_pattern, text, re.IGNORECASE)

    cleaned_urls = []
    for u in raw_urls:
        u = u.strip().rstrip('.,;:!?)')
        if not u.startswith("http://") and not u.startswith("https://"):
            u = "https://" + u
        if u not in cleaned_urls:
            cleaned_urls.append(u)
    return cleaned_urls


def check_typosquatting(domain: str) -> Optional[Dict[str, Any]]:
    """O'zbekistonning mashhur brendlari nomini qalbakilashtirish tekshiruvi."""
    domain_clean = domain.lower()
    if domain_clean.startswith("www."):
        domain_clean = domain_clean[4:]

    if domain_clean in TRUSTED_UZ_DOMAINS:
        return None

    parts = domain_clean.split(".")
    domain_body = parts[0] if len(parts) > 1 else domain_clean

    for brand in PROTECTED_BRAND_NAMES:
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
                "detail": f"Ushbu domen rasmiy '{brand}' xizmatiga aloqador emas, lekin fuqarolarni chalg'itish uchun uning nomini o'g'irlagan!"
            }

        dist = levenshtein_distance(domain_body, brand)
        if 1 <= dist <= 2 and len(domain_body) >= 4:
            return {
                "target_brand": brand.capitalize(),
                "type": "Typosquatting (O'xshash qalbaki yozuv)",
                "detail": f"Domen nomi rasmiy '{brand}' brendiga ataylab juda o'xshatib yozilgan (masofa: {dist}). Bu o'ta xavfli fishing tuzog'i!"
            }

    return None


async def inspect_webpage_content(url: str) -> Dict[str, Any]:
    """Havolaga xavfsiz ulanib, sahifa shakli, yashirin avtospisanie va soxta kassa tuzoqlarini skanerlaydi."""
    result = {
        "final_url": url,
        "status_code": None,
        "redirect_chain": [],
        "has_password_field": False,
        "has_card_field": False,
        "has_otp_field": False,
        "has_balance_field": False,
        "has_hidden_subscription": False,
        "has_fake_delivery": False,
        "page_title": "",
        "fetch_success": False
    }

    parsed = urllib.parse.urlparse(url)
    hostname = parsed.hostname or ""

    if hostname in ("localhost", "127.0.0.1", "0.0.0.0", "::1") or hostname.startswith("192.168.") or hostname.startswith("10."):
        return result

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 ShieldGuard/2.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "uz,ru;q=0.9,en;q=0.8"
    }

    try:
        async with httpx.AsyncClient(timeout=6.0, follow_redirects=True, verify=False) as client:
            response = await client.get(url, headers=headers)
            result["fetch_success"] = True
            result["status_code"] = response.status_code
            result["final_url"] = str(response.url)

            for hist in response.history:
                result["redirect_chain"].append(str(hist.url))

            raw_html = response.text
            lower_html = raw_html.lower()

            title_match = re.search(r'<title[^>]*>(.*?)</title>', raw_html, re.IGNORECASE | re.DOTALL)
            if title_match:
                result["page_title"] = title_match.group(1).strip()[:120]

            input_tags = re.findall(r'<input\b[^>]*>', raw_html, re.IGNORECASE)

            # 1. Parol maydoni
            result["has_password_field"] = any(re.search(r'type=["\']?password["\']?', inp, re.IGNORECASE) for inp in input_tags)

            # 2. Bank kartasi maydoni
            card_re = re.compile(r'\b(card[-_]?num|card[-_]?number|karta[-_]?raqam|pan[-_]?num|cc[-_]?number|card[-_]?pan|credit[-_]?card)\b|(?:karta\s*raqam|номер\s*карты|card\s*number|8600|9860)', re.IGNORECASE)
            cvv_re = re.compile(r'\b(cvv\d?|cvc\d?|card[-_]?cvv|security[-_]?code)\b', re.IGNORECASE)
            result["has_card_field"] = any(card_re.search(inp) or cvv_re.search(inp) for inp in input_tags)

            # 3. SMS kod maydoni
            otp_re = re.compile(r'\b(sms[-_]?kod|sms[-_]?code|tasdiqlash[-_]?kod|otp[-_]?code|sms[-_]?otp)\b|(?:sms\s*kod|tasdiqlash\s*kodi|код\s*из\s*смс|bir\s*martalik\s*kod)', re.IGNORECASE)
            result["has_otp_field"] = any(otp_re.search(inp) for inp in input_tags)

            # 4. Karta balansi maydoni (Firibgarlar qancha pul o'g'irlash mumkinligini bilish uchun kiritishni so'rashadi!)
            balance_re = re.compile(r'\b(balans|balance|karta[-_]?balans|ostatok|summa[-_]?na[-_]?karte|qoldiq)\b|(?:kartadagi\s*balans|kartadagi\s*qoldiq|баланс\s*карты|остаток\s*на\s*карте)', re.IGNORECASE)
            result["has_balance_field"] = any(balance_re.search(inp) for inp in input_tags)

            # 5. Yashirin avtospisanie belgilari HTML tarkibida
            if any(term in lower_html for term in ["avtospisanie", "rekurrent", "podpiska", "har oy kartadan", "avtomatik to'lov", "sinov muddati tugagach", "har 3 kunda", "1 rub", "1 so'm to'lov"]):
                result["has_hidden_subscription"] = True

            # 6. Soxta dostavka belgilari
            if any(term in lower_html for term in ["olx dostavka", "uzum dostavka", "cdek dostavka", "poluchit dengi", "pulni qabul qilib olish", "priem plateja"]):
                result["has_fake_delivery"] = True

    except Exception:
        result["fetch_success"] = False

    return result


async def analyze_url_or_text(raw_input: str) -> Dict[str, Any]:
    """URL yoki shubhali xabarni kompleks tekshirish (Chuqur Evristika + Fishing + Yashirin o'g'irliklar tahlili)."""
    urls = extract_urls(raw_input)
    risk_score = 0
    red_flags: List[str] = []
    positive_flags: List[str] = []
    detected_brand = None
    inspected_data = None
    target_display = raw_input[:100]
    matched_categories = set()

    # 1. Matndagi barcha xavf andozalarini tekshirish
    lower_input = raw_input.lower()
    for pattern, score_add, explanation, category in THREAT_PATTERNS:
        if re.search(pattern, lower_input, re.IGNORECASE):
            risk_score += score_add
            matched_categories.add(category)
            flag_entry = f"⚠️ {explanation}"
            if flag_entry not in red_flags:
                red_flags.append(flag_entry)

    # 2. Agar matnda havola(lar) bo'lsa
    if urls:
        first_url = urls[0]
        target_display = first_url
        parsed = urllib.parse.urlparse(first_url)
        domain = parsed.hostname or ""
        domain = domain.lower()
        if domain.startswith("www."):
            domain = domain[4:]

        # Rasmiy oq ro'yxat tekshiruvi
        if domain in TRUSTED_UZ_DOMAINS:
            # Agar rasmiy domen bo'lsa va matnda hech qanday tajovuzkor xavf bo'lmasa
            if not matched_categories:
                return {
                    "input": raw_input,
                    "target": domain,
                    "risk_score": 0,
                    "verdict": "safe",
                    "verdict_uz": "Xavfsiz va Ishonchli",
                    "summary_uz": f"Ushbu havola rasmiy va tasdiqlangan milliy tizimga tegishli: {TRUSTED_UZ_DOMAINS[domain]}.",
                    "red_flags": [],
                    "positive_flags": [f"✅ Rasmiy manzil: {TRUSTED_UZ_DOMAINS[domain]}"],
                    "details": {
                        "is_official": True,
                        "official_name": TRUSTED_UZ_DOMAINS[domain],
                        "extracted_urls": urls
                    }
                }
            else:
                positive_flags.append(f"ℹ️ Manzil rasmiy tizimga o'xshaydi ({TRUSTED_UZ_DOMAINS[domain]}), biroq matnda shubhali chaqiriqlar bor.")

        # Typosquatting / Brend o'g'irlash
        typo_result = check_typosquatting(domain)
        if typo_result:
            risk_score += 65
            detected_brand = typo_result["target_brand"]
            red_flags.append(f"🚨 {typo_result['type']}: {typo_result['detail']}")

        # Shubhali TLD zona
        tld = domain.split(".")[-1] if "." in domain else ""
        if tld in SUSPICIOUS_TLDS:
            risk_score += 35
            red_flags.append(f"⚠️ Shubhali domen zonasi (. {tld}): Bu hudud ko'pincha bir kunlik kiber-firibgarlik saytlari uchun qo'llaniladi.")

        # IP-manzil yoki ko'p darajali subdomen
        if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', domain):
            risk_score += 50
            red_flags.append("🚨 To'g'ridan-to'g'ri IP-manzilga yo'naltirilgan! Rasmiy kompaniyalar bunday havoladan foydalanmaydi.")

        if domain.count(".") >= 3:
            risk_score += 25
            red_flags.append("⚠️ Murakkab ko'p bosqichli subdomen: Firibgarlar haqiqiy manzilni yashirish maqsadida qo'llagan.")

        # Sahifani jonli xavfsiz skanerlash
        inspected_data = await inspect_webpage_content(first_url)
        if inspected_data["fetch_success"]:
            if inspected_data["has_card_field"]:
                risk_score += 45
                red_flags.append("🚨 Saytda bank kartasi ma'lumotlarini (PAN/CVV) kiritish shakli topildi!")
            if inspected_data["has_otp_field"]:
                risk_score += 55
                red_flags.append("🚨 Saytda SMS orqali keladigan bir martalik tasdiqlash kodini kiritish talab qilinmoqda! (Kartadagi pullarni to'liq o'g'irlash xavfi)")
            if inspected_data["has_balance_field"]:
                risk_score += 60
                red_flags.append("🚨 Sayt kartangizdagi joriy qoldiqni (balansni) so'ramoqda! Bu firibgarlar barcha pulingizni bir martada yechib olishi uchun qo'llanadigan xarakterli belgi!")
            if inspected_data["has_hidden_subscription"]:
                risk_score += 50
                red_flags.append("🚨 Sayt kodida yashirin avtospisanie va takroriy obuna to'lovlari (har oy/hafta pul yechish) shartlari aniqlandi!")
            if inspected_data["has_fake_delivery"]:
                risk_score += 50
                red_flags.append("🚨 Sayt soxta kuryerlik yetkazib berish (dostavka) niqobidan foydalanmoqda!")
            if inspected_data["has_password_field"] and typo_result:
                risk_score += 40
                red_flags.append("🚨 Qalbaki sahifada hisob parolini kiritish talab qilinmoqda!")

    # 3. Tashqi AI / Sotsial muhandislik tahlilchisi bilan integratsiya (llm_engine)
    try:
        from backend.security_engine.llm_engine import analyze_scam_text
        ai_analysis = await analyze_scam_text(raw_input)
        ai_score = ai_analysis.get("risk_score", 0)
        if ai_score > risk_score:
            risk_score = ai_score

        tactics = ai_analysis.get("manipulation_tactics", [])
        for tac in tactics:
            if tac and tac != "Ochiq manipulyatsiya aniqlanmadi":
                tac_flag = f"🧠 AI Tahlil: {tac}"
                if tac_flag not in red_flags:
                    red_flags.append(tac_flag)
    except Exception:
        pass

    # Xavf darajasini chegaralash (0 - 100)
    risk_score = min(max(risk_score, 0), 100)

    # Yakuniy Hukm
    if risk_score >= 70:
        verdict = "dangerous"
        verdict_uz = "Kritik Xavfli! (Firibgarlik / Pul o'g'irlash)"
        summary_uz = "DIQQAT! Ushbu xabar yoki havola kiber-firibgarlar tomonidan sizning kartangizdagi pullarni o'g'irlash yoki hisoblaringizni qo'lga kiritish uchun tuzilgan. Hech qanday ma'lumot kiritmang va pul o'tkazmang!"
    elif risk_score >= 40:
        verdict = "suspicious"
        verdict_uz = "Shubhali (Ehtiyot bo'ling)"
        summary_uz = "Xabarda bir nechta shubhali va noaniq belgilar aniqlandi. Tasdiqlanmagan manbalardan kelgan chaqiriqlarga ishonmang va begonalarga kodlarni bermang."
    else:
        verdict = "safe"
        verdict_uz = "Xavfsiz ko'rinadi"
        summary_uz = "Xabarda ochiq firibgarlik yoki yashirin o'g'irlik alomatlari aniqlanmadi. Shunga qaramay, kiber-gigiyena qoidalariga rioya qiling."

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
        "matched_categories": list(matched_categories),
        "details": {
            "extracted_urls": urls,
            "web_inspection": inspected_data
        }
    }
