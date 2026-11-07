import re

# Zero-width va ko'rinmas belgilar
ZERO_WIDTH_CHARS = [
    '\u200b', '\u200c', '\u200d', '\ufeff', '\u00ad',
    '\u200e', '\u200f', '\u202a', '\u202b', '\u202c', '\u202d', '\u202e'
]

# Kirill - Lotin gomogliflari (Firibgarlar filtrlarni aldash uchun aralashtirib yozadi)
CYRILLIC_TO_LATIN_HOMOGLYPHS = {
    'а': 'a', 'А': 'A',
    'в': 'b', 'В': 'B',
    'е': 'e', 'Е': 'E',
    'к': 'k', 'К': 'K',
    'м': 'm', 'М': 'M',
    'н': 'h', 'Н': 'H',
    'о': 'o', 'О': 'O',
    'р': 'p', 'Р': 'P',
    'с': 'c', 'С': 'C',
    'т': 't', 'Т': 'T',
    'у': 'y', 'У': 'Y',
    'х': 'x', 'Х': 'X',
    'і': 'i', 'І': 'I',
    'ј': 'j', 'Ј': 'J',
    'ѕ': 's', 'Ѕ': 'S',
    'і': 'i', 'ї': 'i'
}

# L33t speak almashtirishlari (so'zlarni niqoblash)
LEET_SPEAK_MAP = {
    '@': 'a',
    '0': 'o',
    '1': 'l',
    '3': 'e',
    '4': 'a',
    '5': 's',
    '7': 't',
    '8': 'b',
    '$': 's'
}

def strip_zero_width_chars(text: str) -> str:
    """Matn ichidagi barcha ko'rinmas zero-width va boshqaruv belgilarini tozalaydi."""
    for ch in ZERO_WIDTH_CHARS:
        text = text.replace(ch, '')
    return text

def normalize_homoglyphs(text: str) -> str:
    """Kirill va lotin aralashtirilgan harflarni yagona standart lotin alifbosiga keltiradi."""
    chars = []
    for char in text:
        chars.append(CYRILLIC_TO_LATIN_HOMOGLYPHS.get(char, char))
    return "".join(chars)

def normalize_leet_speak(text: str) -> str:
    """L33t speak belgilarini (masalan, p@yme -> payme, c1ick -> click) normallashtiradi."""
    # Faqat so'z ichida kelganda almashtiramiz
    words = text.split()
    normalized_words = []
    for w in words:
        # Agar URL yoki email bo'lsa teginmaymiz
        if "://" in w or "@" in w and "." in w and not w.startswith("@"):
            normalized_words.append(w)
            continue
        nw = []
        for ch in w:
            nw.append(LEET_SPEAK_MAP.get(ch, ch))
        normalized_words.append("".join(nw))
    return " ".join(normalized_words)

def deep_clean_scam_text(text: str) -> str:
    """Firibgarlar filtrlarni aylanib o'tish uchun qo'llaydigan barcha niqoblarni yechib, toza matn hosil qiladi."""
    if not text:
        return ""
    # 1. Ko'rinmas belgilarni olib tashlash
    cleaned = strip_zero_width_chars(text)
    # 2. Gomogliflarni tekislash
    cleaned = normalize_homoglyphs(cleaned)
    # 3. L33t speakni tozalash
    cleaned = normalize_leet_speak(cleaned)
    # 4. Ortiqcha bo'shliqlarni birlashtirish
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned
