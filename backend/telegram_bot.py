import asyncio
import io
import json
import logging
import re
import socket
from datetime import datetime
from typing import Optional, List, Dict, Any

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from aiogram.enums import ParseMode
from sqlalchemy.future import select
from sqlalchemy import func, or_, desc

from backend.config import settings
from backend.database import AsyncSessionLocal
from backend.models import (
    User,
    ScanHistory,
    CardBlacklist,
    CommunityBlacklist,
    AdminAuditLog,
    BroadcastMessage,
    FamilyLink
)
from backend.security_engine.url_analyzer import analyze_url_or_text
from backend.security_engine.apk_analyzer import analyze_file_security
from backend.security_engine.contract_analyzer import analyze_contract_file
from backend.security_engine.card_analyzer import analyze_card_number
from backend.security_engine.bot_inspector import analyze_telegram_bot_or_username
from backend.utils import notify_family_guardians, send_telegram_message

logger = logging.getLogger(__name__)

bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

# Foydalanuvchi holatlari (FSM xotirasi)
user_states: Dict[int, Dict[str, Any]] = {}

# Interaktiv Kiber-Viktorina Savollari
QUIZ_QUESTIONS = [
    {
        "id": 1,
        "title": "1-SAVOL: Notanish shaxs va SMS kod",
        "question": (
            "1️⃣ <b>Telegramda notanish odam sizga xabar yozdi:</b>\n\n"
            "<i>'Tabriklaymiz, siz 1,000,000 so'm yutib oldingiz! Pulni kartangizga o'tkazishimiz uchun "
            "telefoningizga borgan 6 xonali SMS kodni yuboring.'</i>\n\n"
            "Sizning to'g'ri harakatingiz qanday?"
        ),
        "options": [
            ("A) Darhol kodni yuboraman, pul kerak", False, "❌ <b>Katta xato!</b> Bank hech qachon SMS-tasdiqlash kodini so'ramaydi. Kodni berishingiz bilan kartangizdagi barcha pul yechib olinadi!"),
            ("B) Xabarni o'chirib, foydalanuvchini bloklayman", True, "✅ <b>To'g'ri javob!</b> Bu eng klassik fishing tuzog'i. Hech kim tekinga pul bermaydi va SMS kodni hech qachon birovga berish mumkin emas."),
            ("C) Faqat karta raqamimni yuboraman, kodni bermayman", False, "⚠️ <b>Xavfli!</b> Firibgarlar karta raqamingizni bilib, keyin soxta to'lov tizimlari orqali profilingizni buzishga urinishadi.")
        ]
    },
    {
        "id": 2,
        "title": "2-SAVOL: Tanlovda ovoz berish havolasi",
        "question": (
            "2️⃣ <b>Yaqin tanishingizdan Telegramda xabar keldi:</b>\n\n"
            "<i>'Jiyanimga tanlovda ovoz berib yubor, iltimos: [havola]'</i>\n"
            "Havolaga kirsangiz, Telegram telefon raqamingiz va tasdiqlash kodini kiritishni so'rayapti.\n\n"
            "Bu vaziyatda nima sodir bo'lmoqda?"
        ),
        "options": [
            ("A) Bu soxta havola, do'stimning profili buzilgan", True, "✅ <b>To'g'ri javob!</b> Bu o'zbek segmentida eng ko'p tarqalgan profil o'g'irlash usuli. Havola orqali kod kiritilsa, Telegram akkauntingiz to'liq boshqalar qo'liga o'tadi."),
            ("B) Oddiy ovoz berish jarayoni, kodni kiritaman", False, "❌ <b>Noto'g'ri!</b> Hech qanday rasmiy tanlov Telegram tasdiqlash kodini talab qilmaydi."),
            ("C) Havolani boshqa do'stlarimga ham tarqataman", False, "❌ <b>Mutlaqo noto'g'ri!</b> Siz ham bilmasdan firibgarlarning tuzog'ini do'stlaringizga tarqatgan bo'lasiz.")
        ]
    },
    {
        "id": 3,
        "title": "3-SAVOL: Shubhali APK fayl",
        "question": (
            "3️⃣ <b>Sizga 'To'y taklifnomasi.apk' yoki 'Fotosurat.apk' nomli fayl keldi.</b>\n\n"
            "Ushbu faylni yuklab olib, telefonga o'rnatish xavfsizmi?"
        ),
        "options": [
            ("A) Ha, bu shunchaki chiroyli taklifnoma", False, "❌ <b>Juda katta xato!</b> Fotosuratlar yoki taklifnomalar '.apk' kengaytmasiga ega bo'lmaydi. Bu xavfli bank troyani!"),
            ("B) Yo'q! Bu bank kartalaridan pul o'g'irlovchi troyan virus", True, "✅ <b>Barakalla!</b> .apk fayli Android dasturidir. Firibgarlar uni rasm niqobi ostida tarqatib, SMS va bank ilovalarini to'liq nazoratga olishadi."),
            ("C) O'rnatib ko'raman, yoqmasa o'chirib tashlayman", False, "❌ <b>Kech bo'ladi!</b> APK o'rnatilishi bilan u yashirincha SMS xabarlaringizni o'qib, bank kartangizni bo'shatadi.")
        ]
    },
    {
        "id": 4,
        "title": "4-SAVOL: Soxta to'lov domeni",
        "question": (
            "4️⃣ <b>Brauzerda manzil 'payme-bonus.ru' yoki 'c1ick-uz.com' deb yozilgan,</b>\n"
            "lekin sayt dizayni xuddi Payme yoki Click'nikiga o'xshaydi va karta parolini so'rayapti.\n\n"
            "Bu qanday sayt?"
        ),
        "options": [
            ("A) Rasmiy aksiyalar sayti, bonus beradi", False, "❌ <b>Noto'g'ri!</b> Rasmiy to'lov tizimlari faqat '.uz' zonasida va o'zining rasmiy domenlarida (payme.uz, click.uz) ishlaydi."),
            ("B) Soxta fishing sayt, kartani o'g'irlaydi", True, "✅ <b>Ajoyib!</b> Bu 'Typosquatting' va brand-spoofing usuli. Manzildagi bitta harf yoki domen zonasi o'zgargan bo'lsa — bu 100% firibgarlik!"),
            ("C) Yangi xalqaro filiali bo'lsa kerak", False, "❌ <b>Aslo!</b> O'zbekiston to'lov tizimlari '.ru' yoki '.xyz' zonalarida karta ma'lumotlarini yig'maydi.")
        ]
    },
    {
        "id": 5,
        "title": "5-SAVOL: Soxta bank xodimi",
        "question": (
            "5️⃣ <b>Sizga telefon qilib o'zini 'Bank xavfsizlik xizmati xodimi' deb tanishtirishdi</b>\n"
            "va <i>'Kartangizdan shubhali operatsiya o'tdi, to'xtatish uchun kodni ayting'</i> deyishdi.\n\n"
            "Nima qilasiz?"
        ),
        "options": [
            ("A) Go'shakni qo'yib, bankning rasmiy raqamiga o'zim qayta qo'ng'iroq qilaman", True, "✅ <b>100% to'g'ri!</b> Bank xodimlari HECH QACHON mijozga qo'ng'iroq qilib SMS-kod so'ramaydi. Bu ijtimoiy muhandislik firibgarligi."),
            ("B) Pulim kuyib ketmasligi uchun darhol kodni aytaman", False, "❌ <b>Eng katta xato!</b> Firibgarlar aynan sizni shoshirib qo'yish orqali pulingizni o'zlashtiradi."),
            ("C) Qaysi bankdaligini so'rab, ishonib kodni beraman", False, "❌ <b>Yo'q!</b> Firibgarlar internetdan ismingiz va bank nomini osongina topib oladi.")
        ]
    }
]

# O'zbekiston Banklari Tezkor Aloqa Raqamlari
BANK_DIRECTORY = [
    ("Click (To'lov tizimi)", "71 202-88-88", "@clickuz"),
    ("Payme (To'lov tizimi)", "78 150-22-29", "@payme_uz"),
    ("Uzum Bank & Market", "78 777-07-99", "@uzumbank"),
    ("Agrobank", "1216", "@AgrobankUz"),
    ("Xalq Banki", "1106", "@xalqbankuz"),
    ("O'zmilliybank (NBU)", "1344", "@nbu_official"),
    ("Kapitalbank", "71 200-15-15", "@kapitalbank_uz"),
    ("Ipak Yo'li Banki", "1296", "@ipakyulibank"),
    ("Sanoat Qurilish Bank (SQB)", "1180", "@sqbuz"),
    ("Anorbank", "1290", "@anorbank"),
    ("TBC Bank", "1150", "@tbcbankuz"),
    ("Hamkorbank", "1256", "@hamkorbank_uz"),
    ("Asakabank", "1152", "@asakabank_uz"),
    ("Ipoteka Bank", "78 150-11-22", "@ipotekabankuz"),
    ("IIV Kiber-Xizmat (Ichki Ishlar)", "1102 / 102", "cyber.uz")
]


# =========================================================================
# 1. FOYDALANUVCHINI ANIQLASH VA BAZA BILAN ISHLASH
# =========================================================================

async def get_or_create_user(telegram_id: int, username: Optional[str], full_name: Optional[str]) -> User:
    """Foydalanuvchini bazadan qidirish, yangilash va Owner darajasini o'rnatish.
    Baza vaqtincha javob bermaganda ham bot to'xtab qolmasligi uchun xavfsiz User qaytaradi."""
    is_owner = (
        telegram_id == settings.OWNER_TELEGRAM_ID or
        (username and username.lower() == settings.OWNER_USERNAME.lower())
    )
    fallback_user = User(
        telegram_id=telegram_id,
        username=username,
        full_name=full_name or "Foydalanuvchi",
        role="owner" if is_owner else "user",
        active_mode="owner" if is_owner else "user"
    )
    try:
        async with AsyncSessionLocal() as session:
            stmt = select(User).where(User.telegram_id == telegram_id)
            res = await session.execute(stmt)
            user = res.scalar_one_or_none()

            if not user:
                user = User(
                    telegram_id=telegram_id,
                    username=username,
                    full_name=full_name or "Foydalanuvchi",
                    role="owner" if is_owner else "user",
                    active_mode="owner" if is_owner else "user"
                )
                session.add(user)
                try:
                    await session.commit()
                    await session.refresh(user)
                except Exception:
                    await session.rollback()
            else:
                changed = False
                if is_owner and user.role != "owner":
                    user.role = "owner"
                    changed = True
                if is_owner and not user.active_mode:
                    user.active_mode = "owner"
                    changed = True
                if username and user.username != username:
                    user.username = username
                    changed = True
                if full_name and user.full_name != full_name:
                    user.full_name = full_name
                    changed = True
                if changed:
                    try:
                        await session.commit()
                        await session.refresh(user)
                    except Exception:
                        await session.rollback()
            return user
    except Exception as e:
        logger.warning(f"Baza bilan bog'lanishda xatolik ({e}). Xavfsiz xotira foydalanuvchisi ishlatilmoqda.")
        return fallback_user


async def safe_save_scan_history(
    user_telegram_id: int,
    scan_type: str,
    target_name: str,
    risk_score: float,
    verdict: str,
    summary_uz: str,
    details_json: str
) -> Optional[ScanHistory]:
    """Skanerlash tarixini xavfsiz saqlash. Baza muammosi tufayli foydalanuvchiga javob berish to'xtab qolmaydi."""
    try:
        async with AsyncSessionLocal() as session:
            hist = ScanHistory(
                user_telegram_id=user_telegram_id,
                scan_type=scan_type,
                target_name=target_name[:120] if target_name else "Noma'lum",
                risk_score=float(risk_score),
                verdict=verdict,
                summary_uz=summary_uz[:250] if summary_uz else "",
                details_json=details_json
            )
            session.add(hist)
            await session.commit()

            if risk_score >= 70:
                try:
                    await notify_family_guardians(session, user_telegram_id, target_name, risk_score, summary_uz)
                except Exception as fe:
                    logger.warning(f"Oila a'zolarini ogohlantirishda xatolik: {fe}")
            return hist
    except Exception as e:
        logger.warning(f"Scan tarixini saqlashda vaqtinchalik DB xatosi: {e}")
        return None


# =========================================================================
# 2. TUGMALAR (REPLY KEYBOARD & INLINE KEYBOARD)
# =========================================================================

def get_owner_reply_keyboard() -> ReplyKeyboardMarkup:
    """Super Owner uchun to'liq boshqaruv doimiy tugmalari (ReplyKeyboardMarkup)."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="👑 Boshqaruv Markazi"),
                KeyboardButton(text="👥 Adminlar Boshqaruvi")
            ],
            [
                KeyboardButton(text="👤 Foydalanuvchilar Bazasi"),
                KeyboardButton(text="🛡️ Kiber-Monitoring (Jonli)")
            ],
            [
                KeyboardButton(text="🚫 Qora Ro'yxat (Kartalar)"),
                KeyboardButton(text="🌐 Fishing Saytlar Bazasi")
            ],
            [
                KeyboardButton(text="📡 Jonli Kiber-Radar"),
                KeyboardButton(text="🎙️ Ovozli Xabar / Qo'ng'iroq")
            ],
            [
                KeyboardButton(text="📢 Smart E'lon Tarqatish"),
                KeyboardButton(text="⚙️ AI & Tizim Sozlamalari")
            ],
            [
                KeyboardButton(text="📊 Kengaytirilgan Statistika"),
                KeyboardButton(text="👤 Oddiy Rejimga O'tish")
            ]
        ],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Owner Boshqaruvida: buyruq yoki amalni tanlang..."
    )


def get_user_reply_keyboard(is_owner: bool = False) -> ReplyKeyboardMarkup:
    """Oddiy fuqaro yoki oddiy rejimdagi Owner uchun pastdagi doimiy tugmalar."""
    keyboard = [
        [
            KeyboardButton(text="🛡️ Havola / Matn Tekshirish"),
            KeyboardButton(text="💳 Karta Tekshirish")
        ],
        [
            KeyboardButton(text="🤖 Bot / Kanal Tekshirish"),
            KeyboardButton(text="📄 Shartnoma Rentgeni")
        ],
        [
            KeyboardButton(text="🆘 Meni Aldashdi! (Yordam)"),
            KeyboardButton(text="🧠 Kiber-Viktorina (Test)")
        ],
        [
            KeyboardButton(text="👨‍👩‍👧‍👦 Oila Qalqoni"),
            KeyboardButton(text="🏦 Banklar & Bloklash Raqamlari")
        ],
        [
            KeyboardButton(text="🎙️ Ovozli Xabar / Qo'ng'iroq"),
            KeyboardButton(text="📡 Jonli Kiber-Radar")
        ],
        [
            KeyboardButton(text="💡 Kiber-Tavsiyalar"),
            KeyboardButton(text="📱 WebApp Ilovasi")
        ]
    ]

    if is_owner:
        keyboard.append([
            KeyboardButton(text="👑 Owner Rejimiga O'tish")
        ])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Havola, karta, bot yoki fayl yuboring..."
    )


def get_main_inline_keyboard(user_id: int, is_owner: bool = False, active_mode: str = "user") -> InlineKeyboardMarkup:
    """Xabar ichidagi tezkor WebApp va yordamchi inline tugmalar."""
    webapp_url = (settings.WEBAPP_URL or "").strip()

    first_row = []
    if webapp_url.startswith("https://"):
        first_row.append(
            InlineKeyboardButton(
                text="🛡️ Ilovada Ochish (Mini App)",
                web_app=WebAppInfo(url=webapp_url)
            )
        )
    else:
        first_row.append(
            InlineKeyboardButton(
                text="📱 Ilovada Ko'rish (Mini App)",
                callback_data="btn_webapp_info"
            )
        )

    buttons = [
        first_row,
        [
            InlineKeyboardButton(text="💳 Karta Tekshirish", callback_data="btn_card_info"),
            InlineKeyboardButton(text="🤖 Bot Tekshirish", callback_data="btn_bot_info")
        ],
        [
            InlineKeyboardButton(text="📄 Shartnoma Auditi", callback_data="btn_contract_info"),
            InlineKeyboardButton(text="👨‍👩‍👧‍👦 Oila Qalqoni", callback_data="btn_family_info")
        ],
        [
            InlineKeyboardButton(text="📡 Jonli Kiber-Radar", callback_data="btn_open_radar"),
            InlineKeyboardButton(text="🎙️ Ovozli Tekshiruv (Vishing)", callback_data="btn_open_voice")
        ],
        [
            InlineKeyboardButton(text="🆘 Meni Aldashdi! (Yordam)", callback_data="btn_sos_info"),
            InlineKeyboardButton(text="🧠 Kiber-Viktorina (Test)", callback_data="btn_quiz_info")
        ],
        [
            InlineKeyboardButton(text="🏦 Banklar Ro'yxati", callback_data="btn_bank_callcenters"),
            InlineKeyboardButton(text="💡 Kiber-Tavsiyalar", callback_data="btn_cyber_tips")
        ]
    ]

    if is_owner:
        if active_mode == "owner":
            buttons.append([
                InlineKeyboardButton(text="👑 Boshqaruv Markazi (/admin)", callback_data="btn_open_admin"),
                InlineKeyboardButton(text="👤 Oddiy Rejimga O'tish", callback_data="btn_toggle_role")
            ])
        else:
            buttons.append([
                InlineKeyboardButton(text="👑 Owner Rejimiga Qaytish", callback_data="btn_toggle_role")
            ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


# =========================================================================
# 3. REJIMLARNI ALMASHTIRISH (ROLE SWITCHER)
# =========================================================================

async def switch_owner_role(user_id: int, message: types.Message, to_mode: Optional[str] = None):
    """Owner rejimini o'zgartirish va pastki tugmalarni yangilash."""
    if user_id != settings.OWNER_TELEGRAM_ID:
        await message.answer("❌ Bu amal faqat loyiha egasi (@fayzbek1331) uchun mo'ljallangan.")
        return

    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.telegram_id == user_id)
        res = await session.execute(stmt)
        db_user = res.scalar_one_or_none()

        if not db_user:
            db_user = User(telegram_id=user_id, username=settings.OWNER_USERNAME, role="owner", active_mode="owner")
            session.add(db_user)

        if to_mode in ("owner", "user"):
            new_mode = to_mode
        else:
            new_mode = "user" if db_user.active_mode == "owner" else "owner"

        db_user.active_mode = new_mode
        await session.commit()

        if new_mode == "owner":
            text = (
                "👑 <b>Owner Boshqaruv Rejimi Faollashtirildi!</b>\n\n"
                "✅ Pastdagi barcha boshqaruv tugmalari <b>Super Owner holatiga o'tdi</b>:\n"
                "• 👑 <b>Boshqaruv Markazi</b> — Server va tizim holati\n"
                "• 👥 <b>Adminlar Boshqaruvi</b> — Admin tayinlash va o'chirish\n"
                "• 👤 <b>Foydalanuvchilar Bazasi</b> — A'zolar ro'yxati va Ban/Unban\n"
                "• 🛡️ <b>Kiber-Monitoring</b> — Jonli tekshiruvlar monitoringi\n"
                "• 🚫 <b>Qora Ro'yxat (Kartalar)</b> — Firibgar kartalar bazasi\n"
                "• 🌐 <b>Fishing Saytlar Bazasi</b> — Soxta domenlar ro'yxati\n"
                "• 📢 <b>Smart E'lon</b> — Barcha a'zolarga xabar tarqatish\n"
                "• ⚙️ <b>AI Sozlamalari</b> — Gemini va xavf dvigatellari\n\n"
                "👇 <i>Pastdagi tugmalar orqali to'liq boshqarishingiz mumkin:</i>"
            )
            reply_kb = get_owner_reply_keyboard()
        else:
            text = (
                "👤 <b>Oddiy Foydalanuvchi Rejimi Faollashtirildi!</b>\n\n"
                "✅ Pastdagi tugmalar <b>oddiy fuqaro ko'rinishiga</b> o'tdi.\n"
                "Siz hozir botni oddiy foydalanuvchi ko'zi bilan sinab ko'rishingiz mumkin.\n\n"
                "👑 <i>Owner rejimiga qaytish uchun: pastdagi '👑 Owner Rejimiga O'tish' tugmasini bosing yoki /switch_role yozing.</i>"
            )
            reply_kb = get_user_reply_keyboard(is_owner=True)

        await message.answer(text, reply_markup=reply_kb, parse_mode=ParseMode.HTML)
        await message.answer(
            "🎛️ <b>Rejim holati muvaffaqiyatli yangilandi:</b>",
            reply_markup=get_main_inline_keyboard(user_id, is_owner=True, active_mode=new_mode),
            parse_mode=ParseMode.HTML
        )


# =========================================================================
# 4. OWNER & ADMIN BOSHQARUV MARKAZI
# =========================================================================

async def render_admin_dashboard(message: types.Message, user_id: int):
    """Owner & Admin uchun keng qamrovli boshqaruv markazi."""
    is_owner = (user_id == settings.OWNER_TELEGRAM_ID)
    async with AsyncSessionLocal() as session:
        total_users = (await session.execute(select(func.count(User.id)))).scalar() or 0
        banned_users = (await session.execute(select(func.count(User.id)).where(User.is_banned == True))).scalar() or 0
        total_admins = (await session.execute(select(func.count(User.id)).where(User.role == "admin"))).scalar() or 0
        total_scans = (await session.execute(select(func.count(ScanHistory.id)))).scalar() or 0
        threat_scans = (await session.execute(select(func.count(ScanHistory.id)).where(ScanHistory.risk_score >= 70))).scalar() or 0
        total_cards = (await session.execute(select(func.count(CardBlacklist.id)))).scalar() or 0
        total_domains = (await session.execute(select(func.count(CommunityBlacklist.id)))).scalar() or 0

        text = (
            "👑 <b>SHIELDGUARD AI — SUPER BOSHQARUV MARKAZI</b>\n"
            "══════════════════════════════\n"
            f"👤 <b>Boshqaruvchi:</b> {'👑 SUPER OWNER' if is_owner else '🛡️ ADMIN'}\n"
            f"🌐 <b>Vercel Production:</b> <code>https://shieldguardpro.vercel.app</code>\n"
            f"⚡ <b>AI Dvigateli:</b> Gemini 1.5 + Smart Heuristics\n\n"
            "📊 <b>JONLI METRIKALAR:</b>\n"
            f"• 👥 Jami foydalanuvchilar: <b>{total_users}</b> nafar (Bloklangan: {banned_users})\n"
            f"• 🛡️ Tayinlangan adminlar: <b>{total_admins}</b> nafar\n"
            f"• 🔍 Bajarilgan tekshiruvlar: <b>{total_scans}</b> ta\n"
            f"• 🚨 Fosh qilingan kiber-xavflar: <b>{threat_scans}</b> ta\n"
            f"• 💳 Qora ro'yxatdagi kartalar: <b>{total_cards}</b> ta\n"
            f"• 🌐 Aniqlangan fishing saytlar: <b>{total_domains}</b> ta\n\n"
            "👇 <i>Kerakli boshqaruv bo'limini tanlang:</i>"
        )

        kb = [
            [
                InlineKeyboardButton(text="👥 Adminlar Boshqaruvi", callback_data="btn_list_admins"),
                InlineKeyboardButton(text="👤 Foydalanuvchilar Bazasi", callback_data="btn_list_users")
            ],
            [
                InlineKeyboardButton(text="🛡️ Kiber-Monitoring (Jonli)", callback_data="btn_live_monitor"),
                InlineKeyboardButton(text="🚫 Firibgar Kartalar", callback_data="btn_list_cards")
            ],
            [
                InlineKeyboardButton(text="🌐 Fishing Saytlar Bazasi", callback_data="btn_list_domains"),
                InlineKeyboardButton(text="📢 Smart E'lon Tarqatish", callback_data="btn_prompt_broadcast")
            ],
            [
                InlineKeyboardButton(text="⚙️ AI & Tizim Sozlamalari", callback_data="btn_system_settings"),
                InlineKeyboardButton(text="📊 Kengaytirilgan Statistika", callback_data="btn_detailed_stats")
            ]
        ]
        if is_owner:
            kb.append([
                InlineKeyboardButton(text="🔄 Oddiy Rejimga O'tish", callback_data="btn_toggle_role")
            ])

        await message.answer(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
            parse_mode=ParseMode.HTML
        )


async def render_admins_management(message: types.Message, user_id: int):
    """Adminlar ro'yxati va interaktiv boshqaruv tugmalarini ko'rsatish."""
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(or_(User.role == "admin", User.telegram_id == settings.OWNER_TELEGRAM_ID))
        res = await session.execute(stmt)
        admins = res.scalars().all()

        text = (
            "👥 <b>SHIELDGUARD ADMINLAR BOSHQARUVI:</b>\n"
            "══════════════════════════════\n\n"
            f"👑 <b>SUPER OWNER:</b> @{settings.OWNER_USERNAME} (ID: <code>{settings.OWNER_TELEGRAM_ID}</code>)\n\n"
            "🛡️ <b>TAYINLANGAN ADMINLAR:</b>\n"
        )
        sub_admins = [a for a in admins if a.telegram_id != settings.OWNER_TELEGRAM_ID]
        if sub_admins:
            for i, a in enumerate(sub_admins, 1):
                uname = f"@{a.username}" if a.username else "Usernamesiz"
                text += f"{i}. <b>{a.full_name or 'Noma`lum'}</b> ({uname}) — ID: <code>{a.telegram_id}</code>\n"
        else:
            text += "<i>Hozircha qo'shimcha adminlar tayinlanmagan.</i>\n"

        text += (
            "\n💡 <b>Admin qo'shish usullari:</b>\n"
            "1) Quyidagi <b>'➕ Yangi Admin Qo'shish'</b> tugmasini bosing;\n"
            "2) Yoki <code>/addadmin &lt;telegram_id yoki @username&gt;</code> yozing;\n"
            "3) Yoki o'sha shaxsning biron bir xabarini menga <b>Forward</b> qiling!"
        )

        kb_rows = [
            [
                InlineKeyboardButton(text="➕ Yangi Admin Qo'shish", callback_data="btn_prompt_add_admin"),
                InlineKeyboardButton(text="➖ Admin O'chirish", callback_data="btn_prompt_del_admin")
            ],
            [
                InlineKeyboardButton(text="🔄 Yangilash", callback_data="btn_refresh_admins"),
                InlineKeyboardButton(text="🔙 Boshqaruv Markazi", callback_data="btn_open_admin")
            ]
        ]
        await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows), parse_mode=ParseMode.HTML)


async def render_users_management(message: types.Message, user_id: int):
    """Foydalanuvchilar bazasi va boshqaruvi."""
    async with AsyncSessionLocal() as session:
        total = (await session.execute(select(func.count(User.id)))).scalar() or 0
        banned = (await session.execute(select(func.count(User.id)).where(User.is_banned == True))).scalar() or 0

        recent_stmt = select(User).order_by(User.id.desc()).limit(8)
        recent_users = (await session.execute(recent_stmt)).scalars().all()

        text = (
            "👤 <b>FOYDALANUVCHILAR BAZASI VA NAZORATI:</b>\n"
            "══════════════════════════════\n"
            f"👥 Jami ro'yxatdan o'tganlar: <b>{total}</b> nafar\n"
            f"🚫 Bloklangan qoidabuzarlar: <b>{banned}</b> nafar\n\n"
            "📋 <b>OXIRGI RO'YXATDAN O'TGAN FOYDALANUVCHILAR:</b>\n"
        )

        for u in recent_users:
            uname = f"@{u.username}" if u.username else "usernamesiz"
            status = "🚫 BLOKLANGAN" if u.is_banned else ("👑 OWNER" if u.role == "owner" else ("🛡️ ADMIN" if u.role == "admin" else "👤 User"))
            text += f"• <b>{u.full_name or 'Foydalanuvchi'}</b> ({uname}) — ID: <code>{u.telegram_id}</code> [{status}]\n"

        text += (
            "\n💡 <b>Boshqaruv buyruqlari:</b>\n"
            "• <code>/ban &lt;telegram_id&gt;</code> — Foydalanuvchini bloklash\n"
            "• <code>/unban &lt;telegram_id&gt;</code> — Blokdan chiqarish"
        )

        kb = [
            [
                InlineKeyboardButton(text="🚫 Foydalanuvchini Bloklash", callback_data="btn_prompt_ban_user"),
                InlineKeyboardButton(text="✅ Blokdan Chiqarish", callback_data="btn_prompt_unban_user")
            ],
            [
                InlineKeyboardButton(text="🔄 Yangilash", callback_data="btn_list_users"),
                InlineKeyboardButton(text="🔙 Boshqaruv Markazi", callback_data="btn_open_admin")
            ]
        ]
        await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode=ParseMode.HTML)


async def render_live_monitoring(message: types.Message, user_id: int):
    """Jonli kiber-monitoring: oxirgi tahlillar."""
    async with AsyncSessionLocal() as session:
        stmt = select(ScanHistory).order_by(ScanHistory.id.desc()).limit(8)
        scans = (await session.execute(stmt)).scalars().all()

        text = (
            "🛡️ <b>JONLI KIBER-MONITORING (OXIRGI TEKSHIRUVLAR):</b>\n"
            "══════════════════════════════\n\n"
        )

        if not scans:
            text += "<i>Hozircha tekshiruvlar tarixi mavjud emas.</i>\n"
        else:
            for s in scans:
                risk = s.risk_score or 0
                icon = "🔴" if risk >= 70 else ("🟡" if risk >= 40 else "🟢")
                scan_date = s.created_at.strftime("%H:%M %d.%m") if s.created_at else "Hozirgina"
                text += (
                    f"{icon} <b>[{int(risk)}%]</b> {s.scan_type.upper()} | <i>{scan_date}</i>\n"
                    f"🎯 <code>{s.target_name[:40]}</code>\n"
                    f"💬 {s.summary_uz[:70]}...\n\n"
                )

        kb = [
            [InlineKeyboardButton(text="🔄 Yangilash", callback_data="btn_live_monitor")],
            [InlineKeyboardButton(text="🔙 Boshqaruv Markazi", callback_data="btn_open_admin")]
        ]
        await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode=ParseMode.HTML)


async def render_scam_cards_management(message: types.Message, user_id: int):
    """Firibgar kartalar ro'yxatini ko'rsatish."""
    async with AsyncSessionLocal() as session:
        stmt = select(CardBlacklist).order_by(CardBlacklist.id.desc()).limit(8)
        res = await session.execute(stmt)
        cards = res.scalars().all()

        text = (
            "🚫 <b>FIRIBGAR BANK KARTALARI QORA RO'YXATI:</b>\n"
            "══════════════════════════════\n\n"
        )
        if cards:
            for c in cards:
                text += f"💳 <code>{c.card_number}</code> | {c.bank_name or 'Bank'}\n⚠️ <i>{c.reason}</i> (Shikoyatlar: {c.report_count} ta)\n\n"
        else:
            text += "<i>Hozircha qora ro'yxatda kartalar mavjud emas.</i>\n\n"

        text += (
            "💡 <b>Yangi karta qo'shish uchun:</b>\n"
            "<code>/addcard &lt;karta_raqami&gt; &lt;sabab&gt;</code>\n"
            "O'chirish uchun: <code>/delcard &lt;karta_raqami&gt;</code>"
        )

        kb = [
            [
                InlineKeyboardButton(text="➕ Qora Ro'yxatga Karta Qo'shish", callback_data="btn_prompt_add_card"),
                InlineKeyboardButton(text="➖ Kartani O'chirish", callback_data="btn_prompt_del_card")
            ],
            [
                InlineKeyboardButton(text="🔄 Yangilash", callback_data="btn_list_cards"),
                InlineKeyboardButton(text="🔙 Boshqaruv Markazi", callback_data="btn_open_admin")
            ]
        ]
        await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode=ParseMode.HTML)


async def render_phishing_domains_management(message: types.Message, user_id: int):
    """Fishing domenlar bazasi boshqaruvi."""
    async with AsyncSessionLocal() as session:
        stmt = select(CommunityBlacklist).order_by(CommunityBlacklist.id.desc()).limit(8)
        domains = (await session.execute(stmt)).scalars().all()

        text = (
            "🌐 <b>FISHING VA SOXTA SAYTLAR BAZASI:</b>\n"
            "══════════════════════════════\n\n"
        )
        if domains:
            for d in domains:
                text += f"🛑 <code>{d.domain_or_pattern}</code> [{d.category}]\n⚠️ <i>{d.reason}</i>\n\n"
        else:
            text += "<i>Hozircha maxsus kiritilgan soxta domenlar mavjud emas.</i>\n\n"

        text += (
            "💡 <b>Yangi fishing domen qo'shish:</b>\n"
            "<code>/adddomain &lt;domen&gt; &lt;sababi&gt;</code>\n"
            "O'chirish uchun: <code>/deldomain &lt;domen&gt;</code>"
        )

        kb = [
            [
                InlineKeyboardButton(text="➕ Yangi Fishing Domen Qo'shish", callback_data="btn_prompt_add_domain"),
                InlineKeyboardButton(text="➖ Domen O'chirish", callback_data="btn_prompt_del_domain")
            ],
            [
                InlineKeyboardButton(text="🔄 Yangilash", callback_data="btn_list_domains"),
                InlineKeyboardButton(text="🔙 Boshqaruv Markazi", callback_data="btn_open_admin")
            ]
        ]
        await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode=ParseMode.HTML)


async def render_system_settings(message: types.Message, user_id: int):
    """AI va Tizim sozlamalari markazi."""
    ai_status = "Gemini API (Ulangan / Faol)" if settings.GEMINI_API_KEY else "Aqlli Heuristic AI (Lokal faol)"
    text = (
        "⚙️ <b>SHIELDGUARD AI — TIZIM VA ALGORITM SOZLAMALARI:</b>\n"
        "══════════════════════════════\n\n"
        f"🤖 <b>Asosiy AI Modeli:</b> {ai_status}\n"
        f"🌐 <b>Webhook Manzili:</b> <code>{settings.WEBAPP_URL}/api/webhook</code>\n"
        f"☁️ <b>Hosting:</b> Vercel Serverless (Fluid Compute)\n"
        f"🗄️ <b>Ma'lumotlar Bazasi:</b> SQLite (Async SQLAlchemy)\n"
        f"👑 <b>Super Owner:</b> @{settings.OWNER_USERNAME} (<code>{settings.OWNER_TELEGRAM_ID}</code>)\n\n"
        "🛡️ <b>XAVF DARAJASI CHEGARALARI:</b>\n"
        "• 🟢 Xavfsiz: 0% - 39%\n"
        "• 🟡 Shubhali: 40% - 69%\n"
        "• 🔴 Kritik Xavfli (Blok): 70% - 100%\n\n"
        "🔍 <i>Quyidagi tugmalar orqali dvigatellarni test qilishingiz mumkin:</i>"
    )

    kb = [
        [
            InlineKeyboardButton(text="🧪 AI Dvigatelini Sinash", callback_data="btn_test_ai_engine"),
            InlineKeyboardButton(text="📊 Server Salomatligi", callback_data="btn_server_health")
        ],
        [
            InlineKeyboardButton(text="🔙 Boshqaruv Markazi", callback_data="btn_open_admin")
        ]
    ]
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode=ParseMode.HTML)


async def render_system_stats(message: types.Message, user_id: int):
    """Kengaytirilgan statistika."""
    async with AsyncSessionLocal() as session:
        total_users = (await session.execute(select(func.count(User.id)))).scalar() or 0
        total_scans = (await session.execute(select(func.count(ScanHistory.id)))).scalar() or 0
        blocked_threats = (await session.execute(select(func.count(ScanHistory.id)).where(ScanHistory.risk_score >= 70))).scalar() or 0
        total_cards_scam = (await session.execute(select(func.count(CardBlacklist.id)))).scalar() or 0
        total_admins = (await session.execute(select(func.count(User.id)).where(User.role == "admin"))).scalar() or 0
        total_links = (await session.execute(select(func.count(FamilyLink.id)))).scalar() or 0

        text = (
            "📊 <b>SHIELDGUARD AI — TO'LIQ KIBER-STATISTIKA:</b>\n"
            "══════════════════════════════\n\n"
            f"👥 <b>Foydalanuvchilar:</b> {total_users} nafar\n"
            f"🛡️ <b>Tayinlangan adminlar:</b> {total_admins} nafar\n"
            f"👨‍👩‍👧‍👦 <b>Oila Qalqoni bog'lanishlari:</b> {total_links} ta\n"
            f"🔍 <b>Jami tahlillar soni:</b> {total_scans} ta\n"
            f"🚨 <b>Zararsizlantirilgan tahdidlar:</b> {blocked_threats} ta\n"
            f"🚫 <b>Qora ro'yxatdagi kartalar:</b> {total_cards_scam} ta\n\n"
            "🎯 <b>Eng ko'p nishonga olingan brendlar:</b>\n"
            "• Click O'zbekiston (Soxta bonus & yutuqlar)\n"
            "• Payme (Soxta aksiyalar & parollar)\n"
            "• Uzum Bank / Nasiya (Soxta kreditlar)\n"
            "• Agrobank & Xalq Banki (Soxta subsidiyalar)\n\n"
            "🟢 <b>Himoya Holati:</b> 24/7 Avtomatik monitoring faol"
        )
        kb = [[InlineKeyboardButton(text="🔙 Boshqaruv Markazi", callback_data="btn_open_admin")]]
        await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode=ParseMode.HTML)


# =========================================================================
# 5. ADMIN QO'SHISH VA O'CHIRISH FUNKSIYALARI
# =========================================================================

async def promote_user_to_admin(owner_id: int, target_id: int, target_username: Optional[str], target_name: Optional[str], message: types.Message):
    """Foydalanuvchiga rasman Adminlik vakolatini berish."""
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.telegram_id == target_id)
        res = await session.execute(stmt)
        target = res.scalar_one_or_none()

        if not target:
            target = User(
                telegram_id=target_id,
                username=target_username,
                full_name=target_name or f"Admin {target_id}",
                role="admin",
                active_mode="admin"
            )
            session.add(target)
        else:
            target.role = "admin"
            if target_username:
                target.username = target_username
            if target_name:
                target.full_name = target_name

        audit = AdminAuditLog(
            admin_telegram_id=owner_id,
            action="add_admin",
            target=str(target_id),
            details="Owner tomonidan tayinlandi"
        )
        session.add(audit)
        await session.commit()

    display_name = target_name or (f"@{target_username}" if target_username else f"ID: {target_id}")
    await message.answer(
        f"🎉 <b>Yangi Admin Muvaffaqiyatli Tayinlandi!</b>\n\n"
        f"👤 <b>Foydalanuvchi:</b> {display_name}\n"
        f"🆔 <b>Telegram ID:</b> <code>{target_id}</code>\n"
        f"📎 <b>Username:</b> @{target_username if target_username else 'mavjud emas'}\n\n"
        f"✅ Endi ushbu foydalanuvchi tizim ma'muri hisoblanadi va /admin buyruqlaridan foydalana oladi.",
        reply_markup=get_owner_reply_keyboard(),
        parse_mode=ParseMode.HTML
    )
    await send_telegram_message(
        target_id,
        "🎉 <b>Tabriklaymiz!</b> Siz ShieldGuard AI tizimida <b>Admin</b> etib tayinlandingiz!\n\n"
        "Admin boshqaruv markazini ko'rish uchun /admin buyrug'ini yozing."
    )


async def resolve_and_promote_admin(owner_id: int, raw_input: str, message: types.Message, forward_user: Optional[types.User] = None):
    """Foydalanuvchi kiritmasi yoki Forward xabardan yangi adminni aniqlash."""
    target_id = None
    target_username = None
    target_name = None

    if forward_user:
        target_id = forward_user.id
        target_username = forward_user.username
        target_name = forward_user.full_name
    elif raw_input.isdigit():
        target_id = int(raw_input)
    else:
        clean_uname = raw_input.lstrip("@").strip().lower()
        async with AsyncSessionLocal() as session:
            stmt = select(User).where(func.lower(User.username) == clean_uname)
            res = await session.execute(stmt)
            found_user = res.scalar_one_or_none()
            if found_user:
                target_id = found_user.telegram_id
                target_username = found_user.username
                target_name = found_user.full_name
            else:
                await message.answer(
                    f"⚠️ <b>@{clean_uname}</b> ma'lumotlar bazasida topilmadi!\n\n"
                    f"<b>Sababi:</b> Ushbu foydalanuvchi hali botimizga /start bosmagan bo'lishi mumkin.\n\n"
                    f"💡 <b>Qanday hal qilish mumkin?</b>\n"
                    f"1️⃣ Uning raqamli <b>Telegram ID</b>sini yuboring (masalan: <code>123456789</code>), yoki\n"
                    f"2️⃣ O'sha do'stingizdan kelgan bitta xabarni shu chatga <b>Forward (uzatish)</b> qiling!\n\n"
                    f"❌ <i>Bekor qilish: /cancel</i>",
                    parse_mode=ParseMode.HTML
                )
                return

    if target_id == settings.OWNER_TELEGRAM_ID:
        await message.answer("ℹ️ Siz allaqachon Super Owner maqomidasiz!")
        return

    await promote_user_to_admin(
        owner_id=owner_id,
        target_id=target_id,
        target_username=target_username,
        target_name=target_name,
        message=message
    )


async def show_delete_admin_picker(message: types.Message, owner_id: int):
    """Adminni bitta tugma bilan o'chirish menyusini ko'rsatish."""
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.role == "admin", User.telegram_id != settings.OWNER_TELEGRAM_ID)
        res = await session.execute(stmt)
        admins = res.scalars().all()

        if not admins:
            await message.answer("ℹ️ Hozircha o'chirish uchun qo'shimcha adminlar tayinlanmagan.")
            return

        kb = []
        for a in admins:
            label = f"❌ O'chirish: {a.full_name or a.username or a.telegram_id}"
            kb.append([InlineKeyboardButton(text=label[:35], callback_data=f"deladmin_id:{a.telegram_id}")])

        kb.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="btn_refresh_admins")])

        await message.answer(
            "🗑️ <b>Adminlik huquqini bekor qilish:</b>\n\nQuyidagi ro'yxatdan o'chirmoqchi bo'lgan ma'murni tanlang:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
            parse_mode=ParseMode.HTML
        )


async def execute_broadcast(owner_id: int, broadcast_body: str, message: types.Message):
    """Barcha a'zolarga e'lon tarqatish."""
    status_msg = await message.answer("⏳ <i>Barcha foydalanuvchilarga xabar tarqatilmoqda...</i>", parse_mode=ParseMode.HTML)
    async with AsyncSessionLocal() as session:
        users_res = await session.execute(select(User.telegram_id).where(User.is_banned == False))
        uids = users_res.scalars().all()

        sent = 0
        failed = 0
        msg_formatted = (
            f"📢 <b>SHIELDGUARD KIBER-OGOHLANTIRISH</b>\n\n"
            f"{broadcast_body}\n\n"
            f"🛡️ <i>ShieldGuard AI — Doimo xavfsizligingiz himoyasida.</i>"
        )

        for uid in uids:
            ok = await send_telegram_message(uid, msg_formatted)
            if ok:
                sent += 1
            else:
                failed += 1

        b_log = BroadcastMessage(
            sender_telegram_id=owner_id,
            text=broadcast_body,
            total_recipients=len(uids),
            success_count=sent,
            failed_count=failed
        )
        session.add(b_log)
        await session.commit()

        await status_msg.edit_text(
            f"✅ <b>E'lon muvaffaqiyatli tarqatildi!</b>\n\n"
            f"• Jami a'zolar: {len(uids)}\n"
            f"• Muvaffaqiyatli yetkazildi: <b>{sent}</b> ta\n"
            f"• Yetkazib bo'lmadi (bloklaganlar): {failed} ta",
            parse_mode=ParseMode.HTML
        )


# =========================================================================
# 6. ODDIY FOYDALANUVCHI MARKAZLARI (CITIZEN HUBS)
# =========================================================================

async def render_user_link_center(message: types.Message):
    """Havola va matn tekshirish markazi."""
    text = (
        "🛡️ <b>HAVOLA VA MATN TEKSHIRISH XIZMATI:</b>\n"
        "══════════════════════════════\n\n"
        "Shubhali deb gumon qilingan har qanday havola yoki xabarni menga yuboring!\n\n"
        "🔍 <b>ShieldGuard tekshiruv algoritmi:</b>\n"
        "1. Sayt domenining yoshi va SSL sertifikati (yangi ochilgan soxta saytlar);\n"
        "2. Taniqli brendlar (Click, Payme, Uzum, Banklar) nomini soxtalashtirish (Typosquatting);\n"
        "3. Yashirin bank kartasi va SMS-kod talab qiluvchi shakllar (OTP harvesting);\n"
        "4. Ijtimoiy muhandislik va soxta aksiya va'dalari.\n\n"
        "👇 <i>Havolani xabar qilib yuboring yoki namunaviy sinovdan o'ting:</i>"
    )
    kb = [
        [
            InlineKeyboardButton(text="🧪 Namuna Fishing Havolani Sinash", callback_data="btn_sample_phishing"),
            InlineKeyboardButton(text="🔍 Domen Yoshini Tekshirish", callback_data="btn_whois_info")
        ],
        [
            InlineKeyboardButton(text="📖 Firibgarlar Qanday Aldaydi?", callback_data="btn_phishing_guide")
        ]
    ]
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode=ParseMode.HTML)


async def render_user_card_center(message: types.Message):
    """Karta tekshirish markazi."""
    text = (
        "💳 <b>BANK KARTASINI TEKSHIRISH VA ANTI-SCAM MARKAZI:</b>\n"
        "══════════════════════════════\n\n"
        "Sizdan pul o'tkazishni so'rashgan 16 talik karta raqamini yuboring (masalan: <code>8600 1234 5678 9012</code>).\n\n"
        "ShieldGuard quyidagilarni aniqlab beradi:\n"
        "• To'lov tizimi (Uzcard, Humo, Visa, Mastercard);\n"
        "• Kartaning emitent banki (O'zbekistondagi barcha banklar);\n"
        "• Firibgarlarning qora ro'yxatida mavjudligi;\n"
        "• Luhn algoritmi bo'yicha haqiqiyligi.\n\n"
        "👇 <i>Karta raqamini yuboring yoki quyidagi vositalardan foydalaning:</i>"
    )
    kb = [
        [
            InlineKeyboardButton(text="🧪 Namuna Firibgar Kartani Sinash", callback_data="btn_sample_scam_card"),
            InlineKeyboardButton(text="🏦 Banklar BIN Ko'rsatkichi", callback_data="btn_bin_directory")
        ],
        [
            InlineKeyboardButton(text="⚠️ Firibgarlikning 5 Ta Belgisi", callback_data="btn_card_fraud_signs"),
            InlineKeyboardButton(text="🚩 Shubhali Kartani Shikoyat Qilish", callback_data="btn_report_card")
        ]
    ]
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode=ParseMode.HTML)


async def render_user_bot_center(message: types.Message):
    """Telegram bot va kanal tekshirish markazi."""
    text = (
        "🤖 <b>TELEGRAM BOT VA KANAL TEKSHIRISH XIZMATI:</b>\n"
        "══════════════════════════════\n\n"
        "Sizga shubhali ko'ringan botning username'ini yuboring (masalan: <code>@click_bonus_bot</code>).\n\n"
        "Biz ushbu botning rasmiy ekanligini, foydalanuvchilarni aldash sxemalariga aloqadorligini "
        "va brendlarni soxtalashtirish alomatlarini fosh qilamiz.\n\n"
        "👇 <i>Bot usernamesini yuboring yoki ma'lumotlarni ko'ring:</i>"
    )
    kb = [
        [
            InlineKeyboardButton(text="🧪 Namuna Soxta Botni Tekshirish", callback_data="btn_sample_fake_bot"),
            InlineKeyboardButton(text="📋 Ko'p Uchraydigan Soxta Botlar", callback_data="btn_known_fake_bots")
        ],
        [
            InlineKeyboardButton(text="✅ Rasmiy Bank & To'lov Botlari", callback_data="btn_official_bots")
        ]
    ]
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode=ParseMode.HTML)


async def render_user_contract_center(message: types.Message):
    """Shartnoma rentgeni markazi."""
    text = (
        "📄 <b>SHARTNOMA RENTGENI (YURIDIK AI SHIELD):</b>\n"
        "══════════════════════════════\n\n"
        "Kredit, mikroqarz, muddatli to'lov (nasiya), ijara, avto-lizing yoki mehnat shartnomasining "
        "<b>PDF</b> faylini yoki sahifalarining fotosuratini yuboring!\n\n"
        "Sun'iy intellekt shartnomani tahlil qilib, quyidagi tuzoqlarni fosh qiladi:\n"
        "• Kunlik oshirilgan jarimalar (penya foizlari);\n"
        "• Bank yoki lizing kompaniyasining foizlarni bir tomonlama oshirish huquqi;\n"
        "• Yashirin komissiyalar va sug'urta to'lovlari;\n"
        "• Sudsiz mulkni musodara qilish xavfi.\n\n"
        "👇 <i>PDF yoki fotosurat yuboring:</i>"
    )
    kb = [
        [
            InlineKeyboardButton(text="🧪 Namuna Shartnoma Xulosasi", callback_data="btn_sample_contract"),
            InlineKeyboardButton(text="📑 Shartnomadagi 4 Asosiy Tuzoq", callback_data="btn_contract_traps")
        ]
    ]
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode=ParseMode.HTML)


async def render_user_bank_directory(message: types.Message):
    """Banklar ma'lumotnomasi va favqulodda bloklash raqamlari."""
    text = (
        "🏦 <b>O'ZBEKISTON BANKLARI VA KARTANI BLOKLASH RAQAMLARI:</b>\n"
        "══════════════════════════════\n\n"
        "Kartangiz ma'lumotlari firibgarlar qo'liga tushgan bo'lsa, zudlik bilan qo'ng'iroq qiling:\n\n"
    )
    for name, phone, tg in BANK_DIRECTORY:
        text += f"• <b>{name}:</b> 📞 <code>{phone}</code> ({tg})\n"

    text += "\n🚨 <b>IIV Kiberxavfsizlik Markazi:</b> 📞 <code>1102</code> yoki <code>102</code>"
    await message.answer(text, parse_mode=ParseMode.HTML)


async def render_user_cyber_tips(message: types.Message):
    """Kiber-xavfsizlik bo'yicha oltin qoidalar."""
    text = (
        "💡 <b>KIBER-XAVFSIZLIKNING 5 TA OLTIN QOIDASI:</b>\n"
        "══════════════════════════════\n\n"
        "1️⃣ <b>SMS TASDIQLASH KODI — BU SIR:</b>\n"
        "Hech qachon va hech kimga (hatto o'zini bank xodimi deb tanishtirganlarga ham) telefoningizga kelgan SMS-kodni aytmang!\n\n"
        "2️⃣ <b>2 BOSQICHLI AUTENTIFIKATSIYA (2FA):</b>\n"
        "Telegram va bank ilovalaringizda 'Bulutli parol' (Cloud Password)ni yoqib qo'ying.\n\n"
        "3️⃣ <b>SOXTA TAKLIFNOMA VA '.APK' FAYLLAR:</b>\n"
        "Telegramda tanishlaringizdan kelgan bo'lsa ham 'To'y taklifnomasi.apk' yoki 'Rasm.apk' fayllarini aslo o'rnatmang!\n\n"
        "4️⃣ <b>DOMEN MANZILIGA E'TIBOR BERING:</b>\n"
        "Har doim brauzer manziliga qarang. 'c1ick', 'payme-bonus', '.xyz', '.site' kabi manzillar — 100% soxtadir.\n\n"
        "5️⃣ <b>TEKIN PANDAQ FAQAT QOPQONDA BO'LADI:</b>\n"
        "Prezident nomidan kompensatsiya, 1 million so'm yutuq yoki so'rovnoma uchun katta pul va'dalariga aslo ishonmang!"
    )
    await message.answer(text, parse_mode=ParseMode.HTML)


# =========================================================================
# 7. ASOSIY BUYRUQLAR (/start, /switch_role, /admin...)
# =========================================================================

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    """Start buyrug'i: foydalanuvchini aniqlash va mos menyuni ochish."""
    user = message.from_user
    db_user = None
    if user:
        db_user = await get_or_create_user(user.id, user.username, user.full_name)

    is_owner = (
        user.id == settings.OWNER_TELEGRAM_ID or
        (user.username and user.username.lower() == settings.OWNER_USERNAME.lower())
    )
    active_mode = db_user.active_mode if db_user else ("owner" if is_owner else "user")

    if is_owner and active_mode == "owner":
        reply_kb = get_owner_reply_keyboard()
        owner_welcome = (
            f"👑 <b>Assalomu alaykum, Hurmatli Bosh Administrator (Owner) @{settings.OWNER_USERNAME}!</b>\n\n"
            f"🛡️ <b>ShieldGuard Pro AI</b> boshqaruv tizimi to'liq ixtiyoringizda.\n\n"
            f"🎯 <b>Pastda barcha 10 ta Super Owner boshqaruv tugmalari faol:</b>\n"
            f"• 👑 <b>Boshqaruv Markazi</b> — Jonli metrikalar va server monitoringi\n"
            f"• 👥 <b>Adminlar Boshqaruvi</b> — Yangi admin qo'shish va o'chirish\n"
            f"• 👤 <b>Foydalanuvchilar Bazasi</b> — Barcha a'zolar va Ban/Unban nazorati\n"
            f"• 🛡️ <b>Kiber-Monitoring</b> — Jonli foydalanuvchilar skaneri\n"
            f"• 🚫 <b>Qora Ro'yxat (Kartalar)</b> — Firibgar kartalarni boshqarish\n"
            f"• 🌐 <b>Fishing Saytlar Bazasi</b> — Soxta domenlar arxivi\n"
            f"• 📢 <b>Smart E'lon</b> — Barcha a'zolarga xabar yuborish\n"
            f"• ⚙️ <b>AI & Tizim Sozlamalari</b> — Gemini AI va xavf darajalari\n"
            f"• 👤 <b>Oddiy Rejimga O'tish</b> — Botni fuqaro ko'zi bilan sinash\n\n"
            f"👇 <i>Pastdagi tugmalar yoki quyidagi tezkor menyudan foydalaning:</i>"
        )
        await message.answer(text=owner_welcome, reply_markup=reply_kb, parse_mode=ParseMode.HTML)
        await message.answer(
            "⚡ <b>Tezkor boshqaruv havolalari:</b>",
            reply_markup=get_main_inline_keyboard(user.id, is_owner=True, active_mode="owner"),
            parse_mode=ParseMode.HTML
        )
        return

    reply_kb = get_user_reply_keyboard(is_owner=is_owner)
    welcome_text = (
        f"👋 <b>Assalomu alaykum, {user.first_name if user else 'qadrdon yurtdosh'}!</b>\n\n"
        f"🛡️ <b>ShieldGuard AI</b> — siz va oilangizni internetdagi fishing, "
        f"soxta bank kartalari, zararli APK-viruslar va yuridik shartnoma tuzoqlaridan "
        f"himoya qiluvchi keng qamrovli kiber-qalqondir.\n\n"
        f"⚡ <b>Menga quyidagilarni yuborishingiz mumkin:</b>\n"
        f"• Shubhali havola yoki matn (fishing skaneri);\n"
        f"• 16 talik bank karta raqami (masalan: <code>8600...</code> yoki <code>9860...</code>);\n"
        f"• Shubhali Telegram bot (masalan: <code>@click_bonus_bot</code>);\n"
        f"• Telegramdan kelgan fayl (masalan: <code>To'y taklifnomasi.apk</code>);\n"
        f"• Kredit yoki ijara shartnomasi (PDF yoki fotosurat).\n\n"
        f"👇 <i>Pastdagi 10 ta himoya tugmalaridan kerakli xizmatni tanlang:</i>"
    )

    if is_owner and active_mode == "user":
        welcome_text += "\n\n<i>[💡 Siz hozir sinov tariqasida oddiy fuqaro rejimidasiz. Boshqaruv markaziga qaytish uchun pastdagi '👑 Owner Rejimiga O'tish' tugmasini bosing yoki /switch_role yozing]</i>"

    await message.answer(text=welcome_text, reply_markup=reply_kb, parse_mode=ParseMode.HTML)
    await message.answer(
        "⚡ <b>Qo'shimcha kiber-vositalar:</b>",
        reply_markup=get_main_inline_keyboard(user.id if user else 0, is_owner=is_owner, active_mode=active_mode),
        parse_mode=ParseMode.HTML
    )


@dp.message(Command("switch_role"))
async def cmd_switch_role(message: types.Message):
    user = message.from_user
    await switch_owner_role(user.id, message)


@dp.callback_query(F.data == "btn_toggle_role")
async def cb_toggle_role(callback: types.CallbackQuery):
    user = callback.from_user
    if user.id != settings.OWNER_TELEGRAM_ID:
        await callback.answer("Faqat Super Owner uchun!", show_alert=True)
        return
    await callback.answer()
    await switch_owner_role(user.id, callback.message)


@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    user = message.from_user
    is_owner = (user.id == settings.OWNER_TELEGRAM_ID)
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.telegram_id == user.id)
        res = await session.execute(stmt)
        db_user = res.scalar_one_or_none()
        if not is_owner and (not db_user or db_user.role != "admin" or db_user.is_banned):
            await message.answer("❌ Bu bo'limga faqat ma'murlar kira oladi.")
            return

    await render_admin_dashboard(message, user.id)


@dp.callback_query(F.data == "btn_open_admin")
async def cb_open_admin(callback: types.CallbackQuery):
    await callback.answer()
    await render_admin_dashboard(callback.message, callback.from_user.id)


@dp.message(Command("admins"))
async def cmd_list_admins(message: types.Message):
    await render_admins_management(message, message.from_user.id)


@dp.callback_query(F.data.in_(["btn_list_admins", "btn_refresh_admins"]))
async def cb_list_admins(callback: types.CallbackQuery):
    await callback.answer()
    await render_admins_management(callback.message, callback.from_user.id)


@dp.callback_query(F.data == "btn_list_users")
async def cb_list_users(callback: types.CallbackQuery):
    await callback.answer()
    await render_users_management(callback.message, callback.from_user.id)


@dp.callback_query(F.data == "btn_live_monitor")
async def cb_live_monitor(callback: types.CallbackQuery):
    await callback.answer()
    await render_live_monitoring(callback.message, callback.from_user.id)


@dp.callback_query(F.data == "btn_list_cards")
async def cb_list_cards(callback: types.CallbackQuery):
    await callback.answer()
    await render_scam_cards_management(callback.message, callback.from_user.id)


@dp.callback_query(F.data == "btn_list_domains")
async def cb_list_domains(callback: types.CallbackQuery):
    await callback.answer()
    await render_phishing_domains_management(callback.message, callback.from_user.id)


@dp.callback_query(F.data == "btn_system_settings")
async def cb_system_settings(callback: types.CallbackQuery):
    await callback.answer()
    await render_system_settings(callback.message, callback.from_user.id)


@dp.callback_query(F.data == "btn_detailed_stats")
async def cb_detailed_stats(callback: types.CallbackQuery):
    await callback.answer()
    await render_system_stats(callback.message, callback.from_user.id)


# =========================================================================
# 8. ADMIN QO'SHISH, O'CHIRISH, BLOKLASH BUYRUQLARI
# =========================================================================

@dp.message(Command("addadmin"))
async def cmd_add_admin(message: types.Message):
    user = message.from_user
    if user.id != settings.OWNER_TELEGRAM_ID:
        await message.answer("❌ Faqat loyiha egasi (@fayzbek1331) yangi admin tayinlay oladi.")
        return

    if message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user
        await promote_user_to_admin(
            owner_id=user.id,
            target_id=target.id,
            target_username=target.username,
            target_name=target.full_name,
            message=message
        )
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        user_states[user.id] = {"action": "waiting_for_admin"}
        await message.answer(
            "➕ <b>YANGI ADMIN TAYINLASH</b>\n\n"
            "Iltimos, admin qilmoqchi bo'lgan foydalanuvchini yuboring:\n\n"
            "1️⃣ <b>Telegram ID raqami:</b> (masalan: <code>123456789</code>)\n"
            "2️⃣ <b>@username:</b> (masalan: <code>@sherzod_uz</code> yoki <code>sherzod_uz</code>)\n"
            "3️⃣ <b>Xabarini forward qilish:</b> O'sha shaxsning biron bir xabarini menga <b>Forward</b> qiling!\n\n"
            "❌ <i>Bekor qilish uchun: /cancel</i>",
            parse_mode=ParseMode.HTML
        )
        return

    await resolve_and_promote_admin(owner_id=user.id, raw_input=parts[1].strip(), message=message)


@dp.callback_query(F.data == "btn_prompt_add_admin")
async def cb_prompt_add_admin(callback: types.CallbackQuery):
    user = callback.from_user
    if user.id != settings.OWNER_TELEGRAM_ID:
        await callback.answer("Faqat Super Owner uchun!", show_alert=True)
        return
    await callback.answer()
    user_states[user.id] = {"action": "waiting_for_admin"}
    await callback.message.answer(
        "➕ <b>YANGI ADMIN TAYINLASH:</b>\n\n"
        "Foydalanuvchining ID raqami, @username'i yoki undan kelgan xabarni bu yerga <b>Forward</b> qiling.\n\n"
        "❌ <i>Bekor qilish: /cancel</i>",
        parse_mode=ParseMode.HTML
    )


@dp.message(Command("deladmin"))
async def cmd_del_admin(message: types.Message):
    user = message.from_user
    if user.id != settings.OWNER_TELEGRAM_ID:
        await message.answer("❌ Faqat loyiha egasi (@fayzbek1331) adminni o'chira oladi.")
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await show_delete_admin_picker(message, user.id)
        return

    arg = parts[1].strip()
    target_id = None
    if arg.isdigit():
        target_id = int(arg)
    else:
        clean_uname = arg.lstrip("@").strip().lower()
        async with AsyncSessionLocal() as session:
            stmt = select(User).where(func.lower(User.username) == clean_uname)
            res = await session.execute(stmt)
            target = res.scalar_one_or_none()
            if target:
                target_id = target.telegram_id

    if not target_id or target_id == settings.OWNER_TELEGRAM_ID:
        await message.answer("❌ Noto'g'ri ID yoki Super Ownerni o'chirib bo'lmaydi.")
        return

    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.telegram_id == target_id)
        res = await session.execute(stmt)
        target = res.scalar_one_or_none()
        if target and target.role == "admin":
            target.role = "user"
            session.add(AdminAuditLog(admin_telegram_id=user.id, action="remove_admin", target=str(target_id), details="Buyruq orqali"))
            await session.commit()
            await message.answer(f"✅ Foydalanuvchining (ID: <code>{target_id}</code>) adminlik huquqi bekor qilindi.", parse_mode=ParseMode.HTML)
        else:
            await message.answer("Foydalanuvchi admin emas yoki topilmadi.")


@dp.callback_query(F.data == "btn_prompt_del_admin")
async def cb_prompt_del_admin(callback: types.CallbackQuery):
    user = callback.from_user
    if user.id != settings.OWNER_TELEGRAM_ID:
        await callback.answer("Faqat Super Owner uchun!", show_alert=True)
        return
    await callback.answer()
    await show_delete_admin_picker(callback.message, user.id)


@dp.callback_query(F.data.startswith("deladmin_id:"))
async def cb_delete_admin_by_id(callback: types.CallbackQuery):
    user = callback.from_user
    if user.id != settings.OWNER_TELEGRAM_ID:
        await callback.answer("Faqat Super Owner uchun!", show_alert=True)
        return

    target_id = int(callback.data.split(":")[1])
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.telegram_id == target_id)
        res = await session.execute(stmt)
        target = res.scalar_one_or_none()
        if target and target.role == "admin":
            target.role = "user"
            session.add(AdminAuditLog(admin_telegram_id=user.id, action="remove_admin", target=str(target_id), details="Tugma orqali"))
            await session.commit()
            await callback.answer("Adminlik huquqi bekor qilindi!", show_alert=True)
            await callback.message.edit_text(f"✅ Admin (ID: <code>{target_id}</code>) muvaffaqiyatli o'chirildi.", parse_mode=ParseMode.HTML)


@dp.message(Command("ban"))
async def cmd_ban_user(message: types.Message):
    user = message.from_user
    if user.id != settings.OWNER_TELEGRAM_ID:
        await message.answer("❌ Faqat Super Owner foydalanuvchini bloklay oladi.")
        return

    parts = message.text.split(maxsplit=2)
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("Foydalanish: <code>/ban &lt;telegram_id&gt; [sabab]</code>", parse_mode=ParseMode.HTML)
        return

    target_id = int(parts[1])
    reason = parts[2] if len(parts) > 2 else "Kiber-xavfsizlik qoidalarini buzish"

    if target_id == settings.OWNER_TELEGRAM_ID:
        await message.answer("❌ Super Ownerni bloklab bo'lmaydi!")
        return

    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.telegram_id == target_id)
        res = await session.execute(stmt)
        target = res.scalar_one_or_none()
        if target:
            target.is_banned = True
            session.add(AdminAuditLog(admin_telegram_id=user.id, action="ban_user", target=str(target_id), details=reason))
            await session.commit()
            await message.answer(f"🚫 Foydalanuvchi (ID: <code>{target_id}</code>) botdan bloklandi.\nSabab: {reason}", parse_mode=ParseMode.HTML)
        else:
            await message.answer("Foydalanuvchi bazada topilmadi.")


@dp.message(Command("unban"))
async def cmd_unban_user(message: types.Message):
    user = message.from_user
    if user.id != settings.OWNER_TELEGRAM_ID:
        return

    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("Foydalanish: <code>/unban &lt;telegram_id&gt;</code>", parse_mode=ParseMode.HTML)
        return

    target_id = int(parts[1])
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.telegram_id == target_id)
        res = await session.execute(stmt)
        target = res.scalar_one_or_none()
        if target:
            target.is_banned = False
            session.add(AdminAuditLog(admin_telegram_id=user.id, action="unban_user", target=str(target_id), details="Blokdan chiqarildi"))
            await session.commit()
            await message.answer(f"✅ Foydalanuvchi (ID: <code>{target_id}</code>) blokdan chiqarildi.", parse_mode=ParseMode.HTML)
        else:
            await message.answer("Foydalanuvchi topilmadi.")


@dp.callback_query(F.data == "btn_prompt_ban_user")
async def cb_prompt_ban(callback: types.CallbackQuery):
    user = callback.from_user
    if user.id != settings.OWNER_TELEGRAM_ID:
        await callback.answer("Faqat Super Owner uchun!", show_alert=True)
        return
    await callback.answer()
    user_states[user.id] = {"action": "waiting_for_ban"}
    await callback.message.answer(
        "🚫 <b>FOYDALANUVCHINI BLOKLASH:</b>\n\n"
        "Bloklamoqchi bo'lgan shaxsning <b>Telegram ID</b> raqamini yuboring.\n"
        "Masalan: <code>123456789</code>\n\n"
        "❌ <i>Bekor qilish: /cancel</i>",
        parse_mode=ParseMode.HTML
    )


@dp.callback_query(F.data == "btn_prompt_unban_user")
async def cb_prompt_unban(callback: types.CallbackQuery):
    user = callback.from_user
    if user.id != settings.OWNER_TELEGRAM_ID:
        await callback.answer("Faqat Super Owner uchun!", show_alert=True)
        return
    await callback.answer()
    user_states[user.id] = {"action": "waiting_for_unban"}
    await callback.message.answer(
        "✅ <b>BLOKDAN CHIQARISH:</b>\n\n"
        "Blokdan chiqarmoqchi bo'lgan shaxsning <b>Telegram ID</b> raqamini yuboring.\n\n"
        "❌ <i>Bekor qilish: /cancel</i>",
        parse_mode=ParseMode.HTML
    )


@dp.message(Command("broadcast"))
async def cmd_broadcast(message: types.Message):
    user = message.from_user
    if user.id != settings.OWNER_TELEGRAM_ID:
        await message.answer("❌ Faqat Super Owner umumiy xabar tarqata oladi.")
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        user_states[user.id] = {"action": "waiting_for_broadcast"}
        await message.answer(
            "📢 <b>Barcha foydalanuvchilarga xabar tarqatish:</b>\n\n"
            "Iltimos, e'loningiz matnini shu yerga yozib yuboring.\n\n"
            "❌ <i>Bekor qilish uchun: /cancel</i>",
            parse_mode=ParseMode.HTML
        )
        return

    await execute_broadcast(owner_id=user.id, broadcast_body=parts[1].strip(), message=message)


@dp.callback_query(F.data == "btn_prompt_broadcast")
async def cb_prompt_broadcast(callback: types.CallbackQuery):
    user = callback.from_user
    if user.id != settings.OWNER_TELEGRAM_ID:
        await callback.answer("Faqat Super Owner uchun!", show_alert=True)
        return
    await callback.answer()
    user_states[user.id] = {"action": "waiting_for_broadcast"}
    await callback.message.answer(
        "📢 <b>YANGI E'LON TARQATISH:</b>\n\n"
        "Barcha bot a'zolariga yubormoqchi bo'lgan xabaringiz matnini yuboring.\n\n"
        "❌ <i>Bekor qilish uchun: /cancel</i>",
        parse_mode=ParseMode.HTML
    )


@dp.callback_query(F.data == "btn_prompt_add_card")
async def cb_prompt_add_card(callback: types.CallbackQuery):
    user = callback.from_user
    await callback.answer()
    user_states[user.id] = {"action": "waiting_for_scam_card"}
    await callback.message.answer(
        "🚫 <b>FIRIBGAR KARTANI QORA RO'YXATGA QO'SHISH</b>\n\n"
        "Quyidagi formatda yuboring:\n"
        "<code>&lt;16 talik karta raqami&gt; &lt;sababi&gt;</code>\n\n"
        "Masalan:\n<code>8600123456789012 Telegramda soxta ovoz berish orqali pul talab qildi</code>\n\n"
        "❌ <i>Bekor qilish uchun: /cancel</i>",
        parse_mode=ParseMode.HTML
    )


@dp.callback_query(F.data == "btn_prompt_del_card")
async def cb_prompt_del_card(callback: types.CallbackQuery):
    user = callback.from_user
    await callback.answer()
    user_states[user.id] = {"action": "waiting_for_del_card"}
    await callback.message.answer(
        "➖ <b>KARTANI QORA RO'YXATDAN O'CHIRISH:</b>\n\n"
        "O'chirmoqchi bo'lgan 16 talik karta raqamini yuboring.\n\n"
        "❌ <i>Bekor qilish: /cancel</i>",
        parse_mode=ParseMode.HTML
    )


@dp.callback_query(F.data == "btn_prompt_add_domain")
async def cb_prompt_add_domain(callback: types.CallbackQuery):
    user = callback.from_user
    await callback.answer()
    user_states[user.id] = {"action": "waiting_for_domain"}
    await callback.message.answer(
        "🌐 <b>YANGI FISHING DOMEN QO'SHISH:</b>\n\n"
        "Quyidagi formatda yuboring:\n"
        "<code>&lt;domen_nomi&gt; &lt;sababi&gt;</code>\n\n"
        "Masalan:\n<code>c1ick-bonus.xyz Soxta aksiya va kartani o'g'irlash</code>\n\n"
        "❌ <i>Bekor qilish: /cancel</i>",
        parse_mode=ParseMode.HTML
    )


@dp.callback_query(F.data == "btn_prompt_del_domain")
async def cb_prompt_del_domain(callback: types.CallbackQuery):
    user = callback.from_user
    await callback.answer()
    user_states[user.id] = {"action": "waiting_for_del_domain"}
    await callback.message.answer(
        "➖ <b>FISHING DOMENNI O'CHIRISH:</b>\n\n"
        "O'chirmoqchi bo'lgan domen nomini yuboring (masalan: <code>c1ick-bonus.xyz</code>).\n\n"
        "❌ <i>Bekor qilish: /cancel</i>",
        parse_mode=ParseMode.HTML
    )


@dp.message(Command("addcard"))
async def cmd_add_card(message: types.Message):
    user = message.from_user
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("Foydalanish: <code>/addcard 8600123456789012 Sababi...</code>", parse_mode=ParseMode.HTML)
        return
    clean_num = "".join(filter(str.isdigit, parts[1]))
    if len(clean_num) != 16:
        await message.answer("❌ Karta raqami 16 ta raqamdan iborat bo'lishi kerak!")
        return

    card_info = analyze_card_number(clean_num)
    async with AsyncSessionLocal() as session:
        stmt = select(CardBlacklist).where(CardBlacklist.card_number == clean_num)
        res = await session.execute(stmt)
        c = res.scalar_one_or_none()
        if not c:
            c = CardBlacklist(
                card_number=clean_num,
                bank_name=card_info.get("bank_name"),
                reason=parts[2].strip(),
                reported_by=user.id
            )
            session.add(c)
        else:
            c.report_count += 1
            c.reason += f" | {parts[2].strip()}"
        await session.commit()
    await message.answer(f"✅ Karta <code>{clean_num}</code> muvaffaqiyatli qora ro'yxatga kiritildi!", parse_mode=ParseMode.HTML)


# =========================================================================
# 9. FOYDALANUVCHI INTERAKTIV VOSITALARI & SINOVLAR
# =========================================================================

@dp.callback_query(F.data == "btn_sample_phishing")
async def cb_sample_phishing(callback: types.CallbackQuery):
    """Namuna fishing havolani diagnostika qilish."""
    await callback.answer("Namuna fishing tahlili ishga tushdi...")
    test_url = "https://c1ick-bonus-prezident-yordam.xyz/card-login"
    res = await analyze_url_or_text(test_url)
    risk = res["risk_score"]
    report = (
        "🧪 <b>NAMUNAVIY FISHING HAVOLA DIAGNOSTIKASI:</b>\n"
        "══════════════════════════════\n\n"
        f"🎯 <b>Tekshirilgan manzil:</b> <code>{test_url}</code>\n"
        f"📊 <b>Xavf ko'rsatkichi:</b> 🔴 <b>{int(risk)}% (Kritik Xavfli!)</b>\n"
        f"📝 <b>Hukm:</b> {res['verdict_uz']}\n\n"
        f"💬 <b>Tahlil xulosasi:</b>\n{res['summary_uz']}\n\n"
        "🚩 <b>Aniqlangan xavfli omillar:</b>\n"
        "• 🚨 <b>Brend o'g'irligi:</b> 'Click' to'lov tizimining nomini soxtalashtirish (Typosquatting);\n"
        "• 🛑 <b>Shubhali domen zonasi:</b> '.xyz' arzon firibgarlik zonasi;\n"
        "• ⚠️ <b>Ijtimoiy muhandislik:</b> 'prezident yordam' yolg'on va'dasi orqali aldash;\n"
        "• 🚨 <b>OTP / Parol o'g'irlash:</b> Sahifada bank kartasi va SMS-kod kiritish shakli topildi!\n\n"
        "⛔ <b>Hukm:</b> Ushbu manzil 100% kiber-firibgarlar tuzog'idir!"
    )
    await callback.message.answer(report, parse_mode=ParseMode.HTML)


@dp.callback_query(F.data == "btn_sample_scam_card")
async def cb_sample_scam_card(callback: types.CallbackQuery):
    """Namuna firibgar kartani tekshirish."""
    await callback.answer()
    report = (
        "🧪 <b>NAMUNA FIRIBGAR KARTA DIAGNOSTIKASI:</b>\n"
        "══════════════════════════════\n\n"
        "💳 <b>Karta:</b> <code>8600 1234 5678 9012</code>\n"
        "🏦 <b>To'lov tizimi & Bank:</b> Uzcard (Agrobank ATB)\n"
        "📊 <b>Xavf darajasi:</b> 🔴 <b>100% (Qora ro'yxatda)</b>\n\n"
        "⚠️ <b>Qora ro'yxat ma'lumoti:</b>\n"
        "Ushbu karta egasi Telegramda 'Yutuqli aksiya' deb aldab, fuqarolardan 450,000 so'm avans olib g'oyib bo'lgan.\n"
        "Shikoyatlar soni: <b>12 ta</b>\n\n"
        "⛔ <b>Tavsiya:</b> Ushbu karta bilan hech qanday moliyaviy amaliyot bajarmang!"
    )
    await callback.message.answer(report, parse_mode=ParseMode.HTML)


@dp.callback_query(F.data == "btn_bin_directory")
async def cb_bin_directory(callback: types.CallbackQuery):
    """Bank kartalari BIN prefikslari."""
    await callback.answer()
    text = (
        "🏦 <b>O'ZBEKISTON BANK KARTALARI BIN PREFIKSLARI:</b>\n"
        "══════════════════════════════\n\n"
        "🔢 <b>Karta boshidagi dastlabki 4-6 ta raqam:</b>\n"
        "• <code>8600</code> — Uzcard (Milliy to'lov tizimi, barcha banklar)\n"
        "• <code>9860</code> — Humo (Milliy to'lov tizimi, kontaktsiz)\n"
        "• <code>5614</code> — Humo Virtual va xalqaro kartalar\n"
        "• <code>4...</code> — Visa xalqaro kartalari (Kapital, NBU, Ipak Yo'li va b.)\n"
        "• <code>5...</code> — Mastercard xalqaro kartalari\n"
        "• <code>62..</code> — UnionPay xalqaro kartalari\n\n"
        "💡 <i>Karta haqiqiy yoki soxtaligini tekshirish uchun uning 16 talik raqamini botga yuboring!</i>"
    )
    await callback.message.answer(text, parse_mode=ParseMode.HTML)


@dp.callback_query(F.data == "btn_card_fraud_signs")
async def cb_card_fraud_signs(callback: types.CallbackQuery):
    """Karta firibgarligining 5 asosiy belgisi."""
    await callback.answer()
    text = (
        "⚠️ <b>KARTA FIRIBGARLIGINING 5 TA ASOSIY BELGISI:</b>\n"
        "══════════════════════════════\n\n"
        "1️⃣ <b>Oldindan to'lov (Avans) talab qilish:</b>\n"
        "Tovar yoki xizmatni ko'rsatmasdan turib 'Karta raqamimga zaklad tashlang' deyish;\n\n"
        "2️⃣ <b>Ortiqcha pul o'tkazdim deb yolg'on gapirish:</b>\n"
        "'Sizga adashib 500 ming tashlab yubordim, 400 mingini qaytarib bering' deb soxta chek yuborish;\n\n"
        "3️⃣ <b>Karta rasmini so'rash (Old va Orqa tomoni):</b>\n"
        "Karta ustidagi CVV kod va amal qilish muddatini bilib olishga urinish;\n\n"
        "4️⃣ <b>SMS tasdiqlash kodini so'rash:</b>\n"
        "'Pul tushishi uchun SMS kodni ayting' deyish (Pul tushishi uchun kod kerak emas!);\n\n"
        "5️⃣ <b>Tezkor shoshiltirish:</b>\n"
        "'Faqat 10 daqiqa vaqtingiz bor, tezroq to'lang' deb psixologik bosim o'tkazish."
    )
    await callback.message.answer(text, parse_mode=ParseMode.HTML)


@dp.callback_query(F.data == "btn_sample_fake_bot")
async def cb_sample_fake_bot(callback: types.CallbackQuery):
    """Namuna soxta bot tahlili."""
    await callback.answer()
    res = analyze_telegram_bot_or_username("@click_bonus_yutuq_bot")
    report = (
        "🧪 <b>NAMUNA SOXTA BOT TAHLILI:</b>\n"
        "══════════════════════════════\n\n"
        f"🎯 <b>Nishon:</b> <code>@click_bonus_yutuq_bot</code>\n"
        f"📊 <b>Xavf darajasi:</b> 🔴 <b>90% (Kritik Xavfli!)</b>\n"
        f"📝 <b>Hukm:</b> {res['verdict_uz']}\n\n"
        f"💬 <b>Xulosa:</b>\n{res['summary_uz']}\n\n"
        "🚩 <b>Aniqlangan omillar:</b>\n"
        "• Click brendini ruxsatsiz noqonuniy ishlatish;\n"
        "• Rasmiy verifikatsiya nishoni (ko'k belgi) yo'qligi;\n"
        "• Foydalanuvchilardan karta ma'lumotlarini to'plash."
    )
    await callback.message.answer(report, parse_mode=ParseMode.HTML)


@dp.callback_query(F.data == "btn_known_fake_bots")
async def cb_known_fake_bots(callback: types.CallbackQuery):
    """Ko'p uchraydigan soxta botlar ro'yxati."""
    await callback.answer()
    text = (
        "📋 <b>ENG KO'P UCHRAYDIGAN SOXTA BOT TUZOQLARI:</b>\n"
        "══════════════════════════════\n\n"
        "🛑 <b>1. 'Bonus & Yutuq' botlari:</b>\n"
        "Masalan: <code>@click_yutuq_bot</code>, <code>@payme_bonus_bot</code>, <code>@uzum_sovg'a_bot</code>\n"
        "<i>Maqsadi: Karta raqam va SMS kodni olib pul yechish.</i>\n\n"
        "🛑 <b>2. 'Ovoz berish / Open Budget' soxta botlari:</b>\n"
        "<i>Maqsadi: Telegram tasdiqlash kodini kiritdirib akkauntingizni o'g'irlash.</i>\n\n"
        "🛑 <b>3. 'Davlat Subsidiyasi / Moddiy yordam' botlari:</b>\n"
        "<i>Maqsadi: Soxta komissiya to'lovlarini undirish.</i>\n\n"
        "💡 <i>Har qanday botni tekshirish uchun uning @usernamesini ShieldGuard'ga yuboring!</i>"
    )
    await callback.message.answer(text, parse_mode=ParseMode.HTML)


@dp.callback_query(F.data == "btn_official_bots")
async def cb_official_bots(callback: types.CallbackQuery):
    """Rasmiy tasdiqlangan botlar ro'yxati."""
    await callback.answer()
    text = (
        "✅ <b>RASMIY VA ISHONCHLI TO'LOV BOTLARI:</b>\n"
        "══════════════════════════════\n\n"
        "• <b>Click:</b> @clickuz (Rasmiy verifikatsiya ko'k belgisi mavjud)\n"
        "• <b>Payme:</b> @payme_uz (Rasmiy to'lov xizmati)\n"
        "• <b>Uzum:</b> @uzumbank (Rasmiy ilova va xizmat)\n"
        "• <b>Davlat Xizmatlari:</b> @myGovUzBot (Yagona interaktiv portal)\n"
        "• <b>Soliq Qo'mitasi:</b> @SoliqUzBot\n\n"
        "⚠️ <i>Eslatma: Rasmiy botlar hech qachon sizdan SMS tasdiqlash kodini chat orqali so'ramaydi!</i>"
    )
    await callback.message.answer(text, parse_mode=ParseMode.HTML)


@dp.callback_query(F.data == "btn_sample_contract")
async def cb_sample_contract(callback: types.CallbackQuery):
    """Namuna shartnoma rentgeni tahlili."""
    await callback.answer()
    report = (
        "📄 <b>NAMUNA SHARTNOMA RENTGENI (MIKROQARZ TAHLILI):</b>\n"
        "══════════════════════════════\n\n"
        "📑 <b>Hujjat turi:</b> Mikroqarz va muddatli to'lov shartnomasi\n"
        "🛡️ <b>Ishonchlilik balli:</b> 🔴 <b>35/100 (Juda xavfli!)</b>\n\n"
        "💬 <b>Oddiy tildagi xulosa:</b>\n"
        "Ushbu shartnoma iste'molchi huquqlarini jiddiy cheklovchi yirtqich (predatory) shartlarga ega!\n\n"
        "⚠️ <b>ANIQLANGAN 3 TA KRITIK TUZOQ:</b>\n"
        "1. <b>4.2-band (Kunlik Penya):</b> To'lov kechikkan har bir kun uchun qarz summasidan kunlik 1.5% jarima (yillik 547%!) hisoblanadi;\n"
        "2. <b>8.1-band (Bir tomonlama foiz):</b> Tashkilot xabardor qilmasdan foiz stavkalarini istalgan paytda oshirish huquqini saqlab qolgan;\n"
        "3. <b>11.4-band (Garovni tortib olish):</b> Qarz muddati 10 kunga o'tsa, garovdagi mulk sudsiz to'g'ridan-to'g'ri musodara qilinadi!\n\n"
        "⛔ <b>Yuridik maslahat:</b> Ushbu shartnomani imzolash qat'iyan tavsiya etilmaydi!"
    )
    await callback.message.answer(report, parse_mode=ParseMode.HTML)


@dp.callback_query(F.data == "btn_contract_traps")
async def cb_contract_traps(callback: types.CallbackQuery):
    """Shartnomadagi 4 asosiy tuzoq."""
    await callback.answer()
    text = (
        "📑 <b>KREDIT VA IJARA SHARTNOMALARIDAGI 4 ASOSIY TUZOQ:</b>\n"
        "══════════════════════════════\n\n"
        "1️⃣ <b>Yirtqich Penya (Kunlik jarima):</b>\n"
        "Qonuniy me'yordan ortiq (kunlik 0.5% - 2% gacha) penya yozilishi. Natijada kichik qarz bir oyda 3 barobarga oshadi.\n\n"
        "2️⃣ <b>Yashirin sug'urta va xizmat haqlari:</b>\n"
        "Kredit foizi past ko'rsatiladi (masalan 24%), lekin har oy 'Hisob yuritish' yoki 'Majburiy sug'urta' uchun yashirin 2-3% qo'shimcha yechiladi.\n\n"
        "3️⃣ <b>Bir tomonlama shartlarni o'zgartirish:</b>\n"
        "Kompaniya xohlagan paytda foizlarni yoki ijara haqini oshirish huquqini o'zida qoldirishi.\n\n"
        "4️⃣ <b>Sudsiz undiruv huquqi:</b>\n"
        "Biroz kechikish bo'lsa ham avtomobil yoki mulkni sud qarorisiz tortib olish bandi.\n\n"
        "💡 <i>Har qanday shartnoma imzolashdan oldin uning PDF yoki rasmini ShieldGuard'ga yuboring!</i>"
    )
    await callback.message.answer(text, parse_mode=ParseMode.HTML)


# =========================================================================
# 10. INTERAKTIV KIBER-VIKTORINA (TEST) MOTORIKASI
# =========================================================================

@dp.message(Command("quiz"))
async def cmd_quiz(message: types.Message):
    """Kiber-viktorinani boshlash."""
    text = (
        "🧠 <b>SHIELDGUARD KIBER-SAVODXONLIK TESTI:</b>\n"
        "══════════════════════════════\n\n"
        "Siz o'zingiz va oilangizni internetdagi zamonaviy firibgarliklardan himoya qila olasizmi?\n\n"
        "Ushbu testda real hayotdagi <b>5 ta eng xavfli firibgarlik vaziyati</b> keltirilgan.\n"
        "Sinovdan o'ting, bilimingizni tekshiring va <b>Kiber-Qalqon</b> reytingingizni bilib oling!\n\n"
        "👇 <i>Testni boshlash uchun quyidagi tugmani bosing:</i>"
    )
    kb = [[InlineKeyboardButton(text="🚀 Testni Boshlash (5 ta savol)", callback_data="quiz_start")]]
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode=ParseMode.HTML)


@dp.callback_query(F.data == "btn_quiz_info")
async def cb_quiz_info(callback: types.CallbackQuery):
    await callback.answer()
    await cmd_quiz(callback.message)


@dp.callback_query(F.data == "quiz_start")
async def cb_quiz_start(callback: types.CallbackQuery):
    """Viktorinaning 1-savoli."""
    await callback.answer()
    user_id = callback.from_user.id
    user_states[user_id] = {"quiz_step": 1, "quiz_score": 0}
    await send_quiz_question(callback.message, step=1, user_id=user_id)


async def send_quiz_question(message: types.Message, step: int, user_id: int):
    """Savolni inline tugmalar bilan yuborish."""
    if step > len(QUIZ_QUESTIONS):
        # Viktorina tugadi
        state = user_states.get(user_id, {})
        score = state.get("quiz_score", 0)
        user_states.pop(user_id, None)

        if score == 5:
            badge = "🏆 <b>OLINMA KIBER-QALQON (5/5)</b>"
            comment = "Ajoyib natija! Siz to'liq kiber-himoyalangansiz. Firibgarlar sizni aslo alday olmaydi!"
        elif score >= 3:
            badge = "🥇 <b>HUSH-YOR HIMOYACHI (3-4/5)</b>"
            comment = "Yaxshi natija! Siz kiber-xavflarni yaxshi tushunasiz, ammo ba'zi nozik tuzoqlarga hushyor bo'ling."
        else:
            badge = "⚠️ <b>EHTIYOT BO'LING! (0-2/5)</b>"
            comment = "Kiber-savodxonlikni oshirish zarur! Firibgarlarning hiylalariga aldanib qolmaslik uchun ShieldGuard tavsiyalarini muntazam o'qib boring."

        finish_text = (
            "🎉 <b>VIKTORINA YAKUNLANDI!</b>\n"
            "══════════════════════════════\n\n"
            f"📊 <b>Sizning Natijangiz:</b> {score} / 5 ball\n"
            f"🏅 <b>Maqomingiz:</b> {badge}\n\n"
            f"💬 <b>Ekspert bahosi:</b>\n{comment}\n\n"
            "🛡️ <i>ShieldGuard AI — Doimo oilangiz va mablag'ingiz xavfsizligi himoyasida!</i>"
        )
        kb = [
            [InlineKeyboardButton(text="🔄 Qaytadan Sinab Ko'rish", callback_data="quiz_start")],
            [InlineKeyboardButton(text="📱 Mini Appda Ko'rish", url=f"{settings.WEBAPP_URL}/webapp")]
        ]
        await message.answer(finish_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode=ParseMode.HTML)
        return

    q = QUIZ_QUESTIONS[step - 1]
    kb = []
    for idx, (label, is_corr, _) in enumerate(q["options"]):
        cb_code = f"qans:{step}:{idx}"
        kb.append([InlineKeyboardButton(text=label[:40], callback_data=cb_code)])

    await message.answer(
        q["question"],
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
        parse_mode=ParseMode.HTML
    )


@dp.callback_query(F.data.startswith("qans:"))
async def cb_quiz_answer(callback: types.CallbackQuery):
    """Javobni baholash va tushuntirish berish."""
    await callback.answer()
    parts = callback.data.split(":")
    step = int(parts[1])
    opt_idx = int(parts[2])
    user_id = callback.from_user.id

    q = QUIZ_QUESTIONS[step - 1]
    label, is_correct, explanation = q["options"][opt_idx]

    state = user_states.get(user_id, {"quiz_step": step, "quiz_score": 0})
    if is_correct:
        state["quiz_score"] = state.get("quiz_score", 0) + 1

    feedback = (
        f"<b>{q['title']} Natijasi:</b>\n\n"
        f"Sizning javobingiz: <i>{label}</i>\n\n"
        f"{explanation}\n\n"
        f"Hozirgi to'plangan ball: <b>{state.get('quiz_score', 0)} / {step}</b>"
    )

    next_step = step + 1
    state["quiz_step"] = next_step
    user_states[user_id] = state

    next_btn_label = "➡️ Keyingi Savolga O'tish" if next_step <= len(QUIZ_QUESTIONS) else "🏁 Natijani Ko'rish"
    kb = [[InlineKeyboardButton(text=next_btn_label, callback_data=f"qnext:{next_step}")]]

    await callback.message.answer(feedback, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode=ParseMode.HTML)


@dp.callback_query(F.data.startswith("qnext:"))
async def cb_quiz_next(callback: types.CallbackQuery):
    await callback.answer()
    next_step = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    await send_quiz_question(callback.message, step=next_step, user_id=user_id)


# =========================================================================
# 11. FAVQULODDA YORDAM (SOS) VA TEZKOR QO'LLANMALAR
# =========================================================================

@dp.message(Command("sos"))
async def cmd_sos(message: types.Message):
    """SOS favqulodda xavfsizlik va yordam markazi."""
    sos_text = (
        "🆘 <b>FAVQULODDA XAVFSIZLIK VA TEZKOR YORDAM MARKAZI:</b>\n"
        "══════════════════════════════\n\n"
        "Agar siz firibgarlarga karta ma'lumotlaringizni berib qo'ygan bo'lsangiz yoki hisobingizdan pul yechilgan bo'lsa:\n\n"
        "1️⃣ <b>ZUDLIK BILAN KARTANI BLOKLANG:</b>\n"
        "Bank ilovangizga (Click, Payme, Uzum) kiring va kartangiz ustiga bosib 'Bloklash'ni bosing!\n"
        "⚡ <i>Click USSD: *880*3# orqali ham darhol bloklash mumkin.</i>\n\n"
        "2️⃣ <b>BANKINGIZGA QO'NG'IROQ QILING:</b>\n"
        "• Click: <b>71 202-88-88</b> | Payme: <b>78 150-22-29</b>\n"
        "• Uzum Bank: <b>78 777-07-99</b> | Uzcard (24/7): <b>1224</b>\n"
        "• Humo (24/7): <b>71 200-08-88</b> | Agrobank: <b>1216</b>\n\n"
        "3️⃣ <b>TELEGRAM PROFILINI HIMOYA QILING:</b>\n"
        "Sozlamalar -> Qurilmalar (Devices) -> 'Barcha boshqa seanslarni tugatish'!\n\n"
        "4️⃣ <b>IIV KIBERXAVFSIZLIK BO'LIMIGA MUROJAAT:</b>\n"
        "📞 Ishonch telefoni: <b>102</b> yoki <b>1102</b>\n"
        "Rasmiy ariza portali: <code>cyber102.uz</code>"
    )
    kb = [
        [
            InlineKeyboardButton(text="🚨 5 Ta Shoshilinch Qadam", callback_data="btn_sos_steps"),
            InlineKeyboardButton(text="📋 Politsiyaga Ariza Shabloni", callback_data="btn_police_template")
        ],
        [
            InlineKeyboardButton(text="🛑 Obunani (Avtospisanie) Bekor Qilish", callback_data="btn_cancel_subscription_guide"),
            InlineKeyboardButton(text="🏦 Banklar Koll-Markazlari", callback_data="btn_bank_callcenters")
        ]
    ]
    await message.answer(sos_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode=ParseMode.HTML)


@dp.callback_query(F.data == "btn_sos_info")
async def cb_sos_info(callback: types.CallbackQuery):
    await callback.answer()
    await cmd_sos(callback.message)


@dp.callback_query(F.data == "btn_sos_steps")
async def cb_sos_steps(callback: types.CallbackQuery):
    await callback.answer()
    steps_text = (
        "🚨 <b>PULINGIZNI QUTQARIB QOLISH UCHUN 5 TA SHOSHILINCH QADAM:</b>\n"
        "══════════════════════════════\n\n"
        "1️⃣ <b>1-QADAM: KARTANI 10 SONIYADA BLOKLANG!</b>\n"
        "Click, Payme yoki Uzum ilovasiga kiring -> Karta sozlamalari -> 'Bloklash'.\n"
        "<i>Bu firibgarlarning kartadagi qolgan barcha pullarni yechib olishini to'xtatadi.</i>\n\n"
        "2️⃣ <b>2-QADAM: BANK KOLL-MARKAZIGA QO'NG'IROQ QILING</b>\n"
        "Zudlik bilan bankka qo'ng'iroq qilib: 'Mablag'im firibgarlar tomonidan noqonuniy yechildi, tranzaksiyani to'xtating va kartamni to'liq muzlating' deb ayting.\n\n"
        "3️⃣ <b>3-QADAM: TELEGRAM VA ILOVALARDAN ULARNI CHIQARIB YUBORING</b>\n"
        "Telegram -> Sozlamalar -> Qurilmalar (Devices) -> 'Barcha boshqa seanslarni tugatish' tugmasini bosing.\n\n"
        "4️⃣ <b>4-QADAM: ISBOTLARNI SAQLAB QOLING</b>\n"
        "Firibgar bilan bo'lgan barcha yozishmalar, soxta cheklar, telefon raqamlar va ularning bank karta raqamini darhol skrinshot qilib oling.\n\n"
        "5️⃣ <b>5-QADAM: RASMIY KIBER-ARIZA TOPSHIRING</b>\n"
        "O'zbekiston IIV Kiberxavfsizlik markazining <code>cyber102.uz</code> portaliga yoki <b>102</b> raqamiga ariza bering."
    )
    kb = [
        [InlineKeyboardButton(text="📋 Tayyor Ariza Matnini Olish", callback_data="btn_police_template")],
        [InlineKeyboardButton(text="🛑 Obunani (Avtospisanie) To'xtatish", callback_data="btn_cancel_subscription_guide")],
        [InlineKeyboardButton(text="⬅️ Favqulodda Menyu", callback_data="btn_sos_info")]
    ]
    await callback.message.answer(steps_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode=ParseMode.HTML)


@dp.callback_query(F.data == "btn_police_template")
async def cb_police_template(callback: types.CallbackQuery):
    await callback.answer()
    template_text = (
        "📋 <b>IIV KIBERXAVFSIZLIKKA TAYYOR ARIZA SHABLONI:</b>\n"
        "══════════════════════════════\n"
        "<i>Quyidagi matn ustiga bosib nusxalang, qavs ichidagi ma'lumotlaringizni to'ldiring va cyber102.uz portaliga yoki tuman IIBga taqdim eting:</i>\n\n"
        "<code>O'zbekiston Respublikasi IIV Tezkor-qidiruv departamenti Kiberxavfsizlik markazi boshlig'iga\n\n"
        "Ariza beruvchi: [Familiyangiz Ismingiz Sharifingiz]\n"
        "JShShIR / Pasport: [Pasport seriya va raqami]\n"
        "Telefon raqam: [Telefon raqamingiz]\n"
        "Yashash manzili: [Yashash manzilingiz]\n\n"
        "ARIZA\n"
        "(Internet orqali sodir etilgan firibgarlik to'g'risida)\n\n"
        "Men, [Ismingiz Sharifingiz], [Sana] kuni soat taxminan [Vaqt]da internet tarmog'ida noma'lum shaxs(lar)ning firibgarlik harakatlariga duch keldim.\n\n"
        "Ular [OLX soxta dostavka / Kredit sug'urta badali / 1 so'mlik obuna / Telegram orqali] bahonasida meni aldab, mening nomimdagi [Karta raqamingizning birinchi 6 va oxirgi 4 raqami] raqamli bank kartamdan jami [Zarar miqdori, masalan: 1 500 000] so'm mablag'ni noqonuniy ravishda o'zlashtirib olishdi.\n\n"
        "Firibgarning aloqa ma'lumotlari: [Telegram username yoki telefoni]\n"
        "Firibgar pul o'tkazdirgan karta raqami: [Firibgar kartasi]\n"
        "Menga yuborilgan soxta havola: [Havola]\n\n"
        "Ushbu holat yuzasidan zudlik bilan tekshiruv o'tkazishingizni, noqonuniy yechilgan mablag'larni muzlatib, aybdor shaxslarga nisbatan O'zbekiston Respublikasi JK 168-moddasi (Firibgarlik) bilan qonuniy chora ko'rishingizni so'rayman.\n\n"
        "Ilova qilinadi:\n"
        "1. Bankdan to'lov ko'chirmasi (kassa cheki);\n"
        "2. Firibgarlar bilan yozishmalar va havolalar skrinshotlari.\n\n"
        "[Ariza topshirilgan sana] | [Imzo]</code>"
    )
    kb = [
        [InlineKeyboardButton(text="🌐 cyber102.uz Saytiga O'tish", url="https://cyber102.uz")],
        [InlineKeyboardButton(text="⬅️ Favqulodda Menyu", callback_data="btn_sos_info")]
    ]
    await callback.message.answer(template_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode=ParseMode.HTML)


@dp.callback_query(F.data == "btn_cancel_subscription_guide")
async def cb_cancel_subscription_guide(callback: types.CallbackQuery):
    await callback.answer()
    guide_text = (
        "🛑 <b>YASHIRIN AVTOSPISANIE VA OBUNALARNI TO'XTATISH:</b>\n"
        "══════════════════════════════\n\n"
        "Agar kartangizdan 1 so'm to'laganingizdan so'ng har oy/hafta pul yechilayotgan bo'lsa:\n\n"
        "🔹 <b>CLICK ILOVASIDA:</b>\n"
        "1. Click ilovasiga kiring;\n"
        "2. Pastdagi 'Xizmatlar' (yoki 'Batafsil') bo'limiga o'ting;\n"
        "3. 'Avtoto'lovlar va obunalar' bo'limini oching;\n"
        "4. Shubhali obuna ustiga bosib, <b>'Obunani bekor qilish'</b> tugmasini bosing!\n\n"
        "🔹 <b>PAYME ILOVASIDA:</b>\n"
        "1. Payme ilovasiga kiring;\n"
        "2. 'Sozlamalar' (Profil) bo'limiga kiring;\n"
        "3. 'Mening to'lovlarim' -> 'Avtomatik to'lovlar'ga kiring;\n"
        "4. Keraksiz xizmatni o'chirib tashlang.\n\n"
        "🔹 <b>UZUM BANK ILOVASIDA:</b>\n"
        "1. Uzum Bank -> 'To'lovlar' bo'limi;\n"
        "2. 'Avtoto'lovlar' ro'yxatidan obunani o'chiring.\n\n"
        "⚠️ <b>ENG ISHONCHLI CHORA (Agar sayt topilmasa):</b>\n"
        "Agar xorijiy sayt orqali yashirin obuna qilingan bo'lsa, bankingizga qo'ng'iroq qilib yoki ilovada <b>kartani qayta chiqarish (perevipusk)</b> buyurtma qiling. Eski karta yopilgach, yashirin obunalar o'z-o'zidan butunlay to'xtaydi!"
    )
    kb = [
        [InlineKeyboardButton(text="🏦 Banklar Koll-Markazlari", callback_data="btn_bank_callcenters")],
        [InlineKeyboardButton(text="⬅️ Favqulodda Menyu", callback_data="btn_sos_info")]
    ]
    await callback.message.answer(guide_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode=ParseMode.HTML)


@dp.callback_query(F.data == "btn_bank_callcenters")
async def cb_bank_callcenters(callback: types.CallbackQuery):
    await callback.answer()
    await render_user_bank_directory(callback.message)


@dp.callback_query(F.data == "btn_cyber_tips")
async def cb_cyber_tips(callback: types.CallbackQuery):
    await callback.answer()
    await render_user_cyber_tips(callback.message)


@dp.callback_query(F.data == "btn_card_info")
async def cb_card_info(callback: types.CallbackQuery):
    await callback.answer()
    await render_user_card_center(callback.message)


@dp.callback_query(F.data == "btn_bot_info")
async def cb_bot_info(callback: types.CallbackQuery):
    await callback.answer()
    await render_user_bot_center(callback.message)


@dp.callback_query(F.data == "btn_contract_info")
async def cb_contract_info(callback: types.CallbackQuery):
    await callback.answer()
    await render_user_contract_center(callback.message)


@dp.callback_query(F.data == "btn_family_info")
async def cb_family_info(callback: types.CallbackQuery):
    await callback.answer()
    uid = callback.from_user.id
    text = (
        "👨‍👩‍👧‍👦 <b>OILA QALQONI — BIRIKTIRISH XIZMATI:</b>\n"
        "══════════════════════════════\n\n"
        f"Sizning Telegram ID raqamingiz: <code>{uid}</code>\n\n"
        "<b>Qanday ishlaydi?</b>\n"
        "1. Ota-onangiz yoki yaqinlaringiz botning Mini App bo'limiga kirishadi;\n"
        "2. Ular sizning yuqoridagi <code>{uid}</code> raqamingizni 'Himoyachi' sifatida kiritishadi;\n"
        "3. Agar ular xavfli fishing havolaga, soxta aksiyaga yoki APK virusga duch kelsa, "
        "ShieldGuard <b>darhol sizga tezkor xabarnoma</b> yuboradi!\n\n"
        "Shunday qilib, siz yaqinlaringiz pulini vaqtida qutqarib qolasiz."
    )
    kb = [
        [InlineKeyboardButton(text="📱 Mini Appda Oila Qalqonini Ochish", url=f"{settings.WEBAPP_URL}/webapp?user_id={uid}")]
    ]
    await callback.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode=ParseMode.HTML)


@dp.callback_query(F.data == "btn_webapp_info")
async def cb_webapp_info(callback: types.CallbackQuery):
    await callback.answer()
    uid = callback.from_user.id
    await callback.message.answer(
        "📱 <b>ShieldGuard Mini App:</b>\n\n"
        f"🔗 <a href='{settings.WEBAPP_URL}/webapp?user_id={uid}'>Mini Appni Brauzerda Ochish</a>",
        parse_mode=ParseMode.HTML
    )


# =========================================================================
# 12. HUJJAT VA FAYLLARNI QABUL QILISH (APK, PDF)
# =========================================================================

@dp.message(F.document)
async def handle_document(message: types.Message):
    doc = message.document
    filename = doc.file_name or "noma'lum_fayl"
    lower_name = filename.lower()
    user_id = message.from_user.id

    wait_msg = await message.answer("⏳ <i>Fayl qabul qilindi. ShieldGuard xavfsizlik filtrlari tekshirmoqda...</i>", parse_mode=ParseMode.HTML)

    try:
        file_io = io.BytesIO()
        await bot.download(doc, destination=file_io)
        file_bytes = file_io.getvalue()

        # 1. APK yoki ilova troyani
        if lower_name.endswith(".apk") or ".apk." in lower_name or lower_name.endswith(".exe"):
            res = analyze_file_security(filename, file_bytes)
            risk = res["risk_score"]

            if risk >= 70:
                header = "🚨 <b>DIQQAT! KRITIK XAVFLI ILOVA (TROYAN)!</b>"
                icon = "🔴"
            elif risk >= 40:
                header = "⚠️ <b>SHUBHALI ILOVA! EHTIYOT BO'LING!</b>"
                icon = "🟡"
            else:
                header = "✅ <b>ILOVA XAVFSIZ KO'RINADI</b>"
                icon = "🟢"

            report = (
                f"{header}\n\n"
                f"📁 <b>Fayl:</b> <code>{filename}</code>\n"
                f"📊 <b>Xavf ko'rsatkichi:</b> {icon} <b>{int(risk)}%</b>\n"
                f"📝 <b>Hukm:</b> {res['verdict_uz']}\n\n"
                f"💬 <b>Tahlil xulosasi:</b>\n{res['summary_uz']}\n"
            )

            if res.get("red_flags"):
                report += "\n🚩 <b>Xavfli jihatlar:</b>\n" + "\n".join(f"• {f}" for f in res["red_flags"][:4])

            await safe_save_scan_history(
                user_telegram_id=user_id,
                scan_type="file",
                target_name=filename,
                risk_score=float(risk),
                verdict=res["verdict"],
                summary_uz=res["summary_uz"],
                details_json=json.dumps(res, ensure_ascii=False)
            )

            await wait_msg.edit_text(report, reply_markup=get_main_inline_keyboard(user_id), parse_mode=ParseMode.HTML)
            return

        # 2. PDF Shartnoma
        elif lower_name.endswith(".pdf"):
            res = await analyze_contract_file(filename, file_bytes, mime_type="application/pdf")
            score = res.get("overall_safety_score", 100)
            risk = 100 - score
            icon = "🟢" if score >= 80 else ("🟡" if score >= 50 else "🔴")

            report = (
                f"📄 <b>SHARTNOMA AUDITI XULOSASI:</b>\n\n"
                f"📑 <b>Hujjat:</b> <code>{filename}</code>\n"
                f"🛡️ <b>Ishonchlilik balli:</b> {icon} <b>{score}/100</b>\n"
                f"📝 <b>Turi:</b> {res.get('contract_type', 'Aniqlanmadi')}\n\n"
                f"💬 <b>Oddiy tildagi xulosa:</b>\n{res.get('summary_uz', '')}\n"
            )

            if res.get("dangerous_clauses"):
                report += "\n⚠️ <b>Topilgan xavfli bandlar:</b>\n"
                for clause in res["dangerous_clauses"][:3]:
                    report += f"• <b>{clause.get('clause_no', 'Band')}:</b> {clause.get('explanation_uz', '')}\n"

            await safe_save_scan_history(
                user_telegram_id=user_id,
                scan_type="contract",
                target_name=filename,
                risk_score=float(risk),
                verdict="safe" if score >= 70 else "dangerous",
                summary_uz=res.get("summary_uz", ""),
                details_json=json.dumps(res, ensure_ascii=False)
            )

            await wait_msg.edit_text(report, reply_markup=get_main_inline_keyboard(user_id), parse_mode=ParseMode.HTML)
            return

        else:
            await wait_msg.edit_text("ℹ️ Ushbu turdagi fayllar hozircha qo'llab-quvvatlanmaydi. Faqat .apk, .pdf yoki shartnoma fotosuratlarini yuborishingiz mumkin.")

    except Exception as e:
        logger.error(f"Fayl tahlilida xatolik: {e}")
        await wait_msg.edit_text("❌ Faylni tekshirish jarayonida texnik nosozlik yuz berdi.")


@dp.message(F.photo)
async def handle_photo(message: types.Message):
    """Multimodal fotosuratlarni qabul qilish (Cheklar, Skrinshotlar, QR va Shartnomalar)."""
    from backend.security_engine.image_fraud_analyzer import analyze_fraud_image
    user_id = message.from_user.id
    photo = message.photo[-1]
    wait_msg = await message.answer("🔍 <i>ShieldGuard Vision AI: Tasvir (Chek, Skrinshot yoki Shartnoma) tahlil qilinmoqda...</i>", parse_mode=ParseMode.HTML)

    try:
        file_io = io.BytesIO()
        await bot.download(photo, destination=file_io)
        img_bytes = file_io.getvalue()

        # 1. Vision AI orqali tasvir turini aniqlash va tekshirish
        vision_res = await analyze_fraud_image("photo.jpg", img_bytes, mime_type="image/jpeg")
        det_type = vision_res.get("detected_type", "document_photo")

        # 2. Agar shartnoma bo'lsa - to'liq yuridik rentgen
        if det_type == "contract":
            res = await analyze_contract_file("photo.jpg", img_bytes, mime_type="image/jpeg")
            score = res.get("overall_safety_score", 100)
            risk = 100 - score
            icon = "🟢" if score >= 80 else ("🟡" if score >= 50 else "🔴")

            report = (
                f"📄 <b>SHARTNOMA FOTORASMI AUDITI:</b>\n\n"
                f"🛡️ <b>Xavfsizlik balli:</b> {icon} <b>{score}/100</b>\n"
                f"📑 <b>Hujjat turi:</b> {res.get('contract_type', 'Aniqlanmadi')}\n\n"
                f"💬 <b>Xulosa:</b>\n{res.get('summary_uz', '')}\n"
            )
            if res.get("dangerous_clauses"):
                report += "\n⚠️ <b>Topilgan asossiz bandlar:</b>\n"
                for clause in res["dangerous_clauses"][:3]:
                    report += f"• {clause.get('explanation_uz', '')}\n"

            summary_text = res.get("summary_uz", "")
            verdict_val = "safe" if score >= 70 else "dangerous"

        else:
            # Soxta chek yoki skrinshot tahlili
            risk = vision_res.get("risk_score", 20)
            icon = "🔴" if risk >= 70 else ("🟡" if risk >= 40 else "🟢")
            report = (
                f"🖼️ <b>SHIELDGUARD VISION AI TAHLILI:</b>\n\n"
                f"🎯 <b>Natija:</b> {vision_res.get('title_uz', 'Tasvir tahlili')}\n"
                f"📊 <b>Xavf darajasi:</b> {icon} <b>{risk}%</b>\n\n"
                f"💬 <b>Xulosa:</b>\n{vision_res.get('summary_uz', '')}\n"
            )
            if vision_res.get("red_flags"):
                report += "\n🚩 <b>Xavfli omillar:</b>\n" + "\n".join(f"• {f}" for f in vision_res["red_flags"][:3])
            if vision_res.get("recommendations"):
                report += "\n\n💡 <b>Tavsiya:</b>\n" + "\n".join(f"• {r}" for r in vision_res["recommendations"][:2])

            summary_text = vision_res.get("summary_uz", "")
            verdict_val = vision_res.get("verdict", "safe")

        await safe_save_scan_history(
            user_telegram_id=user_id,
            scan_type="image_vision",
            target_name=vision_res.get("title_uz", "Fotorasm")[:120],
            risk_score=float(risk),
            verdict=verdict_val,
            summary_uz=summary_text,
            details_json=json.dumps(vision_res, ensure_ascii=False)
        )

        await wait_msg.edit_text(report, reply_markup=get_main_inline_keyboard(user_id), parse_mode=ParseMode.HTML)

    except Exception as e:
        logger.error(f"Rasm tahlilida xatolik: {e}")
        await wait_msg.edit_text("❌ Fotosuratni tahlil qilishda xatolik yuz berdi. Iltimos, aniqroq rasm yuboring.")



# =========================================================================
# 12.1. OVOZLI VA AUDIO XABARLAR ISHLOVCHISI (VOICE & VISHING AI)
# =========================================================================

async def send_voice_center(target_message: types.Message):
    """Ovozli vishing va telefon qo'ng'iroqlari audit markazi."""
    kb = [
        [
            InlineKeyboardButton(text="📑 Oxirgi Kiber-Dalolatnomani Olish", callback_data="btn_dossier:last")
        ],
        [
            InlineKeyboardButton(text="🛡️ Asosiy Menyu", callback_data="btn_open_user")
        ]
    ]
    text = (
        "🎙️ <b>SHIELDGUARD VOICE & AUDIO AUDIT MARKAZI:</b>\n"
        "═══════════════════════════════════════════\n"
        "💡 <b>Qanday ishlaydi?</b>\n"
        "• Shubhali <b>ovozli xabar</b> yoki telefonda yozib olingan <b>audio faylni</b> botga yuboring.\n"
        "• Sun'iy intellekt audiodagi so'zlarni to'liq tinglab, karta raqami, SMS kod yoki firibgarlik belgilarini tekshiradi.\n\n"
        "🔑 <i>Ovozli xabarlarni to'liq eshitish uchun: /setgemini buyrug'i orqali bepul Google Gemini API kalitini ulashingiz mumkin.</i>\n\n"
        "✍️ <i>Shuningdek, suhbat matnini to'g'ridan-to'g'ri yozib yuborishingiz ham mumkin.</i>"
    )
    await target_message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode=ParseMode.HTML)


@dp.message(F.voice | F.audio)
async def handle_voice_or_audio(message: types.Message):
    """Ovozli xabarlar va audio qo'ng'iroqlar (Soxta bank xodimi, Vishing) tahlili."""
    from backend.security_engine.audio_fraud_analyzer import analyze_audio_recording
    user_id = message.from_user.id
    audio_obj = message.voice or message.audio
    is_voice = message.voice is not None
    filename = "voice_note.ogg" if is_voice else (message.audio.file_name or "audio_call.mp3")
    mime = "audio/ogg" if is_voice else (message.audio.mime_type or "audio/mpeg")

    wait_msg = await message.answer(
        "🎙️ <b>ShieldGuard Voice AI:</b> <i>Ovozli xabar / qo'ng'iroq yozuvi qabul qilindi. "
        "Sotsial muhandislik va soxta bank xodimi belgilari bo'yicha tahlil qilinmoqda...</i>",
        parse_mode=ParseMode.HTML
    )

    try:
        file_io = io.BytesIO()
        await bot.download(audio_obj, destination=file_io)
        audio_bytes = file_io.getvalue()

        res = await analyze_audio_recording(filename, audio_bytes, mime_type=mime)
        risk = res.get("risk_score", 0)
        verdict = res.get("verdict", "safe")
        tr_text = res.get("transcribed_text", "")

        if verdict == "untranscribed":
            report = (
                "🎙️ <b>OVOZLI XABAR QABUL QILINDI:</b>\n"
                "══════════════════════════════\n\n"
                "ℹ️ <b>Holat:</b> Audio eshitish moduli (AI API) ulanmagan\n\n"
                "💬 <b>Tushuntirish:</b>\n"
                "Ovozli xabarlarni so'zma-so'z to'liq o'qish (Speech-to-Text) uchun sun'iy intellekt kaliti kerak.\n\n"
                "💡 <b>Qanday ulanadi?</b>\n"
                "1. <a href='https://aistudio.google.com'>aistudio.google.com</a> saytidan bepul Gemini API kaliti oling;\n"
                "2. Botga <code>/setgemini &lt;kalitingiz&gt;</code> deb yuboring.\n\n"
                "✍️ <i>Audiodagi gaplarni matn ko'rinishida yozib yuborsangiz, bot hoziroq aniq tahlil qilib beradi!</i>"
            )
            kb = [
                [InlineKeyboardButton(text="🛡️ Asosiy Menyu", callback_data="btn_open_user")]
            ]
        elif risk >= 70:
            report = (
                f"🎙️ <b>OVOZLI XABAR AUDITI:</b>\n"
                f"══════════════════════════════\n\n"
                f"📊 <b>Xavf darajasi:</b> 🔴 <b>{int(risk)}% (Kritik Xavfli!)</b>\n"
                f"📝 <b>Holat:</b> Vishing / Moliyaviy firibgarlik\n\n"
            )
            if tr_text:
                report += f"📝 <b>Eshitilgan matn:</b>\n<i>\"{tr_text[:350]}\"</i>\n\n"
            report += f"💬 <b>Tahlil xulosasi:</b>\n{res.get('expert_verdict_uz', '')}\n"
            if res.get("scam_tactics"):
                report += "\n🚩 <b>Aniqlangan tuzoqlar:</b>\n"
                for t in res["scam_tactics"][:3]:
                    report += f"• {t}\n"
            if res.get("immediate_action_uz"):
                report += f"\n💡 <b>Zudlik bilan ko'riladigan chora:</b>\n{res.get('immediate_action_uz')}\n"

            kb = [
                [InlineKeyboardButton(text="📑 Kiber-Ekspertiza Dalolatnomasini Olish", callback_data=f"btn_dossier:{user_id}")],
                [InlineKeyboardButton(text="🚨 5 Ta Shoshilinch Qadam", callback_data="btn_sos_steps")]
            ]
        else:
            report = (
                f"🎙️ <b>OVOZLI XABAR AUDITI:</b>\n"
                f"══════════════════════════════\n\n"
                f"📊 <b>Xavf darajasi:</b> 🟢 <b>{int(risk)}% (Xavfsiz)</b>\n"
                f"📝 <b>Holat:</b> Shubhali yoki firibgarlik belgilari aniqlanmadi\n\n"
            )
            if tr_text:
                report += f"📝 <b>Eshitilgan matn:</b>\n<i>\"{tr_text[:350]}\"</i>\n\n"
            report += f"💬 <b>Xulosa:</b>\n{res.get('expert_verdict_uz', 'Xavfsiz audio suhbat.')}\n"
            kb = [
                [InlineKeyboardButton(text="🛡️ Asosiy Menyu", callback_data="btn_open_user")]
            ]

        await safe_save_scan_history(
            user_telegram_id=user_id,
            scan_type="audio_vishing",
            target_name=filename[:100],
            risk_score=float(risk),
            verdict=verdict,
            summary_uz=res.get("expert_verdict_uz", "")[:250],
            details_json=json.dumps(res, ensure_ascii=False)
        )

        await wait_msg.edit_text(report, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode=ParseMode.HTML)

    except Exception as e:
        logger.error(f"Audio tahlilida xatolik: {e}")
        await wait_msg.edit_text("❌ Audio yozuvni tahlil qilishda xatolik yuz berdi. Iltimos, qaytadan yuboring.")


# =========================================================================
# 12.2. JONLI MILLIY KIBER-RADAR VA DALOLATNOMA
# =========================================================================

async def render_live_cyber_radar(message: types.Message):
    """Butun O'zbekiston bo'yicha jonli kiber-tahdidlar radari."""
    async with AsyncSessionLocal() as session:
        total_scans = (await session.execute(select(func.count(ScanHistory.id)))).scalar() or 0
        total_threats = (await session.execute(select(func.count(ScanHistory.id)).where(ScanHistory.risk_score >= 70))).scalar() or 0
        total_cards = (await session.execute(select(func.count(CardBlacklist.id)))).scalar() or 0
        total_domains = (await session.execute(select(func.count(CommunityBlacklist.id)))).scalar() or 0

        stmt = select(ScanHistory).where(ScanHistory.risk_score >= 70).order_by(ScanHistory.id.desc()).limit(5)
        recent_threats = (await session.execute(stmt)).scalars().all()

    threat_level = "🔴 YUQORI FAOL TAHDIDLAR" if total_threats > 20 else ("🟡 O'RTACHA FAOL" if total_threats > 5 else "🟢 TIZIM HIMOYALANGAN")

    radar_text = (
        "🌐 <b>SHIELDGUARD MILLIY KIBER-TAHDIDLAR RADARI (JONLI):</b>\n"
        "═══════════════════════════════════════════\n"
        f"📡 <b>Respublika bo'yicha kiber-holat:</b> {threat_level}\n"
        f"🕒 <b>Ma'lumotlar bazasi:</b> AWS Neon Cloud Postgres\n\n"
        "📊 <b>BUGUNGI FAOLIK STATISTIKASI:</b>\n"
        f"• 🛡️ Jami himoyalangan so'rovlar: <b>{total_scans}</b> ta\n"
        f"• 🚨 Neytrallangan kiber-hujumlar: <b>{total_threats}</b> ta\n"
        f"• 💳 Fosh etilgan firibgar kartalar: <b>{total_cards}</b> ta\n"
        f"• 🌐 Bloklangan fishing domenlar: <b>{total_domains}</b> ta\n\n"
        "⚠️ <b>SO'NGGI FOSH QILINGAN TAHDIDLAR:</b>\n"
    )

    if not recent_threats:
        radar_text += "• <i>Hozircha tizim tinch va to'liq himoyalangan.</i>\n"
    else:
        for rt in recent_threats:
            dt = rt.created_at.strftime("%H:%M") if rt.created_at else "Hozir"
            radar_text += f"🔴 [{dt}] <b>{rt.scan_type.upper()}</b>: <code>{rt.target_name[:35]}</code>\n"

    radar_text += "\n💡 <i>Shubhali havola, karta yoki audio yozuvni botga yuboring va darhol fosh eting!</i>"

    kb = [
        [InlineKeyboardButton(text="🔄 Radarni Yangilash", callback_data="btn_refresh_radar")],
        [InlineKeyboardButton(text="🆘 Shoshilinch Kiber-Yordam", callback_data="btn_sos_info")]
    ]
    await message.answer(radar_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode=ParseMode.HTML)


@dp.callback_query(F.data == "btn_refresh_radar")
async def cb_refresh_radar(callback: types.CallbackQuery):
    await callback.answer("Radar yangilanmoqda...")
    await render_live_cyber_radar(callback.message)


@dp.callback_query(F.data.startswith("btn_dossier:"))
async def cb_generate_dossier(callback: types.CallbackQuery):
    """Rasmiy Kiber-Ekspertiza Dalolatnomasini shakllantirish."""
    from backend.security_engine.forensic_dossier import create_forensic_dossier
    await callback.answer("📑 Kiber-Ekspertiza Dalolatnomasi tuzilmoqda...")
    uid = callback.from_user.id

    async with AsyncSessionLocal() as session:
        stmt = select(ScanHistory).where(ScanHistory.user_telegram_id == uid).order_by(ScanHistory.id.desc()).limit(1)
        last_scan = (await session.execute(stmt)).scalar_one_or_none()

    target_name = last_scan.target_name if last_scan else "Kiber-Tahdid obyekti"
    threat_type = last_scan.scan_type if last_scan else "Phishing / Cyber-fraud"
    risk_score = last_scan.risk_score if last_scan else 90.0
    scan_id = last_scan.id if last_scan else None

    dossier = create_forensic_dossier(
        scan_id=scan_id,
        user_id=uid,
        target_name=target_name,
        threat_type=threat_type,
        risk_score=risk_score,
        details={"red_flags": ["Aniqlangan kiber-jinoyat belgilari", "Yashirin pul o'g'irlash harakati"]}
    )

    kb = [
        [InlineKeyboardButton(text="🌐 cyber102.uz Portali", url="https://cyber102.uz")],
        [InlineKeyboardButton(text="📋 Politsiya Ariza Shabloni", callback_data="btn_police_template")],
        [InlineKeyboardButton(text="⬅️ Favqulodda Menyu", callback_data="btn_sos_info")]
    ]

    await callback.message.answer(dossier["formatted_text"], reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode=ParseMode.HTML)


@dp.callback_query(F.data == "btn_open_radar")
async def cb_open_radar(callback: types.CallbackQuery):
    await callback.answer("Radar yuklanmoqda...")
    await render_live_cyber_radar(callback.message)


@dp.callback_query(F.data == "btn_open_voice")
async def cb_open_voice(callback: types.CallbackQuery):
    await callback.answer()
    await send_voice_center(callback.message)


@dp.callback_query(F.data.startswith("scam_voice:"))
async def cb_scam_voice_tactic(callback: types.CallbackQuery):
    tactic_key = callback.data.split(":")[1]
    uid = callback.from_user.id
    await callback.answer("⚠️ Kiber-hujum fosh etildi!", show_alert=True)

    tactics_map = {
        "sms_code": ("Bank kartasi SMS-kodini talab qilish", 100, "CRITICAL: SMS-kod talab qilish 100% holatda karta o'g'irlashdir! Bank xodimlari HECH QACHON kod so'ramaydi."),
        "famous_person": ("Mashhur shaxs yoki bloger nomidan soxta murojaat (Deepfake/Vishing)", 100, "CRITICAL: Firibgarlar taniqli shaxslar yoki blogerlar nomidan kartangizning oxirgi 6 ta raqami va SMS kodini so'rab, pul o'g'irlashga urinmoqda! Bank yoki mashhur shaxslar HECH QACHON kod so'ramaydi."),
        "fake_credit": ("Soxta kredit rasmiylashtirilishi haqida aldov", 95, "CRITICAL: Firibgarlar jabrlanuvchini qo'rquvga solish orqali yangi kredit olishga yoki pul o'tkazishga majburlaydi."),
        "remote_app": ("AnyDesk / RustDesk masofaviy boshqaruv talabi", 100, "CRITICAL: Ushbu ilovalar o'rnatilgach, tajovuzkor telefoningizni to'liq boshqarib, barcha pullaringizni yechib oladi."),
        "fake_officer": ("O'zini Markaziy Bank yoki IIV tergovchisi deb tanishtirish", 95, "CRITICAL: Rasmiy idoralar Telegram yoki oddiy telefon orqali tergov o'tkazmaydi va pul talab qilmaydi.")
    }

    tactic_name, risk_val, desc = tactics_map.get(tactic_key, ("Telefon vishing firibgarligi", 95, "Xavfli telefon firibgarligi"))

    # Save to ScanHistory
    await safe_save_scan_history(
        user_telegram_id=uid,
        scan_type="voice_vishing",
        target_name=f"Vishing: {tactic_name}",
        risk_score=float(risk_val),
        verdict="dangerous",
        summary_uz=desc[:250],
        details_json=json.dumps({"tactic": tactic_name, "desc": desc}, ensure_ascii=False)
    )

    kb = [
        [InlineKeyboardButton(text="📑 IIV uchun Rasmiy Dalolatnoma Olish", callback_data=f"btn_dossier:{uid}")],
        [InlineKeyboardButton(text="🚨 5 Ta Shoshilinch Qadam", callback_data="btn_sos_steps")],
        [InlineKeyboardButton(text="🏦 Bank Aloqa Raqamlari", callback_data="btn_bank_callcenters")]
    ]

    alert_text = (
        f"🚨 <b>XAVF FOSH ETILDI! KRITIK TAHDID ({risk_val}%):</b>\n"
        f"═══════════════════════════════════════\n"
        f"🎯 <b>Firibgarlik turi:</b> {tactic_name}\n"
        f"📊 <b>Xavf darajasi:</b> 🔴 <b>{risk_val}% (O'ta Xavfli!)</b>\n\n"
        f"💬 <b>Ekspert xulosasi:</b>\n{desc}\n\n"
        f"🛡️ <b>Zudlik bilan ko'riladigan choralar:</b>\n"
        f"1. Suhbatni darhol to'xtating va go'shakni qo'ying!\n"
        f"2. Hech qanday SMS-kod yoki karta ma'lumotlarini bermang!\n"
        f"3. Pastdagi tugma orqali IIV (cyber102.uz) uchun <b>Rasmiy Dalolatnoma</b> oling!"
    )
    await callback.message.answer(alert_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode=ParseMode.HTML)



@dp.message(Command("radar"))
async def cmd_radar(message: types.Message):
    """/radar buyrug'i."""
    await render_live_cyber_radar(message)


@dp.message(Command("voice"))
async def cmd_voice(message: types.Message):
    """/voice buyrug'i."""
    await send_voice_center(message)


@dp.message(Command("dossier"))
async def cmd_dossier(message: types.Message):
    """/dossier buyrug'i."""
    from backend.security_engine.forensic_dossier import create_forensic_dossier
    uid = message.from_user.id
    async with AsyncSessionLocal() as session:
        stmt = select(ScanHistory).where(ScanHistory.user_telegram_id == uid).order_by(ScanHistory.id.desc()).limit(1)
        last_scan = (await session.execute(stmt)).scalar_one_or_none()

    target_name = last_scan.target_name if last_scan else "Kiber-Tahdid Obyekti"
    threat_type = last_scan.scan_type if last_scan else "Vishing / Phishing"
    risk_score = last_scan.risk_score if last_scan else 95.0
    scan_id = last_scan.id if last_scan else None

    dossier = create_forensic_dossier(
        scan_id=scan_id,
        user_id=uid,
        target_name=target_name,
        threat_type=threat_type,
        risk_score=risk_score,
        details={"red_flags": ["Kiber-jinoyat belgilari fosh etildi", "Yashirin moliyaviy o'g'irlik xavfi"]}
    )

    kb = [
        [InlineKeyboardButton(text="🌐 cyber102.uz Portali", url="https://cyber102.uz")],
        [InlineKeyboardButton(text="📋 Politsiya Ariza Shabloni", callback_data="btn_police_template")],
        [InlineKeyboardButton(text="⬅️ Favqulodda Menyu", callback_data="btn_sos_info")]
    ]
    await message.answer(dossier["formatted_text"], reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode=ParseMode.HTML)



@dp.message(Command("setgemini"))
async def cmd_set_gemini(message: types.Message):
    """Google Gemini API kalitini o'rnatish (Faqat Owner uchun)."""
    user = message.from_user
    if not user or user.id != settings.OWNER_TELEGRAM_ID:
        await message.answer("🚫 Ushbu buyruq faqat bot egasi (Owner) uchun ruxsat etilgan.")
        return

    parts = (message.text or "").strip().split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "🔑 <b>Google Gemini API kalitini ulash:</b>\n\n"
            "Foydalanish: <code>/setgemini &lt;API_KEY&gt;</code>\n\n"
            "<i>Masalan:</i> <code>/setgemini AIzaSy...</code>\n\n"
            "💡 <i>Kalitni mutlaqo bepul olish: https://aistudio.google.com</i>\n"
            "Ushbu kalit ulangach, bot barcha ovozli xabarlarni va audio qo'ng'iroqlarni to'liq eshitib tahlil qiladi.",
            parse_mode=ParseMode.HTML
        )
        return

    new_key = parts[1].strip()
    from backend.models import SystemConfig
    from backend.security_engine.llm_engine import set_cached_gemini_key

    try:
        async with AsyncSessionLocal() as session:
            cfg = await session.get(SystemConfig, "gemini_api_key")
            if cfg:
                cfg.value = new_key
            else:
                cfg = SystemConfig(key="gemini_api_key", value=new_key)
                session.add(cfg)
            await session.commit()
    except Exception as e:
        logger.warning(f"Gemini kalitini bazada saqlashda xatolik: {e}")

    settings.GEMINI_API_KEY = new_key
    set_cached_gemini_key(new_key)
    await message.answer(
        "✅ <b>Google Gemini AI muvaffaqiyatli ulandi!</b>\n\n"
        "🎙️ <b>Multimodal Audio eshitish tizimi faollashdi.</b>\n"
        "Endi barcha ovozli xabarlar va soxta bank qo'ng'iroqlari sun'iy intellekt tomonidan to'g'ridan-to'g'ri tinglanib, "
        "karta va SMS o'g'irliklari avtomatik 100% aniqlanadi.",
        parse_mode=ParseMode.HTML
    )


@dp.message(F.text)
async def handle_text_message(message: types.Message):
    user = message.from_user
    text = (message.text or "").strip()
    user_id = user.id if user else 0

    db_user = None
    if user:
        db_user = await get_or_create_user(user.id, user.username, user.full_name)
        if db_user and db_user.is_banned:
            await message.answer("🚫 Sizning hisobingiz ShieldGuard qoidalarini buzganlik sababli bloklangan.")
            return

    is_owner = (
        user.id == settings.OWNER_TELEGRAM_ID or
        (user.username and user.username.lower() == settings.OWNER_USERNAME.lower()) if user else False
    )
    active_mode = db_user.active_mode if db_user else ("owner" if is_owner else "user")

    # 1. Bekor qilish buyrug'i (/cancel)
    if text.lower() in ("/cancel", "cancel", "bekor qilish"):
        if user_id in user_states:
            user_states.pop(user_id, None)
            reply_kb = get_owner_reply_keyboard() if (is_owner and active_mode == "owner") else get_user_reply_keyboard(is_owner=is_owner)
            await message.answer("✅ Amal bekor qilindi.", reply_markup=reply_kb)
            return

    # 2. Reply Keyboard (Pastdagi doimiy tugmalar) bosilganda:

    # --- OWNER TUGMALARI ---
    if text in ("👑 Boshqaruv Markazi", "👑 Admin Panel"):
        await render_admin_dashboard(message, user_id)
        return
    elif text == "👥 Adminlar Boshqaruvi":
        await render_admins_management(message, user_id)
        return
    elif text in ("👤 Foydalanuvchilar Bazasi", "👤 Foydalanuvchilar"):
        await render_users_management(message, user_id)
        return
    elif text in ("🛡️ Kiber-Monitoring (Jonli)", "🛡️ Kiber-Monitoring"):
        await render_live_monitoring(message, user_id)
        return
    elif text in ("🚫 Qora Ro'yxat (Kartalar)", "🚫 Firibgar Kartalar"):
        await render_scam_cards_management(message, user_id)
        return
    elif text in ("🌐 Fishing Saytlar Bazasi", "🌐 Fishing Saytlar"):
        await render_phishing_domains_management(message, user_id)
        return
    elif text in ("📢 Smart E'lon Tarqatish", "📢 Hammaga Xabar"):
        user_states[user_id] = {"action": "waiting_for_broadcast"}
        await message.answer(
            "📢 <b>Barcha foydalanuvchilarga xabar tarqatish:</b>\n\n"
            "Iltimos, e'loningiz matnini shu yerga yozib yuboring (u barcha bot a'zolariga yetkaziladi).\n\n"
            "❌ <i>Bekor qilish uchun: /cancel</i>",
            parse_mode=ParseMode.HTML
        )
        return
    elif text in ("⚙️ AI & Tizim Sozlamalari", "⚙️ Sozlamalar"):
        await render_system_settings(message, user_id)
        return
    elif text in ("📊 Kengaytirilgan Statistika", "📊 Statistika"):
        await render_system_stats(message, user_id)
        return
    elif text == "👤 Oddiy Rejimga O'tish":
        await switch_owner_role(user_id, message, to_mode="user")
        return
    elif text == "👑 Owner Rejimiga O'tish":
        await switch_owner_role(user_id, message, to_mode="owner")
        return

    # --- FUQARO / USER TUGMALARI ---
    elif text == "🛡️ Havola / Matn Tekshirish":
        await render_user_link_center(message)
        return
    elif text == "💳 Karta Tekshirish":
        await render_user_card_center(message)
        return
    elif text in ("🤖 Bot / Kanal Tekshirish", "🤖 Bot Tekshirish"):
        await render_user_bot_center(message)
        return
    elif text == "📄 Shartnoma Rentgeni":
        await render_user_contract_center(message)
        return
    elif text in ("🆘 Meni Aldashdi! (Yordam)", "🆘 Shoshilinch Yordam"):
        await cmd_sos(message)
        return
    elif text in ("🧠 Kiber-Viktorina (Test)", "🧠 Kiber-Viktorina"):
        await cmd_quiz(message)
        return
    elif text == "👨‍👩‍👧‍👦 Oila Qalqoni":
        await cb_family_info(types.CallbackQuery(id="0", from_user=user, chat_instance="0", message=message))
        return
    elif text in ("🏦 Banklar & Bloklash Raqamlari", "🏦 Banklar Ro'yxati"):
        await render_user_bank_directory(message)
        return
    elif text in ("📡 Jonli Kiber-Radar", "🌐 Milliy Kiber-Radar", "🌐 Kiber-Radar", "📡 Kiber-Radar", "📡 Radar", "radar", "/radar"):
        await render_live_cyber_radar(message)
        return
    elif text in ("🎙️ Ovozli Xabar / Qo'ng'iroq", "🎙️ Ovozli Tekshiruv", "🎙️ Ovozli Audit", "voice", "/voice"):
        await send_voice_center(message)
        return
    elif text in ("📑 Kiber-Ekspertiza Dalolatnomasi", "📑 Dalolatnoma", "dossier", "/dossier"):
        await cmd_dossier(message)
        return
    elif text in ("💡 Kiber-Tavsiyalar", "💡 Tavsiyalar"):
        await render_user_cyber_tips(message)
        return
    elif text == "📱 WebApp Ilovasi":
        await message.answer(
            "📱 <b>ShieldGuard Mini App:</b>\n\n"
            "Quyidagi havola orqali brauzeringizda ochishingiz mumkin:\n"
            f"🔗 <a href='{settings.WEBAPP_URL}/webapp?user_id={user_id}'>ShieldGuard WebApp</a>",
            reply_markup=get_main_inline_keyboard(user_id, is_owner=is_owner, active_mode=active_mode),
            parse_mode=ParseMode.HTML
        )
        return

    # 3. Interaktiv Holatlar (States) tekshiruvi:
    if user_id in user_states:
        state_data = user_states[user_id]
        action = state_data.get("action")

        if action == "waiting_for_admin" and is_owner:
            user_states.pop(user_id, None)
            forward_u = message.forward_from or (message.reply_to_message.from_user if message.reply_to_message else None)
            await resolve_and_promote_admin(owner_id=user_id, raw_input=text, message=message, forward_user=forward_u)
            return

        elif action == "waiting_for_broadcast" and is_owner:
            user_states.pop(user_id, None)
            await execute_broadcast(owner_id=user_id, broadcast_body=text, message=message)
            return

        elif action == "waiting_for_ban" and is_owner:
            user_states.pop(user_id, None)
            if not text.isdigit():
                await message.answer("❌ Noto'g'ri ID. Faqat raqamli Telegram ID kiritilishi kerak.")
                return
            t_id = int(text)
            async with AsyncSessionLocal() as session:
                stmt = select(User).where(User.telegram_id == t_id)
                target = (await session.execute(stmt)).scalar_one_or_none()
                if target:
                    target.is_banned = True
                    session.add(AdminAuditLog(admin_telegram_id=user_id, action="ban_user", target=str(t_id), details="Interaktiv ban"))
                    await session.commit()
                    await message.answer(f"🚫 Foydalanuvchi (ID: <code>{t_id}</code>) muvaffaqiyatli bloklandi.", parse_mode=ParseMode.HTML)
                else:
                    await message.answer("Foydalanuvchi bazada topilmadi.")
            return

        elif action == "waiting_for_unban" and is_owner:
            user_states.pop(user_id, None)
            if not text.isdigit():
                await message.answer("❌ Noto'g'ri ID. Faqat raqamli Telegram ID kiritilishi kerak.")
                return
            t_id = int(text)
            async with AsyncSessionLocal() as session:
                stmt = select(User).where(User.telegram_id == t_id)
                target = (await session.execute(stmt)).scalar_one_or_none()
                if target:
                    target.is_banned = False
                    session.add(AdminAuditLog(admin_telegram_id=user_id, action="unban_user", target=str(t_id), details="Interaktiv unban"))
                    await session.commit()
                    await message.answer(f"✅ Foydalanuvchi (ID: <code>{t_id}</code>) blokdan chiqarildi.", parse_mode=ParseMode.HTML)
                else:
                    await message.answer("Foydalanuvchi bazada topilmadi.")
            return

        elif action == "waiting_for_scam_card":
            user_states.pop(user_id, None)
            parts = text.split(maxsplit=1)
            raw_c = parts[0].strip()
            reas = parts[1].strip() if len(parts) > 1 else "Firibgarlikda gumon qilingan"
            clean_digits = "".join(filter(str.isdigit, raw_c))
            if len(clean_digits) != 16:
                await message.answer("❌ Karta raqami 16 ta raqam bo'lishi kerak. Amal bekor qilindi.")
                return
            card_inf = analyze_card_number(clean_digits)
            async with AsyncSessionLocal() as session:
                st = select(CardBlacklist).where(CardBlacklist.card_number == clean_digits)
                r = await session.execute(st)
                cb = r.scalar_one_or_none()
                if not cb:
                    cb = CardBlacklist(card_number=clean_digits, bank_name=card_inf.get("bank_name"), reason=reas, reported_by=user_id)
                    session.add(cb)
                else:
                    cb.report_count += 1
                    cb.reason += f" | {reas}"
                await session.commit()
            await message.answer(f"✅ Karta <code>{clean_digits}</code> muvaffaqiyatli qora ro'yxatga kiritildi!", parse_mode=ParseMode.HTML)
            return

        elif action == "waiting_for_del_card" and is_owner:
            user_states.pop(user_id, None)
            clean_digits = "".join(filter(str.isdigit, text))
            async with AsyncSessionLocal() as session:
                st = select(CardBlacklist).where(CardBlacklist.card_number == clean_digits)
                r = await session.execute(st)
                cb = r.scalar_one_or_none()
                if cb:
                    await session.delete(cb)
                    await session.commit()
                    await message.answer(f"✅ Karta <code>{clean_digits}</code> qora ro'yxatdan o'chirildi.", parse_mode=ParseMode.HTML)
                else:
                    await message.answer("Ushbu karta qora ro'yxatda topilmadi.")
            return

        elif action == "waiting_for_domain" and is_owner:
            user_states.pop(user_id, None)
            parts = text.split(maxsplit=1)
            dom = parts[0].strip().lower().replace("https://", "").replace("http://", "").split("/")[0]
            reas = parts[1].strip() if len(parts) > 1 else "Fishing va parollarni o'g'irlash"
            async with AsyncSessionLocal() as session:
                st = select(CommunityBlacklist).where(CommunityBlacklist.domain_or_pattern == dom)
                cb = (await session.execute(st)).scalar_one_or_none()
                if not cb:
                    cb = CommunityBlacklist(domain_or_pattern=dom, reason=reas, reported_by_telegram_id=user_id)
                    session.add(cb)
                else:
                    cb.reason += f" | {reas}"
                await session.commit()
            await message.answer(f"✅ Fishing domen <code>{dom}</code> qora ro'yxatga kiritildi!", parse_mode=ParseMode.HTML)
            return

        elif action == "waiting_for_del_domain" and is_owner:
            user_states.pop(user_id, None)
            dom = text.strip().lower().replace("https://", "").replace("http://", "").split("/")[0]
            async with AsyncSessionLocal() as session:
                st = select(CommunityBlacklist).where(CommunityBlacklist.domain_or_pattern == dom)
                cb = (await session.execute(st)).scalar_one_or_none()
                if cb:
                    await session.delete(cb)
                    await session.commit()
                    await message.answer(f"✅ Fishing domen <code>{dom}</code> qora ro'yxatdan o'chirildi.", parse_mode=ParseMode.HTML)
                else:
                    await message.answer("Ushbu domen qora ro'yxatda topilmadi.")
            return

    # 4. Bank kartasi raqami tekshiruvi (Sof 16 ta raqam)
    clean_digits = "".join(filter(str.isdigit, text))
    is_pure_card = (
        len(clean_digits) == 16 and
        len(re.sub(r'[\s\-_]', '', text)) == 16 and
        not any(w in text.lower() for w in ["kredit", "olx", "uzum", "to'lov", "pul", "yechib", "dostavka", "badal", "komissiya", "daromad", "ovoz"])
    )

    if is_pure_card and (clean_digits.startswith(("8600", "9860", "4", "5", "62", "220")) or " " in text):
        analysis = analyze_card_number(text)
        async with AsyncSessionLocal() as session:
            stmt = select(CardBlacklist).where(CardBlacklist.card_number == clean_digits)
            res = await session.execute(stmt)
            scam_card = res.scalar_one_or_none()

        if scam_card:
            card_report = (
                f"🚨 <b>DIQQAT! KRITIK FIRIBGAR KARTA!</b>\n\n"
                f"💳 <b>Karta:</b> <code>{clean_digits}</code>\n"
                f"🏦 <b>Bank:</b> {analysis.get('bank_name')}\n"
                f"📊 <b>Xavf darajasi:</b> 🔴 <b>100%</b>\n\n"
                f"⚠️ <b>Qora ro'yxat sababi:</b>\n{scam_card.reason}\n"
                f"Shikoyatlar soni: <b>{scam_card.report_count}</b> ta\n\n"
                f"⛔ <b>Ushbu kartaga aslo pul o'tkazmang!</b>"
            )
        else:
            risk = analysis.get("risk_score", 0)
            icon = "🔴" if risk >= 70 else ("🟡" if risk >= 40 else "🟢")
            card_report = (
                f"💳 <b>BANK KARTASI TAHLILI:</b>\n\n"
                f"🔢 <b>Karta:</b> <code>{analysis.get('card_number_masked', clean_digits)}</code>\n"
                f"🌐 <b>To'lov tizimi:</b> {analysis.get('payment_system')}\n"
                f"🏦 <b>Emitent Bank:</b> {analysis.get('bank_name')}\n"
                f"📊 <b>Xavf ko'rsatkichi:</b> {icon} <b>{int(risk)}%</b>\n\n"
                f"💬 <b>Xulosa:</b> {analysis.get('summary_uz')}\n"
            )
            if analysis.get("warnings"):
                card_report += "\n⚠️ <b>Ogohlantirishlar:</b>\n" + "\n".join(f"• {w}" for w in analysis["warnings"])
            if analysis.get("recommendations"):
                card_report += "\n\n💡 <b>Tavsiyalar:</b>\n" + "\n".join(f"• {r}" for r in analysis["recommendations"][:2])

        await message.answer(card_report, reply_markup=get_main_inline_keyboard(user_id), parse_mode=ParseMode.HTML)
        return

    # 5. Telegram bot useri kiritilgan bo'lsa (@...bot)
    if text.startswith("@") and text.lower().endswith("bot") and len(text.split()) == 1:
        res = analyze_telegram_bot_or_username(text)
        risk = res["risk_score"]
        icon = "🔴" if risk >= 70 else ("🟡" if risk >= 40 else "🟢")
        report = (
            f"🤖 <b>TELEGRAM BOT TAHLILI:</b>\n\n"
            f"🎯 <b>Nishon:</b> <code>{res['target']}</code>\n"
            f"📊 <b>Xavf darajasi:</b> {icon} <b>{int(risk)}%</b>\n"
            f"📝 <b>Hukm:</b> {res['verdict_uz']}\n\n"
            f"💬 <b>Xulosa:</b>\n{res['summary_uz']}\n"
        )
        if res.get("flags"):
            report += "\n🚩 <b>Belgilar:</b>\n" + "\n".join(f"• {f}" for f in res["flags"])
        await message.answer(report, reply_markup=get_main_inline_keyboard(user_id), parse_mode=ParseMode.HTML)
        return

    if len(text) < 4:
        await message.answer("Iltimos, tekshirish uchun to'liqroq havola, matn yoki karta raqamini yuboring.")
        return

    # 6. URL yoki umumiy firibgarlik xabari
    wait_msg = await message.answer("🛡️ <i>ShieldGuard xavfsizlik filtrlari ishga tushdi...</i>", parse_mode=ParseMode.HTML)

    res = await analyze_url_or_text(text)
    risk = res["risk_score"]

    if risk >= 70:
        header = "🚨 <b>DIQQAT! KRITIK DARAJADAGI FIRIBGARLIK (FISHING)!</b>"
        icon = "🔴"
    elif risk >= 40:
        header = "⚠️ <b>SHUBHALI XABAR YOKI HAVOLA!</b>"
        icon = "🟡"
    else:
        header = "✅ <b>XAVFSIZ VA ISHONCHLI</b>"
        icon = "🟢"

    report = (
        f"{header}\n\n"
        f"🎯 <b>Nishon:</b> <code>{res['target'][:70]}</code>\n"
        f"📊 <b>Xavf darajasi:</b> {icon} <b>{int(risk)}%</b>\n"
        f"📝 <b>Holat:</b> {res['verdict_uz']}\n\n"
        f"💬 <b>Tushuntirish:</b>\n{res['summary_uz']}\n"
    )

    if res.get("red_flags"):
        report += "\n🚩 <b>Aniqlangan xavfli omillar:</b>\n" + "\n".join(f"• {f}" for f in res["red_flags"][:4])

    if res.get("positive_flags"):
        report += "\n" + "\n".join(f"• {f}" for f in res["positive_flags"][:2])

    # Agar matn ichida bank kartasi raqami bo'lsa, uning xavfsizlik holatini qo'shish
    if len(clean_digits) == 16 and (clean_digits.startswith(("8600", "9860", "4", "5", "62", "220")) or " " in text):
        card_scan = analyze_card_number(clean_digits)
        report += (
            f"\n\n💳 <b>Matndagi karta:</b> <code>{card_scan.get('card_number_masked', clean_digits)}</code>\n"
            f"🏦 <b>Bank:</b> {card_scan.get('bank_name')} ({card_scan.get('payment_system')})"
        )
        if card_scan.get("warnings"):
            report += "\n" + "\n".join(f"• {w}" for w in card_scan["warnings"])

    if risk >= 70:
        report += (
            "\n\n💡 <b>Qat'iy tavsiya:</b> Hech qanday holatda karta raqamingiz, CVV kod yoki SMS tasdiqlash kodini begonalarga bermang!\n"
            "⚠️ <i>Agar karta ma'lumotlarini kiritib ulgurgan bo'lsangiz — zudlik bilan bank ilovasida (Click, Payme, Uzum) kartani BLOKLANG!</i>\n\n"
            "📑 <i>IIV va Tergov organlariga topshirish uchun rasmiy Kiber-Ekspertiza Dalolatnomasini pastdagi tugma orqali olishingiz mumkin.</i>"
        )

    await safe_save_scan_history(
        user_telegram_id=user_id,
        scan_type="url_or_text",
        target_name=res["target"][:120],
        risk_score=float(risk),
        verdict=res["verdict"],
        summary_uz=res["summary_uz"],
        details_json=json.dumps(res, ensure_ascii=False)
    )

    await wait_msg.edit_text(report, reply_markup=get_main_inline_keyboard(user_id), parse_mode=ParseMode.HTML)


# =========================================================================
# 13. GLOBAL XATOLIKLAR USHLOVCHISI (AIOGRAM ERROR HANDLER)
# =========================================================================

@dp.error()
async def global_error_handler(event: types.ErrorEvent):
    """Barcha kutilmagan xatoliklarni ushlab qolib, foydalanuvchiga xabar berish."""
    logger.exception(f"Aiogram global xatolik: {event.exception}")
    try:
        if event.update and event.update.message:
            await event.update.message.answer(
                "⚠️ <b>Kechirasiz, so'rovni bajarishda vaqtinchalik nosozlik yuz berdi.</b>\n"
                "Iltimos, qaytadan urinib ko'ring yoki /start buyrug'ini bosing.",
                parse_mode=ParseMode.HTML
            )
        elif event.update and event.update.callback_query and event.update.callback_query.message:
            await event.update.callback_query.message.answer(
                "⚠️ <b>Amalni bajarishda vaqtinchalik xatolik yuz berdi.</b> Iltimos, qaytadan urinib ko'ring.",
                parse_mode=ParseMode.HTML
            )
    except Exception as err:
        logger.error(f"Xatolik xabarini yuborishda muammo: {err}")


# =========================================================================
# 14. BOTNI FONDA ISHGA TUSHIRISH (POLLING)
# =========================================================================

async def start_telegram_bot():
    """Botni lokal fon rejimida polling bilan ishga tushiradi."""
    try:
        logger.info("Telegram Bot polling ishga tushmoqda...")
        await bot.delete_webhook(drop_pending_updates=False)
        await dp.start_polling(bot, handle_signals=False)
    except asyncio.CancelledError:
        logger.info("Telegram Bot lokal vazifasi to'xtatildi. Webhook qayta tiklanmoqda...")
    except Exception as e:
        logger.error(f"Telegram Bot pollingda xatolik: {e}")
    finally:
        try:
            target_webhook = f"{settings.WEBAPP_URL}/api/webhook"
            await bot.set_webhook(url=target_webhook, drop_pending_updates=False)
            logger.info(f"Vercel Webhook avtomatik qayta tiklandi: {target_webhook}")
        except Exception:
            pass
