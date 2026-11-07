import asyncio
import io
import json
import logging
import re
from typing import Optional, List
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
from sqlalchemy import func, or_
from backend.config import settings
from backend.database import AsyncSessionLocal
from backend.models import User, ScanHistory, CardBlacklist, AdminAuditLog, BroadcastMessage
from backend.security_engine.url_analyzer import analyze_url_or_text
from backend.security_engine.apk_analyzer import analyze_file_security
from backend.security_engine.contract_analyzer import analyze_contract_file
from backend.security_engine.card_analyzer import analyze_card_number
from backend.security_engine.bot_inspector import analyze_telegram_bot_or_username
from backend.utils import notify_family_guardians, send_telegram_message

logger = logging.getLogger(__name__)

bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

# Interaktiv holatlar (FSM o'rniga tezkor xotira lug'ati)
user_states = {}


# =========================================================================
# 1. FOYDALANUVCHINI ANIQLASH VA BAZA BILAN ISHLASH
# =========================================================================

async def get_or_create_user(telegram_id: int, username: Optional[str], full_name: Optional[str]) -> User:
    """Foydalanuvchini bazadan qidirish, yangilash va Owner darajasini o'rnatish."""
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.telegram_id == telegram_id)
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()

        is_owner = (telegram_id == settings.OWNER_TELEGRAM_ID or (username and username.lower() == settings.OWNER_USERNAME.lower()))

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


# =========================================================================
# 2. TUGMALAR (REPLY KEYBOARD & INLINE KEYBOARD)
# =========================================================================

def get_owner_reply_keyboard() -> ReplyKeyboardMarkup:
    """Owner uchun pastdagi doimiy boshqaruv tugmalari (ReplyKeyboardMarkup)."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🛡️ Havola / Matn Tekshirish"),
                KeyboardButton(text="💳 Karta Tekshirish")
            ],
            [
                KeyboardButton(text="🤖 Bot Tekshirish"),
                KeyboardButton(text="📄 Shartnoma Rentgeni")
            ],
            [
                KeyboardButton(text="👑 Admin Panel"),
                KeyboardButton(text="👥 Adminlar Boshqaruvi")
            ],
            [
                KeyboardButton(text="📢 Hammaga Xabar"),
                KeyboardButton(text="🚫 Firibgar Kartalar")
            ],
            [
                KeyboardButton(text="📊 Statistika"),
                KeyboardButton(text="👤 Oddiy Rejimga O'tish")
            ]
        ],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Qalqon himoyasida: buyruq yoki xabar yuboring..."
    )


def get_user_reply_keyboard(is_owner: bool = False) -> ReplyKeyboardMarkup:
    """Oddiy fuqaro yoki oddiy rejimdagi Owner uchun pastdagi doimiy tugmalar."""
    keyboard = [
        [
            KeyboardButton(text="🛡️ Havola / Matn Tekshirish"),
            KeyboardButton(text="💳 Karta Tekshirish")
        ],
        [
            KeyboardButton(text="🤖 Bot Tekshirish"),
            KeyboardButton(text="📄 Shartnoma Rentgeni")
        ],
        [
            KeyboardButton(text="🆘 Shoshilinch Yordam"),
            KeyboardButton(text="🧠 Kiber-Viktorina")
        ],
        [
            KeyboardButton(text="👨‍👩‍👧‍👦 Oila Qalqoni"),
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
        input_field_placeholder="Havola, karta raqami yoki xabarni yuboring..."
    )


def get_main_inline_keyboard(user_id: int, is_owner: bool = False, active_mode: str = "user") -> InlineKeyboardMarkup:
    """Xabar ichidagi tezkor WebApp va yordamchi tugmalar."""
    webapp_url = (settings.WEBAPP_URL or "").strip()
    
    first_row = []
    if webapp_url.startswith("https://"):
        first_row.append(
            InlineKeyboardButton(
                text="🛡️ Ilovada ochish (Mini App)",
                web_app=WebAppInfo(url=webapp_url)
            )
        )
    else:
        first_row.append(
            InlineKeyboardButton(
                text="📱 Ilovada ko'rish (Mini App)",
                callback_data="btn_webapp_info"
            )
        )

    buttons = [
        first_row,
        [
            InlineKeyboardButton(text="💳 Karta tekshirish", callback_data="btn_card_info"),
            InlineKeyboardButton(text="🤖 Bot tekshirish", callback_data="btn_bot_info")
        ],
        [
            InlineKeyboardButton(text="📄 Shartnoma auditi", callback_data="btn_contract_info"),
            InlineKeyboardButton(text="👨‍👩‍👧‍👦 Oila Qalqoni", callback_data="btn_family_info")
        ],
        [
            InlineKeyboardButton(text="🆘 Meni aldashdi! (Yordam)", callback_data="btn_sos_info"),
            InlineKeyboardButton(text="🧠 Kiber-Test (Quiz)", callback_data="btn_quiz_info")
        ]
    ]

    if is_owner:
        if active_mode == "owner":
            buttons.append([
                InlineKeyboardButton(text="👑 Admin Panel (/admin)", callback_data="btn_open_admin"),
                InlineKeyboardButton(text="👤 Oddiy rejimga o'tish", callback_data="btn_toggle_role")
            ])
        else:
            buttons.append([
                InlineKeyboardButton(text="👑 Owner rejimiga qaytish", callback_data="btn_toggle_role")
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
                "✅ Pastdagi barcha boshqaruv tugmalari <b>Owner holatiga o'tdi</b>:\n"
                "• 👑 <b>Admin Panel</b> va 👥 <b>Adminlar Boshqaruvi</b> qo'shildi;\n"
                "• 📢 <b>Hammaga Xabar</b> va 🚫 <b>Firibgar Kartalar</b> yoqildi;\n"
                "• Siz endi bemalol yangi adminlar tayinlashingiz mumkin!"
            )
            reply_kb = get_owner_reply_keyboard()
        else:
            text = (
                "👤 <b>Oddiy Foydalanuvchi Rejimi Faollashtirildi!</b>\n\n"
                "✅ Pastdagi tugmalar <b>oddiy fuqaro ko'rinishiga</b> o'tdi.\n"
                "Siz hozir botni fuqaro ko'zi bilan sinab ko'rishingiz mumkin.\n\n"
                "👑 <i>Owner rejimiga qaytish uchun: pastdagi '👑 Owner Rejimiga O'tish' tugmasini bosing yoki /switch_role yozing.</i>"
            )
            reply_kb = get_user_reply_keyboard(is_owner=True)

        await message.answer(text, reply_markup=reply_kb, parse_mode=ParseMode.HTML)
        await message.answer(
            "🎛️ <b>Rejim holati muvaffaqiyatli o'zgartirildi:</b>",
            reply_markup=get_main_inline_keyboard(user_id, is_owner=True, active_mode=new_mode),
            parse_mode=ParseMode.HTML
        )


# =========================================================================
# 4. ADMIN BOSHQARUVI VA AMALLARI
# =========================================================================

async def render_admins_management(message: types.Message, user_id: int):
    """Adminlar ro'yxati va interaktiv boshqaruv tugmalarini ko'rsatish."""
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(or_(User.role == "admin", User.telegram_id == settings.OWNER_TELEGRAM_ID))
        res = await session.execute(stmt)
        admins = res.scalars().all()

        text = (
            "👥 <b>SHIELDGUARD ADMINLAR BOSHQARUVI:</b>\n"
            "════════════════════════\n\n"
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
                InlineKeyboardButton(text="🔄 Ro'yxatni Yangilash", callback_data="btn_refresh_admins")
            ]
        ]
        await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows), parse_mode=ParseMode.HTML)


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
    # Target foydalanuvchiga xabar jo'natish
    await send_telegram_message(
        target_id,
        "🎉 <b>Tabriklaymiz!</b> Siz ShieldGuard AI tizimida <b>Admin</b> etib tayinlandingiz!\n\n"
        "Admin boshqaruv markazini ko'rish uchun /admin buyrug'ini yozing."
    )


async def resolve_and_promote_admin(owner_id: int, raw_input: str, message: types.Message, forward_user: Optional[types.User] = None):
    """Foydalanuvchi kiritmasi yoki Forward qilingan xabardan yangi adminni aniqlash va tayinlash."""
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
                    f"<b>Sababi:</b> Ushbu foydalanuvchi hali botimizga /start bosmagan bo'lishi mumkin. "
                    f"Telegram xavfsizlik protokoli bo'yicha botda ro'yxatdan o'tmagan kishining ID raqamini faqat username orqali aniqlab bo'lmaydi.\n\n"
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


async def render_scam_cards_management(message: types.Message, user_id: int):
    """Firibgar kartalar ro'yxatini ko'rsatish."""
    async with AsyncSessionLocal() as session:
        stmt = select(CardBlacklist).order_by(CardBlacklist.created_at.desc()).limit(8)
        res = await session.execute(stmt)
        cards = res.scalars().all()

        text = "🚫 <b>FIRIBGAR KARTALAR QORA RO'YXATI:</b>\n════════════════════════\n\n"
        if cards:
            for c in cards:
                text += f"💳 <code>{c.card_number}</code> | {c.bank_name or 'Bank'}\n⚠️ <i>{c.reason}</i> (Shikoyat: {c.report_count})\n\n"
        else:
            text += "<i>Hozircha qora ro'yxatda kartalar mavjud emas.</i>\n\n"

        text += "Qora ro'yxatga yangi karta qo'shish uchun quyidagi tugmani bosing yoki <code>/addcard &lt;karta&gt; &lt;sabab&gt;</code> yozing."

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="➕ Qora Ro'yxatga Karta Qo'shish", callback_data="btn_prompt_add_card")],
                [InlineKeyboardButton(text="🔄 Yangilash", callback_data="btn_refresh_cards")]
            ]
        )
        await message.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)


async def render_system_stats(message: types.Message, user_id: int):
    """Tizimning jonli statistikasini chiqarish."""
    async with AsyncSessionLocal() as session:
        total_users = (await session.execute(select(func.count(User.id)))).scalar() or 0
        total_scans = (await session.execute(select(func.count(ScanHistory.id)))).scalar() or 0
        blocked_threats = (await session.execute(select(func.count(ScanHistory.id)).where(ScanHistory.risk_score >= 70))).scalar() or 0
        total_cards_scam = (await session.execute(select(func.count(CardBlacklist.id)))).scalar() or 0
        total_admins = (await session.execute(select(func.count(User.id)).where(User.role == "admin"))).scalar() or 0

        text = (
            f"📊 <b>SHIELDGUARD AI — JONLI STATISTIKA</b>\n"
            f"════════════════════════\n\n"
            f"👥 <b>Foydalanuvchilar:</b> {total_users} nafar\n"
            f"🛡️ <b>Tayinlangan adminlar:</b> {total_admins} nafar\n"
            f"🔍 <b>Amalga oshirilgan tahlillar:</b> {total_scans} ta\n"
            f"🚨 <b>Fosh qilingan firibgarliklar:</b> {blocked_threats} ta\n"
            f"🚫 <b>Qora ro'yxatdagi kartalar:</b> {total_cards_scam} ta\n\n"
            f"🟢 <b>Tizim holati:</b> Normal (Faol himoya rejimida)"
        )
        await message.answer(text, parse_mode=ParseMode.HTML)


# =========================================================================
# 5. ASOSIY BUYRUQLAR (/start, /switch_role, /admin, /addadmin...)
# =========================================================================

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    """Start buyrug'i: Pastdagi tugmalar va boshqaruv panelini ochish."""
    user = message.from_user
    db_user = None
    if user:
        db_user = await get_or_create_user(user.id, user.username, user.full_name)

    is_owner = (user.id == settings.OWNER_TELEGRAM_ID if user else False)
    active_mode = db_user.active_mode if db_user else ("owner" if is_owner else "user")

    reply_kb = get_owner_reply_keyboard() if (is_owner and active_mode == "owner") else get_user_reply_keyboard(is_owner=is_owner)

    if is_owner and active_mode == "owner":
        owner_welcome = (
            f"👑 <b>Assalomu alaykum, Hurmatli Bosh Administrator (Owner) @{settings.OWNER_USERNAME}!</b>\n\n"
            f"🛡️ <b>ShieldGuard Pro AI</b> boshqaruv tizimi to'liq ixtiyoringizda.\n\n"
            f"🎯 <b>Pastda siz uchun maxsus boshqaruv tugmalari joylashtirildi:</b>\n"
            f"• 👑 <b>Admin Panel</b> — Barcha statistika va tizim holati\n"
            f"• 👥 <b>Adminlar Boshqaruvi</b> — Yangi admin qo'shish va o'chirish\n"
            f"• 📢 <b>Hammaga Xabar</b> — Barcha a'zolarga bildirishnoma tarqatish\n"
            f"• 🚫 <b>Firibgar Kartalar</b> — Qora ro'yxatni boshqarish\n"
            f"• 👤 <b>Oddiy Rejimga O'tish</b> — Botni fuqaro sifatida sinash\n\n"
            f"👇 <i>Pastdagi tugmalar yoki quyidagi tezkor menyudan foydalaning:</i>"
        )
        await message.answer(
            text=owner_welcome,
            reply_markup=reply_kb,
            parse_mode=ParseMode.HTML
        )
        await message.answer(
            "⚡ <b>Tezkor amallar (Mini App & Havolalar):</b>",
            reply_markup=get_main_inline_keyboard(user.id, is_owner=True, active_mode="owner"),
            parse_mode=ParseMode.HTML
        )
        return

    welcome_text = (
        f"👋 <b>Assalomu alaykum, {user.first_name if user else 'qadrdon yurtdosh'}!</b>\n\n"
        f"🛡️ <b>ShieldGuard AI</b> — siz va yaqinlaringizni internetdagi fishing, "
        f"soxta bank kartalari, zararli APK-viruslar va og'ir shartnoma tuzoqlaridan "
        f"himoya qiluvchi keng qamrovli kiber-qalqondir.\n\n"
        f"⚡ <b>Menga quyidagilarni yuborishingiz mumkin:</b>\n"
        f"• Shubhali havola yoki matn (fishing skaneri);\n"
        f"• 16 talik bank karta raqami (masalan: <code>8600...</code> yoki <code>9860...</code>);\n"
        f"• Shubhali Telegram bot (masalan: <code>@click_bonus_bot</code>);\n"
        f"• Telegramdan kelgan fayl (masalan: <code>To'y taklifnomasi.apk</code>);\n"
        f"• Kredit yoki ijara shartnomasi (PDF yoki fotosurat).\n\n"
        f"👇 <i>Pastdagi tugmalardan kerakli xizmatni tanlang:</i>"
    )

    if is_owner and active_mode == "user":
        welcome_text += "\n\n<i>[💡 Siz hozir oddiy foydalanuvchi rejimidasiz. Owner rejimiga qaytish uchun pastdagi '👑 Owner Rejimiga O'tish' tugmasini bosing yoki /switch_role yozing]</i>"

    await message.answer(
        text=welcome_text,
        reply_markup=reply_kb,
        parse_mode=ParseMode.HTML
    )
    await message.answer(
        "⚡ <b>Qo'shimcha vositalar (Mini App):</b>",
        reply_markup=get_main_inline_keyboard(user.id if user else 0, is_owner=is_owner, active_mode=active_mode),
        parse_mode=ParseMode.HTML
    )


@dp.message(Command("switch_role"))
async def cmd_switch_role(message: types.Message):
    """Owner rejimini almashtirish buyrug'i."""
    user = message.from_user
    await switch_owner_role(user.id, message)


@dp.callback_query(F.data == "btn_toggle_role")
async def cb_toggle_role(callback: types.CallbackQuery):
    """Inline tugma orqali rejimni almashtirish."""
    user = callback.from_user
    if user.id != settings.OWNER_TELEGRAM_ID:
        await callback.answer("Faqat Super Owner uchun!", show_alert=True)
        return
    await callback.answer()
    await switch_owner_role(user.id, callback.message)


@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    """Admin Boshqaruv Markazi."""
    user = message.from_user
    is_owner = (user.id == settings.OWNER_TELEGRAM_ID)

    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.telegram_id == user.id)
        res = await session.execute(stmt)
        db_user = res.scalar_one_or_none()

        is_admin = is_owner or (db_user and db_user.role == "admin" and not db_user.is_banned)
        if not is_admin:
            await message.answer("❌ Bu bo'limga faqat ma'murlar kira oladi.")
            return

        total_users = (await session.execute(select(func.count(User.id)))).scalar() or 0
        total_scans = (await session.execute(select(func.count(ScanHistory.id)))).scalar() or 0
        blocked_threats = (await session.execute(select(func.count(ScanHistory.id)).where(ScanHistory.risk_score >= 70))).scalar() or 0
        total_cards_scam = (await session.execute(select(func.count(CardBlacklist.id)))).scalar() or 0

        admin_text = (
            f"👑 <b>SHIELDGUARD BOSHQARUV MARKAZI</b>\n"
            f"════════════════════════\n"
            f"👤 <b>Ma'mur:</b> {user.first_name} ({'👑 SUPER OWNER' if is_owner else '🛡️ ADMIN'})\n\n"
            f"📊 <b>Jonli statistika:</b>\n"
            f"• Jami a'zolar: <b>{total_users}</b> ta\n"
            f"• Jami tekshiruvlar: <b>{total_scans}</b> ta\n"
            f"• Fosh qilingan tahdidlar: <b>{blocked_threats}</b> ta\n"
            f"• Qora ro'yxatdagi kartalar: <b>{total_cards_scam}</b> ta\n\n"
            f"🛠️ <b>Mavjud buyruqlar:</b>\n"
            f"• <code>/broadcast &lt;xabar&gt;</code> — Barcha foydalanuvchilarga xabar tarqatish\n"
            f"• <code>/admins</code> — Hozirgi barcha adminlar ro'yxati\n"
            f"• <code>/card &lt;raqam&gt;</code> — Karta raqamini tahlil qilish\n"
            f"• <code>/addcard &lt;karta&gt; &lt;sabab&gt;</code> — Kartani qora ro'yxatga kiritish\n"
            f"• <code>/ban &lt;id&gt; &lt;sabab&gt;</code> — Foydalanuvchini bloklash\n"
            f"• <code>/unban &lt;id&gt;</code> — Blokdan chiqarish\n"
        )

        if is_owner:
            admin_text += (
                f"\n💎 <b>Faqat Owner uchun buyruqlar:</b>\n"
                f"• <code>/addadmin &lt;telegram_id yoki @username&gt;</code> — Yangi admin tayinlash\n"
                f"• <code>/deladmin &lt;telegram_id&gt;</code> — Adminni o'chirish\n"
                f"• <code>/switch_role</code> — Oddiy foydalanuvchi rejimiga o'tish\n"
            )

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="👥 Adminlar Boshqaruvi", callback_data="btn_list_admins"),
                    InlineKeyboardButton(text="🚫 Firibgar Kartalar", callback_data="btn_list_cards")
                ],
                [
                    InlineKeyboardButton(text="📢 Yangi E'lon Tarqatish", callback_data="btn_prompt_broadcast"),
                    InlineKeyboardButton(text="🔄 Rejimni Almashtirish", callback_data="btn_toggle_role")
                ]
            ]
        )

        reply_kb = get_owner_reply_keyboard() if is_owner else None
        await message.answer(admin_text, reply_markup=reply_kb, parse_mode=ParseMode.HTML)
        await message.answer("👇 <i>Kerakli tezkor harakatni tanlang:</i>", reply_markup=kb, parse_mode=ParseMode.HTML)


@dp.callback_query(F.data == "btn_open_admin")
async def cb_open_admin(callback: types.CallbackQuery):
    await callback.answer()
    await cmd_admin(callback.message)


# =========================================================================
# 6. ADMIN QO'SHISH VA O'CHIRISH (INTERAKTIV & BUYRUQ)
# =========================================================================

@dp.message(Command("addadmin"))
async def cmd_add_admin(message: types.Message):
    """Yangi admin tayinlash buyrug'i."""
    user = message.from_user
    if user.id != settings.OWNER_TELEGRAM_ID:
        await message.answer("❌ Faqat loyiha egasi (@fayzbek1331) yangi admin tayinlay oladi.")
        return

    # 1. Agar birovning xabariga Reply qilib /addadmin yozilgan bo'lsa
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
        # Argument kiritilmagan bo'lsa, interaktiv holatga o'tkazish
        user_states[user.id] = {"action": "waiting_for_admin"}
        await message.answer(
            "➕ <b>YANGI ADMIN TAYINLASH</b>\n\n"
            "Iltimos, admin qilmoqchi bo'lgan foydalanuvchini yuboring:\n\n"
            "1️⃣ <b>Telegram ID raqami:</b> (masalan: <code>123456789</code>)\n"
            "2️⃣ <b>@username:</b> (masalan: <code>@sherzod_uz</code> yoki <code>sherzod_uz</code>)\n"
            "3️⃣ <b>Xabarini forward qilish:</b> O'sha shaxsning biron bir xabarini menga <b>Forward</b> (uzatish) qiling!\n\n"
            "❌ <i>Bekor qilish uchun: /cancel</i>",
            parse_mode=ParseMode.HTML
        )
        return

    arg = parts[1].strip()
    await resolve_and_promote_admin(owner_id=user.id, raw_input=arg, message=message)


@dp.callback_query(F.data == "btn_prompt_add_admin")
async def cb_prompt_add_admin(callback: types.CallbackQuery):
    """Tugma orqali yangi admin tayinlashni boshlash."""
    user = callback.from_user
    if user.id != settings.OWNER_TELEGRAM_ID:
        await callback.answer("Faqat Super Owner uchun!", show_alert=True)
        return
    await callback.answer()
    user_states[user.id] = {"action": "waiting_for_admin"}
    await callback.message.answer(
        "➕ <b>YANGI ADMIN TAYINLASH</b>\n\n"
        "Iltimos, yangi admin qilmoqchi bo'lgan foydalanuvchini quyidagi 3 usuldan biri bilan yuboring:\n\n"
        "1️⃣ <b>Telegram ID raqami:</b> (masalan: <code>123456789</code>)\n"
        "2️⃣ <b>@username:</b> (masalan: <code>@sherzod_uz</code> yoki <code>sherzod_uz</code>)\n"
        "3️⃣ <b>Xabarini forward qilish:</b> O'sha shaxsning biron bir xabarini menga <b>Forward</b> qiling!\n\n"
        "❌ <i>Bekor qilish uchun: /cancel</i>",
        parse_mode=ParseMode.HTML
    )


@dp.message(Command("deladmin"))
async def cmd_del_admin(message: types.Message):
    """Adminni o'chirish buyrug'i."""
    user = message.from_user
    if user.id != settings.OWNER_TELEGRAM_ID:
        await message.answer("❌ Faqat loyiha egasi (@fayzbek1331) adminni o'chira oladi.")
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        # Argument kiritilmagan bo'lsa, barcha adminlarni o'chirish tugmalari bilan ko'rsatish
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

    if not target_id:
        await message.answer("❌ Foydalanuvchi topilmadi. Raqamli Telegram ID yoki to'g'ri @usernameni kiriting.")
        return

    if target_id == settings.OWNER_TELEGRAM_ID:
        await message.answer("❌ Super Ownerni o'chirib bo'lmaydi!")
        return

    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.telegram_id == target_id)
        res = await session.execute(stmt)
        target = res.scalar_one_or_none()

        if target and target.role == "admin":
            target.role = "user"
            audit = AdminAuditLog(admin_telegram_id=user.id, action="remove_admin", target=str(target_id), details="Owner tomonidan olib tashlandi")
            session.add(audit)
            await session.commit()
            await message.answer(f"✅ Foydalanuvchining (ID: <code>{target_id}</code>) adminlik vakolati bekor qilindi.", parse_mode=ParseMode.HTML)
            await send_telegram_message(target_id, "ℹ️ Sizning ShieldGuard tizimidagi adminlik vakolatingiz to'xtatildi.")
        else:
            await message.answer("Ushbu foydalanuvchi admin emas yoki bazada topilmadi.")


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


@dp.callback_query(F.data == "btn_prompt_del_admin")
async def cb_prompt_del_admin(callback: types.CallbackQuery):
    """Tugma orqali admin o'chirish menyusini ochish."""
    user = callback.from_user
    if user.id != settings.OWNER_TELEGRAM_ID:
        await callback.answer("Faqat Super Owner uchun!", show_alert=True)
        return
    await callback.answer()
    await show_delete_admin_picker(callback.message, user.id)


@dp.callback_query(F.data.startswith("deladmin_id:"))
async def cb_delete_admin_by_id(callback: types.CallbackQuery):
    """Bitta bosish orqali adminni o'chirish."""
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
            audit = AdminAuditLog(admin_telegram_id=user.id, action="remove_admin", target=str(target_id), details="Owner tomonidan tugma orqali olib tashlandi")
            session.add(audit)
            await session.commit()
            await callback.answer("Adminlik vakolati bekor qilindi!", show_alert=True)
            await callback.message.edit_text(
                f"✅ Foydalanuvchining (ID: <code>{target_id}</code>) adminlik huquqi bekor qilindi.",
                parse_mode=ParseMode.HTML
            )
            await send_telegram_message(target_id, "ℹ️ Sizning ShieldGuard AI tizimidagi adminlik vakolatingiz to'xtatildi.")
        else:
            await callback.answer("Admin topilmadi yoki allaqachon o'chirilgan.", show_alert=True)


@dp.message(Command("admins"))
async def cmd_list_admins(message: types.Message):
    """Barcha adminlar ro'yxatini ko'rsatish."""
    await render_admins_management(message, message.from_user.id)


@dp.callback_query(F.data.in_(["btn_list_admins", "btn_refresh_admins"]))
async def cb_list_admins(callback: types.CallbackQuery):
    await callback.answer()
    await render_admins_management(callback.message, callback.from_user.id)


# =========================================================================
# 7. BROADCAST & QORA RO'YXAT (KARTALAR)
# =========================================================================

@dp.message(Command("broadcast"))
async def cmd_broadcast(message: types.Message):
    """Barcha a'zolarga xabar tarqatish."""
    user = message.from_user
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.telegram_id == user.id)
        res = await session.execute(stmt)
        db_user = res.scalar_one_or_none()

        if user.id != settings.OWNER_TELEGRAM_ID and (not db_user or db_user.role != "admin"):
            await message.answer("❌ Faqat ma'murlar umumiy xabar tarqata oladi.")
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


@dp.callback_query(F.data == "btn_list_cards")
async def cb_list_cards(callback: types.CallbackQuery):
    await callback.answer()
    await render_scam_cards_management(callback.message, callback.from_user.id)


@dp.callback_query(F.data == "btn_prompt_add_card")
async def cb_prompt_add_card(callback: types.CallbackQuery):
    user = callback.from_user
    await callback.answer()
    user_states[user.id] = {"action": "waiting_for_scam_card"}
    await callback.message.answer(
        "🚫 <b>FIRIBGAR KARTANI QORA RO'YXATGA QO'SHISH</b>\n\n"
        "Quyidagi formatda yuboring:\n"
        "<code>&lt;16 talik karta raqami&gt; &lt;firibgarlik sababi&gt;</code>\n\n"
        "Masalan:\n<code>8600123456789012 Telegramda soxta ovoz berish orqali pul talab qildi</code>\n\n"
        "❌ <i>Bekor qilish uchun: /cancel</i>",
        parse_mode=ParseMode.HTML
    )


@dp.message(Command("addcard"))
async def cmd_add_card(message: types.Message):
    user = message.from_user
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("Foydalanish: <code>/addcard 8600123456789012 Sababi...</code>", parse_mode=ParseMode.HTML)
        return
    raw_card = parts[1].strip()
    reason = parts[2].strip()
    clean_num = "".join(filter(str.isdigit, raw_card))
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
                reason=reason,
                reported_by=user.id
            )
            session.add(c)
        else:
            c.report_count += 1
            c.reason += f" | {reason}"
        await session.commit()
    await message.answer(f"✅ Karta <code>{clean_num}</code> muvaffaqiyatli qora ro'yxatga kiritildi!", parse_mode=ParseMode.HTML)


# =========================================================================
# 8. FOYDALANUVCHINI BLOKLASH (/ban & /unban)
# =========================================================================

@dp.message(Command("ban"))
async def cmd_ban_user(message: types.Message):
    user = message.from_user
    if user.id != settings.OWNER_TELEGRAM_ID:
        await message.answer("❌ Faqat ma'murlar foydalanuvchini bloklay oladi.")
        return

    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("Foydalanish: <code>/ban &lt;telegram_id&gt;</code>", parse_mode=ParseMode.HTML)
        return

    target_id = int(parts[1])
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.telegram_id == target_id)
        res = await session.execute(stmt)
        target = res.scalar_one_or_none()
        if target:
            target.is_banned = True
            await session.commit()
            await message.answer(f"🚫 Foydalanuvchi (ID: <code>{target_id}</code>) botdan bloklandi.")
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
            await session.commit()
            await message.answer(f"✅ Foydalanuvchi (ID: <code>{target_id}</code>) blokdan chiqarildi.")


# =========================================================================
# 9. FOYDALANUVCHI VOSITALARI (/card, /botcheck, /sos, /quiz)
# =========================================================================

@dp.message(Command("card"))
async def cmd_check_card(message: types.Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Foydalanish: <code>/card 8600123456789012</code>\n16 talik bank karta raqamini kiriting.", parse_mode=ParseMode.HTML)
        return

    card_raw = parts[1].strip()
    analysis = analyze_card_number(card_raw)
    clean_card = "".join(filter(str.isdigit, card_raw))

    async with AsyncSessionLocal() as session:
        stmt = select(CardBlacklist).where(CardBlacklist.card_number == clean_card)
        res = await session.execute(stmt)
        scam_entry = res.scalar_one_or_none()

    if scam_entry:
        card_report = (
            f"🚨 <b>DIQQAT! KRITIK FIRIBGAR KARTA ANIQLANDI!</b>\n\n"
            f"💳 <b>Karta:</b> <code>{clean_card}</code>\n"
            f"🏦 <b>Bank:</b> {analysis.get('bank_name')}\n"
            f"📊 <b>Xavf darajasi:</b> 🔴 <b>100%</b>\n\n"
            f"⚠️ <b>Qora ro'yxat ma'lumoti:</b>\n"
            f"{scam_entry.reason}\n"
            f"Shikoyatlar soni: <b>{scam_entry.report_count}</b> ta\n\n"
            f"⛔ <b>Ushbu kartaga aslo pul o'tkazmang!</b>"
        )
    else:
        risk = analysis.get("risk_score", 0)
        icon = "🔴" if risk >= 70 else ("🟡" if risk >= 40 else "🟢")
        card_report = (
            f"💳 <b>BANK KARTASI TAHLILI:</b>\n\n"
            f"🔢 <b>Karta:</b> <code>{analysis.get('card_number_masked', clean_card)}</code>\n"
            f"🌐 <b>To'lov tizimi:</b> {analysis.get('payment_system')}\n"
            f"🏦 <b>Emitent Bank:</b> {analysis.get('bank_name')}\n"
            f"📑 <b>Turi:</b> {analysis.get('card_type')}\n"
            f"📊 <b>Xavf ko'rsatkichi:</b> {icon} <b>{int(risk)}%</b>\n\n"
            f"💬 <b>Xulosa:</b> {analysis.get('summary_uz')}\n"
        )
        if analysis.get("warnings"):
            card_report += "\n🚩 <b>Ogohlantirishlar:</b>\n" + "\n".join(f"• {w}" for w in analysis["warnings"])

    await message.answer(card_report, parse_mode=ParseMode.HTML)


@dp.message(Command("botcheck"))
async def cmd_botcheck(message: types.Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Foydalanish: <code>/botcheck @shubhali_bot</code>", parse_mode=ParseMode.HTML)
        return

    bot_user = parts[1].strip()
    res = analyze_telegram_bot_or_username(bot_user)
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

    await message.answer(report, parse_mode=ParseMode.HTML)


@dp.message(Command("sos"))
async def cmd_sos(message: types.Message):
    sos_text = (
        "🆘 <b>FAVQULODDA XAVFSIZLIK VA YORDAM REJASI:</b>\n\n"
        "Agar siz firibgarlarga karta ma'lumotlaringizni yoki SMS-kodni berib qo'ygan bo'lsangiz:\n\n"
        "1️⃣ <b>ZUDLIK BILAN KARTANI BLOKLANGLAR:</b>\n"
        "Bank ilovangizga (Click, Payme, Uzum) kiring va kartangiz ustiga bosib 'Bloklash'ni tanlang.\n\n"
        "2️⃣ <b>BANK KOLL-MARKAZIGA QO'NG'IROQ QILING:</b>\n"
        "• Click: <b>71 202-01-01</b>\n"
        "• Payme: <b>71 200-02-02</b>\n"
        "• Uzum Bank: <b>78 777-07-07</b>\n"
        "• Xalq Banki: <b>1106</b> | Agrobank: <b>1216</b>\n"
        "• Kapitalbank: <b>71 200-15-15</b> | Ipak Yo'li: <b>1296</b>\n"
        "• Anorbank: <b>1290</b> | TBC Bank: <b>1150</b>\n\n"
        "3️⃣ <b>IIV KIBERXAVFSIZLIK MARKAZI:</b>\n"
        "📞 Ishonch telefoni: <b>1102</b> yoki <b>102</b>\n"
        "Barcha yozishmalar, cheklar va telefon raqamlarni skrinshot qilib saqlang!"
    )
    await message.answer(sos_text, parse_mode=ParseMode.HTML)


@dp.message(Command("quiz"))
async def cmd_quiz(message: types.Message):
    quiz_welcome = (
        "🧠 <b>SHIELDGUARD KIBER-SAVODXONLIK TESTI:</b>\n\n"
        "Siz o'zingizni internetdagi firibgarlik va kiber-tuzoqlardan himoya qila olasizmi?\n\n"
        "Ushbu interaktiv testda real hayotdagi 5 ta eng xavfli firibgarlik sxemasi keltirilgan. "
        "Sinovdan o'ting va 'Kiber-Qalqon Sertifikati'ga ega bo'ling!\n\n"
        "👇 <i>Testni boshlash uchun quyidagi tugmani bosing:</i>"
    )
    await message.answer(
        quiz_welcome,
        reply_markup=get_main_inline_keyboard(message.from_user.id),
        parse_mode=ParseMode.HTML
    )


# =========================================================================
# 10. CALLBACK TUGMALARI
# =========================================================================

@dp.callback_query(F.data == "btn_card_info")
async def cb_card_info(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "💳 <b>Bank kartasini tekshirish:</b>\n\n"
        "Sizga pul o'tkazishni so'rashgan 16 talik karta raqamini botga yuboring (masalan: <code>8600123456789012</code>) yoki <code>/card &lt;raqam&gt;</code> buyrug'idan foydalaning.\n\n"
        "Biz kartaning emitent banki va firibgarlar qora ro'yxatida bor-yo'qligini tekshiramiz.",
        parse_mode=ParseMode.HTML
    )


@dp.callback_query(F.data == "btn_bot_info")
async def cb_bot_info(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "🤖 <b>Telegram botni tekshirish:</b>\n\n"
        "Shubhali bot username'ini yuboring (masalan: <code>@click_yutuq_bot</code>) yoki <code>/botcheck &lt;@username&gt;</code> buyrug'ini bering.\n\n"
        "Botning rasmiyligi va xavflilik darajasini fosh qilamiz.",
        parse_mode=ParseMode.HTML
    )


@dp.callback_query(F.data == "btn_sos_info")
async def cb_sos_info(callback: types.CallbackQuery):
    await callback.answer()
    await cmd_sos(callback.message)


@dp.callback_query(F.data == "btn_quiz_info")
async def cb_quiz_info(callback: types.CallbackQuery):
    await callback.answer()
    await cmd_quiz(callback.message)


@dp.callback_query(F.data == "btn_contract_info")
async def cb_contract_info(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "📄 <b>Shartnoma Rentgeni:</b>\n\n"
        "Kredit, mikroqarz, muddatli to'lov (nasiya), ijara yoki mehnat shartnomasining "
        "<b>PDF</b> faylini yoki sahifalar fotosuratini menga yuboring!\n\n"
        "Sun'iy intellekt barcha asossiz moddalarni tahlil qilib beradi.",
        parse_mode=ParseMode.HTML
    )


@dp.callback_query(F.data == "btn_family_info")
async def cb_family_info(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "👨‍👩‍👧‍👦 <b>Oila Qalqoni xizmati:</b>\n\n"
        f"Sizning Telegram ID raqamingiz: <code>{callback.from_user.id}</code>\n\n"
        "Ota-onangiz yoki yaqinlaringiz botning Mini App bo'limiga kirib, sizning ID raqamingizni "
        "<b>'Himoyachi (Vasiy)'</b> sifatida kiritishsa, ular xavfli manzilga duch kelgan zahoti "
        "sizga tezkor signal keladi!",
        parse_mode=ParseMode.HTML
    )


@dp.callback_query(F.data == "btn_webapp_info")
async def cb_webapp_info(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "📱 <b>ShieldGuard Mini App:</b>\n\n"
        "Interaktiv kiber-himoya interfeysini ko'rish uchun:\n"
        "• Kompyuteringizda: <code>http://localhost:8000/webapp</code>\n"
        "• Vercel yoki HTTPS domeniga yuklanganda Telegram ichida to'g'ridan-to'g'ri ochiladi!",
        parse_mode=ParseMode.HTML
    )


# =========================================================================
# 11. HUJJAT VA FAYLLARNI QABUL QILISH (APK, PDF)
# =========================================================================

@dp.message(F.document)
async def handle_document(message: types.Message):
    doc = message.document
    filename = doc.file_name or "noma'lum_fayl"
    lower_name = filename.lower()
    user_id = message.from_user.id

    wait_msg = await message.answer("⏳ <i>Fayl qabul qilindi. ShieldGuard xavfsizlik dvigateli tekshirmoqda...</i>", parse_mode=ParseMode.HTML)

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

            async with AsyncSessionLocal() as session:
                hist = ScanHistory(
                    user_telegram_id=user_id,
                    scan_type="file",
                    target_name=filename,
                    risk_score=float(risk),
                    verdict=res["verdict"],
                    summary_uz=res["summary_uz"],
                    details_json=json.dumps(res, ensure_ascii=False)
                )
                session.add(hist)
                await session.commit()

                if risk >= 70:
                    await notify_family_guardians(session, user_id, filename, risk, res["summary_uz"])

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
                report += "\n⚠️ <b>Xavfli yoki noqonuniy bandlar:</b>\n"
                for clause in res["dangerous_clauses"][:3]:
                    report += f"• <b>{clause.get('clause_no', 'Band')}:</b> {clause.get('explanation_uz', '')}\n"

            async with AsyncSessionLocal() as session:
                hist = ScanHistory(
                    user_telegram_id=user_id,
                    scan_type="contract",
                    target_name=filename,
                    risk_score=float(risk),
                    verdict="safe" if score >= 70 else "dangerous",
                    summary_uz=res.get("summary_uz", ""),
                    details_json=json.dumps(res, ensure_ascii=False)
                )
                session.add(hist)
                await session.commit()

            await wait_msg.edit_text(report, reply_markup=get_main_inline_keyboard(user_id), parse_mode=ParseMode.HTML)
            return

        else:
            await wait_msg.edit_text("ℹ️ Ushbu turdagi fayllar hozircha qo'llab-quvvatlanmaydi. Faqat .apk, .pdf yoki shartnoma rasmlarini yuborishingiz mumkin.")

    except Exception as e:
        logger.error(f"Fayl tahlilida xatolik: {e}")
        await wait_msg.edit_text("❌ Faylni tekshirish jarayonida texnik nosozlik yuz berdi.")


# =========================================================================
# 12. FOTORASMLARNI QABUL QILISH (SHARTNOMA RASMLARI)
# =========================================================================

@dp.message(F.photo)
async def handle_photo(message: types.Message):
    user_id = message.from_user.id
    photo = message.photo[-1]
    wait_msg = await message.answer("🔍 <i>Shartnoma fotosurati o'qilmoqda va AI auditdan o'tkazilmoqda...</i>", parse_mode=ParseMode.HTML)

    try:
        file_io = io.BytesIO()
        await bot.download(photo, destination=file_io)
        img_bytes = file_io.getvalue()

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

        async with AsyncSessionLocal() as session:
            hist = ScanHistory(
                user_telegram_id=user_id,
                scan_type="contract",
                target_name="Shartnoma fotosurati",
                risk_score=float(risk),
                verdict="safe" if score >= 70 else "dangerous",
                summary_uz=res.get("summary_uz", ""),
                details_json=json.dumps(res, ensure_ascii=False)
            )
            session.add(hist)
            await session.commit()

        await wait_msg.edit_text(report, reply_markup=get_main_inline_keyboard(user_id), parse_mode=ParseMode.HTML)

    except Exception as e:
        logger.error(f"Rasm tahlilida xatolik: {e}")
        await wait_msg.edit_text("❌ Fotosuratni tahlil qilishda xatolik yuz berdi. Iltimos, aniqroq rasm yuboring.")


# =========================================================================
# 13. MATNLI XABARLAR VA PASTKI TUGMALAR ISHLOVCHISI
# =========================================================================

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

    is_owner = (user.id == settings.OWNER_TELEGRAM_ID if user else False)
    active_mode = db_user.active_mode if db_user else ("owner" if is_owner else "user")

    # 1. Bekor qilish buyrug'i (/cancel)
    if text.lower() in ("/cancel", "cancel", "bekor qilish"):
        if user_id in user_states:
            user_states.pop(user_id, None)
            reply_kb = get_owner_reply_keyboard() if (is_owner and active_mode == "owner") else get_user_reply_keyboard(is_owner=is_owner)
            await message.answer("✅ Amal bekor qilindi.", reply_markup=reply_kb)
            return

    # 2. Reply Keyboard (Pastdagi tugmalar) bosilganda:
    if text == "👑 Owner Rejimiga O'tish":
        await switch_owner_role(user_id, message, to_mode="owner")
        return
    elif text == "👤 Oddiy Rejimga O'tish":
        await switch_owner_role(user_id, message, to_mode="user")
        return
    elif text == "👑 Admin Panel":
        await cmd_admin(message)
        return
    elif text == "👥 Adminlar Boshqaruvi":
        await render_admins_management(message, user_id)
        return
    elif text == "📢 Hammaga Xabar":
        user_states[user_id] = {"action": "waiting_for_broadcast"}
        await message.answer(
            "📢 <b>Barcha foydalanuvchilarga xabar tarqatish:</b>\n\n"
            "Iltimos, e'loningiz matnini shu yerga yozib yuboring (u barcha bot a'zolariga yetkaziladi).\n\n"
            "❌ <i>Bekor qilish uchun: /cancel</i>",
            parse_mode=ParseMode.HTML
        )
        return
    elif text == "🚫 Firibgar Kartalar":
        await render_scam_cards_management(message, user_id)
        return
    elif text == "📊 Statistika":
        await render_system_stats(message, user_id)
        return
    elif text == "🛡️ Havola / Matn Tekshirish":
        await message.answer(
            "🔍 <b>Havola yoki matn tekshirish:</b>\n\n"
            "Shubhali deb gumon qilingan havola (masalan: <code>https://c1ick-uz.com</code>) "
            "yoki sizga kelgan xabar matnini shu yerga yuboring. ShieldGuard uni phishing, "
            "soxta aksiya va kartani o'g'irlash shakllariga qarshi tekshiradi.",
            parse_mode=ParseMode.HTML
        )
        return
    elif text == "💳 Karta Tekshirish":
        await message.answer(
            "💳 <b>Bank kartasini tekshirish:</b>\n\n"
            "Shubhali 16 talik bank karta raqamini yuboring (masalan: <code>8600 1234 5678 9012</code>).\n\n"
            "Biz kartaning emitent banki, haqiqiyligi va firibgarlar qora ro'yxatida bor-yo'qligini aniqlaymiz.",
            parse_mode=ParseMode.HTML
        )
        return
    elif text == "🤖 Bot Tekshirish":
        await message.answer(
            "🤖 <b>Telegram botni tekshirish:</b>\n\n"
            "Shubhali bot usernamesini yuboring (masalan: <code>@click_bonus_bot</code>).\n\n"
            "Biz uni rasmiy kanallar bilan solishtirib, qalloblik darajasini baholaymiz.",
            parse_mode=ParseMode.HTML
        )
        return
    elif text == "📄 Shartnoma Rentgeni":
        await message.answer(
            "📄 <b>Shartnoma Rentgeni:</b>\n\n"
            "Kredit, mikroqarz, muddatli to'lov yoki ijara shartnomasining <b>PDF</b> faylini yoki fotosuratini yuboring.\n\n"
            "AI yashirin jarimalar va noqonuniy bandlarni oddiy tilda ochib beradi.",
            parse_mode=ParseMode.HTML
        )
        return
    elif text == "🆘 Shoshilinch Yordam":
        await cmd_sos(message)
        return
    elif text == "🧠 Kiber-Viktorina":
        await cmd_quiz(message)
        return
    elif text == "👨‍👩‍👧‍👦 Oila Qalqoni":
        await message.answer(
            "👨‍👩‍👧‍👦 <b>Oila Qalqoni xizmati:</b>\n\n"
            f"Sizning Telegram ID raqamingiz: <code>{user_id}</code>\n\n"
            "Ota-onangiz yoki yaqinlaringiz botning Mini App bo'limiga kirib, sizning ID raqamingizni "
            "<b>'Himoyachi (Vasiy)'</b> sifatida kiritishsa, ular xavfli manzilga duch kelgan zahoti "
            "sizga tezkor signal keladi!",
            parse_mode=ParseMode.HTML
        )
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

        elif action == "waiting_for_scam_card" and (is_owner or (db_user and db_user.role == "admin")):
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

    # 4. Bank kartasi raqami kiritilgan bo'lsa (16 ta raqam)
    clean_digits = "".join(filter(str.isdigit, text))
    if len(clean_digits) == 16 and (clean_digits.startswith(("8600", "9860", "4", "5", "62")) or " " in text):
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

    if risk >= 70:
        report += "\n\n💡 <b>Qat'iy tavsiya:</b> Hech qanday holatda karta raqamingiz, amal qilish muddati yoki SMS orqali kelgan tasdiqlash kodini kiritmang!"

    async with AsyncSessionLocal() as session:
        hist = ScanHistory(
            user_telegram_id=user_id,
            scan_type="url_or_text",
            target_name=res["target"][:120],
            risk_score=float(risk),
            verdict=res["verdict"],
            summary_uz=res["summary_uz"],
            details_json=json.dumps(res, ensure_ascii=False)
        )
        session.add(hist)
        await session.commit()

        if risk >= 70:
            await notify_family_guardians(session, user_id, res["target"], risk, res["summary_uz"])

    await wait_msg.edit_text(report, reply_markup=get_main_inline_keyboard(user_id), parse_mode=ParseMode.HTML)


# =========================================================================
# 14. BOTNI FONDA ISHGA TUSHIRISH
# =========================================================================

async def start_telegram_bot():
    """Botni fon rejimida uzluksiz uzoq muddatli polling bilan ishga tushiradi."""
    while True:
        try:
            logger.info("Telegram Bot polling ishga tushmoqda...")
            await bot.delete_webhook(drop_pending_updates=False)
            await dp.start_polling(bot, handle_signals=False)
            break
        except asyncio.CancelledError:
            logger.info("Telegram Bot vazifasi to'xtatildi.")
            break
        except Exception as e:
            logger.error(f"Telegram Bot pollingda xatolik: {e}. 3 soniyadan keyin qayta ulanadi...")
            await asyncio.sleep(3)
