from typing import Optional, List
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.database import get_db
from backend.models import CardBlacklist
from backend.security_engine.card_analyzer import analyze_card_number
from backend.security_engine.bot_inspector import analyze_telegram_bot_or_username

router = APIRouter(prefix="/api/tools", tags=["Security Tools"])

class CheckCardRequest(BaseModel):
    card_number: str


class CheckBotRequest(BaseModel):
    username: str


class QuizSubmitRequest(BaseModel):
    answers: List[int] # e.g. [1, 2, 0, 3, 1]


# Favqulodda SOS ma'lumotlar bazasi (O'zbekiston banklari va davlat organlari)
EMERGENCY_DATA = {
    "steps": [
        {
            "step": 1,
            "title_uz": "Kartani zudlik bilan bloklang!",
            "desc_uz": "Bank ilovangizga (Click, Payme, Uzum) kiring va kartani 'Bloklash' tugmasini bosing yoki bank koll-markaziga qo'ng'iroq qiling."
        },
        {
            "step": 2,
            "title_uz": "SMS va login parollarni yangilang!",
            "desc_uz": "Agar Telegram kodini yuborgan bo'lsangiz, Telegram sozlamalaridan 'Faol sessiyalar' bo'limiga kirib barcha boshqa qurilmalarni uzib tashlang va 2 bosqichli parolni (Two-Step Verification) yoqing."
        },
        {
            "step": 3,
            "title_uz": "Huquq-tartibot organlariga murojaat qiling!",
            "desc_uz": "Ichki Ishlar Vazirligi Kiberxavfsizlik markaziga (102 yoki 1102) qo'ng'iroq qiling yoki ariza bilan murojaat qiling. Skrinshotlar va cheklarni saqlab qo'ying."
        }
    ],
    "banks_contacts": [
        {"name": "Click O'zbekiston", "phone": "+998 71 202-01-01", "short": "71 202-01-01"},
        {"name": "Payme O'zbekiston", "phone": "+998 71 200-02-02", "short": "71 200-02-02"},
        {"name": "Uzum Bank", "phone": "+998 78 777-07-07", "short": "78 777-07-07"},
        {"name": "Xalq Banki", "phone": "1106", "short": "1106"},
        {"name": "Agrobank", "phone": "1216", "short": "1216"},
        {"name": "Kapitalbank", "phone": "+998 71 200-15-15", "short": "71 200-15-15"},
        {"name": "Ipak Yo'li Banki", "phone": "1296", "short": "1296"},
        {"name": "TBC Bank", "phone": "1150", "short": "1150"},
        {"name": "Anorbank", "phone": "1290", "short": "1290"},
        {"name": "O'zmilliybank (NBU)", "phone": "1344", "short": "1344"},
        {"name": "IIV Kiberxavfsizlik Markazi", "phone": "1102", "short": "1102 / 102"}
    ]
}

QUIZ_QUESTIONS = [
    {
        "id": 1,
        "question": "Sizga Click yoki Payme nomidan qo'ng'iroq qilib: 'Hisobingiz bloklandi, SMSdagi 6 talik kodni ayting' deyishdi. Nima qilasiz?",
        "options": [
            "Tezda kodni aytaman, aks holda pulim kuyib ketadi",
            "Kodni aytmayman va darhol go'shakni qo'yib, bankka o'zim qo'ng'iroq qilaman",
            "SMS kodning faqat oxirgi 3 ta raqamini aytaman",
            "Ular xavfsizlik xodimi bo'lgani uchun ishonaman"
        ],
        "correct": 1,
        "explanation_uz": "Bank yoki to'lov tizimi xodimlari HECH QACHON sizdan SMS tasdiqlash kodini so'ramaydi! Bu 100% firibgarlik."
    },
    {
        "id": 2,
        "question": "Telegramda tanishingizdan: 'Mening jiyanim tanlovda qatnashyapti, iltimos shu havolaga kirib ovoz bering' degan xabar keldi. Bu nima?",
        "options": [
            "Oddiy bolalar tanlovi, darhol kirib ovoz beraman",
            "Telegram hisobingizni o'g'irlash uchun tuzilgan fishing tuzog'i",
            "Telegramning yangi funksiyasi",
            "Do'stimga yordam berishim kerak"
        ],
        "correct": 1,
        "explanation_uz": "Soxta tanlovlar va ovoz berish bahonasida sizdan telefon raqam va Telegram kirish kodi so'raladi va hisobingiz o'g'irlanadi."
    },
    {
        "id": 3,
        "question": "Telegramda 'To'y_taklifnomasi.pdf.apk' degan fayl keldi. Uni ochish kerakmi?",
        "options": [
            "Ha, bu shunchaki chiroyli rasm yoki taklifnoma",
            "Yo'q! Kengaytmasi '.apk' bo'lgan fayl bu rasm emas, xavfli troyan dasturidir",
            "Faqat antivirus o'rnatilgan bo'lsa ochaman",
            "Wi-Fi ga ulanib keyin ochaman"
        ],
        "correct": 1,
        "explanation_uz": "Haqiqiy taklifnomalar hech qachon '.apk' bo'lmaydi. Bu ilova o'rnatilsa, kartangizdagi pullarni yechib oladi."
    },
    {
        "id": 4,
        "question": "Kredit shartnomasida 'Har bir kechiktirilgan kun uchun 1% penya to'lanadi' deyilgan. Bu qanchalik xavfli?",
        "options": [
            "Oddiy holat, hamma shunday qiladi",
            "Bu juda xavfli! Kuniga 1% yillik 365% jarima degani bo'lib, iste'molchini qarz botqog'iga botiradi",
            "Bank xohlagan foizini qo'yishga haqli",
            "1% juda kam summa"
        ],
        "correct": 1,
        "explanation_uz": "Kunlik 0.5% yoki 1% penya asossiz yirik moliyaviy tuzoq hisoblanadi."
    },
    {
        "id": 5,
        "question": "Internetda 'Prezident qaroriga asosan barcha fuqarolarga 650,000 so'm yordam berilmoqda' degan e'lon ko'rdingiz. Nima qilasiz?",
        "options": [
            "Darhol karta raqamimni kiritib pulni olaman",
            "Bu xabarni barcha guruhlarga tarqataman",
            "Bu soxta fishing ekani bilib, havolani ShieldGuard orqali tekshiraman yoki e'tibor bermayman",
            "Karta parolini ham kiritaman"
        ],
        "correct": 2,
        "explanation_uz": "Davlat to'lovlari hech qachon begona saytlarda karta ma'lumotlarini so'rash orqali tarqatilmaydi."
    }
]


@router.post("/check-card")
async def check_card(payload: CheckCardRequest, db: AsyncSession = Depends(get_db)):
    """Bank kartasi raqamini to'liq tekshirish (Format, emitent bank, qora ro'yxat)."""
    analysis = analyze_card_number(payload.card_number)

    # Qora ro'yxatda bor-yo'qligini tekshirish
    clean_card = "".join(filter(str.isdigit, payload.card_number))
    stmt = select(CardBlacklist).where(CardBlacklist.card_number == clean_card)
    res = await db.execute(stmt)
    scam_card = res.scalar_one_or_none()

    if scam_card:
        analysis["risk_score"] = 100
        analysis["verdict"] = "dangerous"
        analysis["is_in_blacklist"] = True
        analysis["scam_details"] = {
            "reason": scam_card.reason,
            "report_count": scam_card.report_count,
            "bank_name": scam_card.bank_name
        }
        analysis["warnings"].insert(0, f"🚨 DIQQAT: Ushbu karta ShieldGuard firibgarlar qora ro'yxatiga kiritilgan! Shikoyatlar: {scam_card.report_count} ta. Aslo pul o'tkazmang!")
    else:
        analysis["is_in_blacklist"] = False

    return analysis


@router.post("/check-bot")
async def check_bot(payload: CheckBotRequest):
    """Telegram bot username tekshiruvi."""
    return analyze_telegram_bot_or_username(payload.username)


@router.get("/emergency-guide")
async def get_emergency_guide():
    """Favqulodda yordam yo'riqnomasi va banklar ro'yxati."""
    return EMERGENCY_DATA


@router.get("/quiz-questions")
async def get_quiz():
    """Kiber-savodxonlik testi savollari."""
    return [
        {
            "id": q["id"],
            "question": q["question"],
            "options": q["options"]
        } for q in QUIZ_QUESTIONS
    ]


@router.post("/quiz-submit")
async def submit_quiz(payload: QuizSubmitRequest):
    """Test natijalarini hisoblash va sertifikat berish."""
    correct_count = 0
    feedback = []

    for i, q in enumerate(QUIZ_QUESTIONS):
        user_choice = payload.answers[i] if i < len(payload.answers) else -1
        is_right = (user_choice == q["correct"])
        if is_right:
            correct_count += 1
        feedback.append({
            "question_id": q["id"],
            "is_correct": is_right,
            "correct_option": q["options"][q["correct"]],
            "explanation": q["explanation_uz"]
        })

    percent = int((correct_count / len(QUIZ_QUESTIONS)) * 100)

    if percent >= 80:
        level = "🛡️ Kiber-Qalqon Mutaxassisi"
        badge_color = "emerald"
        message = "A'lo daraja! Siz firibgarlarning deyarli barcha tuzoqlarini osongina fosh qila olasiz."
    elif percent >= 60:
        level = "⚠️ Hushyor Foydalanuvchi"
        badge_color = "amber"
        message = "Yaxshi ko'rsatkich, biroq ayrim murakkab fishing tuzoqlarida ehtiyotkorlikni oshirishingiz kerak."
    else:
        level = "🚨 Yuqori Xavf Guruhida"
        badge_color = "rose"
        message = "Diqqat! Kiber-xavfsizlik bo'yicha bilimlaringiz yetarli emas, firibgarlar tuzog'iga tushib qolish ehtimolingiz yuqori."

    return {
        "correct_count": correct_count,
        "total": len(QUIZ_QUESTIONS),
        "percentage": percent,
        "level": level,
        "badge_color": badge_color,
        "message_uz": message,
        "detailed_feedback": feedback
    }
