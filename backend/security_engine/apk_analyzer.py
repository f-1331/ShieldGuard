import os
import re
import zipfile
import hashlib
from typing import Dict, Any, List

DANGEROUS_PERMISSIONS = {
    "android.permission.BIND_ACCESSIBILITY_SERVICE": {
        "score": 50,
        "name_uz": "Maxsus imkoniyatlar xizmati (Accessibility Service)",
        "risk_uz": "🚨 Eng xavfli troyan ruxsati! Ilova ekranni to'liq nazorat qila oladi, terilgan parollarni o'qiydi va sizning roziligingizsiz bankdan pul o'tkaza oladi."
    },
    "android.permission.RECEIVE_SMS": {
        "score": 40,
        "name_uz": "SMS xabarlarni qabul qilish",
        "risk_uz": "🚨 Bank va to'lov tizimlaridan kelgan bir martalik tasdiqlash kodlarini yashirincha o'g'irlash xavfi!"
    },
    "android.permission.READ_SMS": {
        "score": 40,
        "name_uz": "SMS xabarlarni o'qish",
        "risk_uz": "🚨 Telefoningizdagi barcha shaxsiy yozishmalar va bank xabarlarini troyan serveriga jo'natish xavfi!"
    },
    "android.permission.SEND_SMS": {
        "score": 30,
        "name_uz": "SMS yuborish",
        "risk_uz": "⚠️ Foydalanuvchiga bildirmasdan pullik raqamlarga yoki tanishlaringizga virus tarqatish maqsadida SMS yuborishi mumkin."
    },
    "android.permission.SYSTEM_ALERT_WINDOW": {
        "score": 35,
        "name_uz": "Boshqa ilovalar ustidan oyna chiqarish (Overlay)",
        "risk_uz": "🚨 Soxta bank oynasini (Click/Payme nusxasini) haqiqiy ilova ustiga chiqarib, karta kodi va parolingizni o'g'irlash xavfi!"
    },
    "android.permission.QUERY_ALL_PACKAGES": {
        "score": 25,
        "name_uz": "O'rnatilgan barcha ilovalarni ko'rish",
        "risk_uz": "⚠️ Telefonda aynan qaysi bank ilovalari (Click, Payme, Uzum) borligini aniqlash uchun razvedka qiladi."
    },
    "android.permission.RECEIVE_BOOT_COMPLETED": {
        "score": 20,
        "name_uz": "Telefon yoqilganda avtomatik ishga tushish",
        "risk_uz": "⚠️ Qurilma o'chib-yoqilgandan so'ng darhol fonda yashirin ishlashni davom ettiradi."
    },
    "android.permission.READ_CONTACTS": {
        "score": 20,
        "name_uz": "Kontaktlarni o'qish",
        "risk_uz": "⚠️ Kontaktlaringiz ro'yxatini ko'chirib olib, barcha yaqinlaringizga fishing havolalar tarqatishda foydalanadi."
    },
    "android.permission.RECORD_AUDIO": {
        "score": 25,
        "name_uz": "Mikrofon orqali ovoz yozib olish",
        "risk_uz": "⚠️ Yashirin tarzda suhbatlarni yozib olish xavfi."
    },
    "android.permission.CAMERA": {
        "score": 20,
        "name_uz": "Kameradan foydalanish",
        "risk_uz": "⚠️ Yashirin tarzda rasm va video olish imkoniyati."
    }
}

# Ijtimoiy muhandislik bilan nomlangan zararli fayl andozalari
SOCIAL_ENGINEERING_FILE_PATTERNS = [
    (r"to['`]?y\s*taklifnoma", "To'y taklifnomasi niqobi ostidagi xavfli troyan (APK)"),
    (r"taklifnoma", "Taklifnoma nomi bilan niqoblangan ilova"),
    (r"foto[_\s-]*albom", "Fotoalbom niqobi ostidagi troyan"),
    (r"rasm", "Rasm niqobi ostidagi dastur"),
    (r"bonus|aksiya|sovg['`]?a", "Bonus yoki sovg'a va'da qiluvchi soxta ilova"),
    (r"kredit|mikroqarz", "Tezkor kredit va'da qiluvchi firibgar ilova"),
    (r"click|payme|uzum", "O'zbekiston to'lov tizimlari nomi bilan soxtalashtirilgan APK"),
    (r"update|obnovleniye", "Tizim yangilanishi niqobidagi zararli dastur")
]

SUSPICIOUS_DOUBLE_EXTENSIONS = [
    ".pdf.apk", ".jpg.apk", ".png.apk", ".jpeg.apk",
    ".mp4.apk", ".zip.apk", ".doc.apk", ".docx.apk",
    ".jpg.exe", ".pdf.exe", ".png.exe"
]


def extract_strings_from_bytes(data: bytes, min_len: int = 4) -> List[str]:
    """Binar ma'lumotlar (masalan, AndroidManifest.xml) ichidan o'qilishi mumkin bo'lgan matnlarni ajratadi."""
    result = []
    # ASCII va UTF-8
    ascii_strings = re.findall(rb'[a-zA-Z0-9_.\-\$]{4,}', data)
    for s in ascii_strings:
        try:
            result.append(s.decode('utf-8', errors='ignore'))
        except Exception:
            pass

    # UTF-16LE (Android binar XML da ko'p uchraydi)
    utf16_strings = re.findall(rb'(?:[\x20-\x7e]\x00){4,}', data)
    for s in utf16_strings:
        try:
            result.append(s.decode('utf-16le', errors='ignore'))
        except Exception:
            pass

    return result


def inspect_apk_content(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """APK fayl ichki arxitekturasi va ruxsatlarini tahlil qiladi."""
    found_permissions: List[str] = []
    has_manifest = False
    has_dex = False
    package_name = "Noma'lum"

    try:
        import io
        with zipfile.ZipFile(io.BytesIO(file_bytes), 'r') as zf:
            file_list = zf.namelist()

            if "AndroidManifest.xml" in file_list:
                has_manifest = True
                manifest_data = zf.read("AndroidManifest.xml")
                extracted_strings = extract_strings_from_bytes(manifest_data)

                # Android ruxsatlarini qidirish
                for s in extracted_strings:
                    if "android.permission." in s:
                        # Toza ruxsat nomini ajratib olish
                        match = re.search(r'android\.permission\.[A-Za-z0-9_]+', s)
                        if match:
                            perm = match.group(0)
                            if perm not in found_permissions:
                                found_permissions.append(perm)

                    # Paket nomini aniqlashga urinish
                    if "package" in s.lower() or (re.match(r'^[a-z][a-z0-9_]+(\.[a-z][a-z0-9_]+)+$', s) and "android" not in s):
                        if package_name == "Noma'lum" and len(s) > 6:
                            package_name = s

            # classes.dex mavjudligi
            for fn in file_list:
                if fn.endswith(".dex"):
                    has_dex = True
                    break

    except zipfile.BadZipFile:
        return {
            "is_valid_apk": False,
            "error": "Fayl haqiqiy APK (ZIP) arxivi emas yoki shikastlangan."
        }
    except Exception as e:
        return {
            "is_valid_apk": False,
            "error": f"Faylni o'qishda xatolik: {str(e)}"
        }

    return {
        "is_valid_apk": True,
        "has_manifest": has_manifest,
        "has_dex": has_dex,
        "package_name": package_name,
        "permissions": found_permissions
    }


def analyze_file_security(filename: str, file_bytes: bytes) -> Dict[str, Any]:
    """Fayl xavfsizligini tekshiradi (APK troyanlar, ikki qavatli kengaytmalar, xavfli ruxsatlar)."""
    clean_name = filename.strip()
    lower_name = clean_name.lower()
    file_size_mb = round(len(file_bytes) / (1024 * 1024), 2)
    sha256_hash = hashlib.sha256(file_bytes).hexdigest()

    risk_score = 0
    red_flags: List[str] = []
    danger_permissions_detected: List[Dict[str, str]] = []
    social_engineering_detected: List[str] = []

    # 1. Ikki qavatli kengaytma (Double Extension) tekshiruvi
    for d_ext in SUSPICIOUS_DOUBLE_EXTENSIONS:
        if lower_name.endswith(d_ext):
            risk_score += 60
            red_flags.append(f"🚨 Niqoblangan ikki qavatli kengaytma aniqlandi ({d_ext})! Foydalanuvchini aldab, zararli dasturni oddiy rasm yoki hujjatdek ko'rsatishga urinish.")
            break

    # 2. Ijtimoiy muhandislik nomlari (Social Engineering)
    for pattern, warning in SOCIAL_ENGINEERING_FILE_PATTERNS:
        if re.search(pattern, lower_name, re.IGNORECASE):
            risk_score += 45
            social_engineering_detected.append(warning)
            red_flags.append(f"🚨 Ijtimoiy manipulyatsiya: {warning}")
            break

    # 3. Agar fayl .apk bo'lsa yoki binar tahlilda ZIP bo'lsa
    is_apk = lower_name.endswith(".apk") or (len(file_bytes) > 4 and file_bytes[:4] == b"PK\x03\x04")
    apk_data = None

    if is_apk:
        apk_data = inspect_apk_content(file_bytes, clean_name)
        if apk_data.get("is_valid_apk"):
            perms = apk_data.get("permissions", [])

            # Xavfli ruxsatlarni solishtirish
            for p in perms:
                if p in DANGEROUS_PERMISSIONS:
                    meta = DANGEROUS_PERMISSIONS[p]
                    risk_score += meta["score"]
                    danger_permissions_detected.append({
                        "permission": p,
                        "name_uz": meta["name_uz"],
                        "risk_uz": meta["risk_uz"]
                    })
                    red_flags.append(meta["risk_uz"])

            # Agar bu Telegram orqali yuborilgan notanish APK bo'lsa va unda SMS/Accessibility bo'lsa
            if any(p in perms for p in ["android.permission.BIND_ACCESSIBILITY_SERVICE", "android.permission.RECEIVE_SMS"]):
                risk_score = max(risk_score, 90)

    # Risk ballini cheklash
    risk_score = min(max(risk_score, 0), 100)

    # Yakuniy xulosa
    if risk_score >= 70:
        verdict = "dangerous"
        verdict_uz = "Kritik Xavfli! (Troyan / Virus)"
        summary_uz = "Ushbu fayl telefoningizga o'rnatilsa, SMS-kodlaringizni, bank ilovalaringizni to'liq nazorat qilib, kartangizdagi pullarni yechib olishi mumkin. TEZDA O'CHIRIB TASHLANG!"
    elif risk_score >= 40:
        verdict = "suspicious"
        verdict_uz = "Shubhali fayl"
        summary_uz = "Faylda xavfli ruxsatlar yoki shubhali nomlanish aniqlandi. Noma'lum manbadan olingan bo'lsa o'rnatish qat'iyan tavsiya etilmaydi."
    else:
        verdict = "safe"
        verdict_uz = "Xavf aniqlanmadi"
        summary_uz = "Faylda ma'lum bo'lgan zararli troyan belgilari topilmadi."

    return {
        "filename": clean_name,
        "file_size_mb": file_size_mb,
        "sha256": sha256_hash,
        "is_apk": is_apk,
        "risk_score": risk_score,
        "verdict": verdict,
        "verdict_uz": verdict_uz,
        "summary_uz": summary_uz,
        "red_flags": red_flags,
        "dangerous_permissions": danger_permissions_detected,
        "social_engineering": social_engineering_detected,
        "apk_metadata": apk_data
    }
