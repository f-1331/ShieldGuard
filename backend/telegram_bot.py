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
    WebAppInfo
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
from backend.utils import notify_family_guardians

logger = logging.getLogger(__name__)

bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()


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


def get_main_inline_keyboard(user_id: int, is_owner: bool = False, active_mode: str = "user") -> InlineKeyboardMarkup:
    """Asosiy WebApp va tezkor tugmalar (Telegram HTTPS talabiga mos)."""
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

    # Agar foydalanuvchi Super Owner bo'lsa
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


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    """Start buyrug'i uchun salomlashish va qo'llanma."""
    user = message.from_user
    db_user = None
    if user:
        db_user = await get_or_create_user(user.id, user.username, user.full_name)

    is_owner = (user.id == settings.OWNER_TELEGRAM_ID if user else False)
    active_mode = db_user.active_mode if db_user else ("owner" if is_owner else "user")

    if is_owner and active_mode == "owner":
        owner_welcome = (
            f"👑 <b>Assalomu alaykum, Hurmatli Bosh Administrator (Owner) @{settings.OWNER_USERNAME}!</b>\n\n"
            f"🛡️ <b>ShieldGuard Pro AI</b> boshqaruv tizimi ixtiyoringizda.\n\n"
            f"⚡ <b>Sizning imtiyozlaringiz:</b>\n"
            f"• <b>/admin</b> — To'liq admin paneli va jonli statistika\n"
            f"• <b>/switch_role</b> — Oddiy foydalanuvchi va Owner rejimlarini almashtirish\n"
            f"• <b>/addadmin &lt;id&gt;</b> — Yangi admin tayinlash\n"
            f"• <b>/deladmin &lt;id&gt;</b> — Adminni o'chirish\n"
            f"• <b>/broadcast &lt;matn&gt;</b> — Barcha foydalanuvchilarga xabar yuborish\n"
            f"• <b>/ban &lt;id&gt;</b> & <b>/unban &lt;id&gt;</b> — Bloklash/Chiqarish\n\n"
            f"👇 <i>Kerakli bo'limni tanlang:</i>"
        )
        await message.answer(
            text=owner_welcome,
            reply_markup=get_main_inline_keyboard(user.id, is_owner=True, active_mode="owner"),
            parse_mode=ParseMode.HTML
        )
        return

    welcome_text = (
        f"👋 <b>Assalomu alaykum, {user.first_name if user else 'qadrdon yurtdosh'}!</b>\n\n"
        f"🛡️ <b>ShieldGuard AI</b> — siz va oilangizni internetdagi fishing, "
        f"soxta bank kartalari, zararli APK-viruslar va og'ir shartnoma tuzoqlaridan "
        f"himoya qiluvchi keng qamrovli kiber-qalqondir.\n\n"
        f"⚡ <b>Menga quyidagilarni yuborishingiz mumkin:</b>\n"
        f"• Shubhali havola yoki matn (fishing skaneri);\n"
        f"• 16 talik bank karta raqami (masalan: <code>8600...</code> yoki <code>9860...</code>);\n"
        f"• Shubhali Telegram bot (masalan: <code>@click_bonus_bot</code>);\n"
        f"• Telegramdan kelgan fayl (masalan: <code>To'y taklifnomasi.apk</code>);\n"
        f"• Kredit yoki ijara shartnomasi (PDF yoki fotosurat).\n\n"
        f"👇 <i>Kerakli xizmatni tanlang:</i>"
    )

    if is_owner and active_mode == "user":
        welcome_text += "\n\n<i>[💡 Siz hozir oddiy foydalanuvchi rejimidasiz. Owner rejimiga qaytish: /switch_role]</i>"

    await message.answer(
        text=welcome_text,
        reply_markup=get_main_inline_keyboard(user.id if user else 0, is_owner=is_owner, active_mode=active_mode),
        parse_mode=ParseMode.HTML
    )


# Role Switching (Owner <-> User)
@dp.message(Command("switch_role"))
async def cmd_switch_role(message: types.Message):
    user = message.from_user
    if user.id != settings.OWNER_TELEGRAM_ID:
        await message.answer("❌ Bu buyruq faqat loyiha egasi (@fayzbek1331) uchun mo'ljallangan.")
        return

    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.telegram_id == user.id)
        res = await session.execute(stmt)
        db_user = res.scalar_one_or_none()

        if not db_user:
            db_user = User(telegram_id=user.id, username=user.username, role="owner", active_mode="owner")
            session.add(db_user)

        new_mode = "user" if db_user.active_mode == "owner" else "owner"
        db_user.active_mode = new_mode
        await session.commit()

        if new_mode == "owner":
            text = "👑 <b>Owner Rejimi Faollashtirildi!</b>\nBarcha ma'muriy vakolatlar va /admin buyruqlari yoqildi."
        else:
            text = "👤 <b>Oddiy Foydalanuvchi Rejimi Faollashtirildi!</b>\nSiz hozir botni oddiy fuqaro ko'zi bilan sinab ko'rishingiz mumkin.\nQaytish uchun: /switch_role"

        await message.answer(
            text,
            reply_markup=get_main_inline_keyboard(user.id, is_owner=True, active_mode=new_mode),
            parse_mode=ParseMode.HTML
        )


@dp.callback_query(F.data == "btn_toggle_role")
async def cb_toggle_role(callback: types.CallbackQuery):
    user = callback.from_user
    if user.id != settings.OWNER_TELEGRAM_ID:
        await callback.answer("Faqat Owner uchun!", show_alert=True)
        return

    await callback.answer()
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.telegram_id == user.id)
        res = await session.execute(stmt)
        db_user = res.scalar_one_or_none()
        new_mode = "user" if db_user.active_mode == "owner" else "owner"
        db_user.active_mode = new_mode
        await session.commit()

        await callback.message.answer(
            f"🔄 Rejim o'zgartirildi: <b>{'👑 Owner Rejimi' if new_mode == 'owner' else '👤 Foydalanuvchi Rejimi'}</b>",
            reply_markup=get_main_inline_keyboard(user.id, is_owner=True, active_mode=new_mode),
            parse_mode=ParseMode.HTML
        )


# Admin Boshqaruv Markazi
@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
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

        # Statistika yig'ish
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
                f"• <code>/addadmin &lt;telegram_id&gt;</code> — Yangi admin tayinlash\n"
                f"• <code>/deladmin &lt;telegram_id&gt;</code> — Adminni o'chirish\n"
                f"• <code>/switch_role</code> — Oddiy foydalanuvchi rejimiga o'tish\n"
            )

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="👥 Adminlar ro'yxati", callback_data="btn_list_admins"),
                    InlineKeyboardButton(text="🚫 Firibgar kartalar", callback_data="btn_list_cards")
                ],
                [
                    InlineKeyboardButton(text="🔄 Rejimni almashtirish", callback_data="btn_toggle_role")
                ]
            ]
        )

        await message.answer(admin_text, reply_markup=kb, parse_mode=ParseMode.HTML)


@dp.callback_query(F.data == "btn_open_admin")
async def cb_open_admin(callback: types.CallbackQuery):
    await callback.answer()
    await cmd_admin(callback.message)


# Admin tayinlash (Faqat Owner)
@dp.message(Command("addadmin"))
async def cmd_add_admin(message: types.Message):
    user = message.from_user
    if user.id != settings.OWNER_TELEGRAM_ID:
        await message.answer("❌ Faqat loyiha egasi (@fayzbek1331) yangi admin tayinlay oladi.")
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip().isdigit():
        await message.answer("Foydalanish: <code>/addadmin &lt;telegram_id&gt;</code>\nMasalan: <code>/addadmin 123456789</code>", parse_mode=ParseMode.HTML)
        return

    target_id = int(parts[1].strip())
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.telegram_id == target_id)
        res = await session.execute(stmt)
        target = res.scalar_one_or_none()

        if not target:
            target = User(telegram_id=target_id, role="admin", full_name=f"Admin {target_id}")
            session.add(target)
        else:
            target.role = "admin"

        audit = AdminAuditLog(admin_telegram_id=user.id, action="add_admin", target=str(target_id), details="Owner tomonidan tayinlandi")
        session.add(audit)
        await session.commit()

        await message.answer(f"✅ Foydalanuvchi (ID: <code>{target_id}</code>) muvaffaqiyatli <b>Admin</b> etib tayinlandi!", parse_mode=ParseMode.HTML)
        await send_telegram_message(target_id, "🎉 Siz ShieldGuard AI tizimida <b>Admin</b> etib tayinlandingiz! Buyruqlar uchun: /admin")


# Adminni o'chirish (Faqat Owner)
@dp.message(Command("deladmin"))
async def cmd_del_admin(message: types.Message):
    user = message.from_user
    if user.id != settings.OWNER_TELEGRAM_ID:
        await message.answer("❌ Faqat loyiha egasi (@fayzbek1331) adminni o'chira oladi.")
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip().isdigit():
        await message.answer("Foydalanish: <code>/deladmin &lt;telegram_id&gt;</code>", parse_mode=ParseMode.HTML)
        return

    target_id = int(parts[1].strip())
    if target_id == settings.OWNER_TELEGRAM_ID:
        await message.answer("❌ Ownerni o'chirib bo'lmaydi!")
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
        else:
            await message.answer("Ushbu foydalanuvchi admin emas.")


# Adminlar ro'yxati
@dp.message(Command("admins"))
async def cmd_list_admins(message: types.Message):
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(or_(User.role == "admin", User.telegram_id == settings.OWNER_TELEGRAM_ID))
        res = await session.execute(stmt)
        admins = res.scalars().all()

        text = "👥 <b>SHIELDGUARD MA'MURLARI RO'YXATI:</b>\n\n"
        for a in admins:
            is_own = (a.telegram_id == settings.OWNER_TELEGRAM_ID)
            status = "👑 SUPER OWNER" if is_own else "🛡️ ADMIN"
            username = f"@{a.username}" if a.username else "Usernamesiz"
            text += f"• <b>{status}:</b> {a.full_name or 'Noma`lum'} ({username}) — ID: <code>{a.telegram_id}</code>\n"

        await message.answer(text, parse_mode=ParseMode.HTML)


@dp.callback_query(F.data == "btn_list_admins")
async def cb_list_admins(callback: types.CallbackQuery):
    await callback.answer()
    await cmd_list_admins(callback.message)


# Barcha foydalanuvchilarga xabar tarqatish (Broadcast)
@dp.message(Command("broadcast"))
async def cmd_broadcast(message: types.Message):
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
            await message.answer("Foydalanish: <code>/broadcast &lt;xabaringiz matni&gt;</code>", parse_mode=ParseMode.HTML)
            return

        broadcast_body = parts[1].strip()
        status_msg = await message.answer("⏳ <i>Xabar tarqatilmoqda...</i>", parse_mode=ParseMode.HTML)

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

        b_log = BroadcastMessage(sender_telegram_id=user.id, text=broadcast_body, total_recipients=len(uids), success_count=sent, failed_count=failed)
        session.add(b_log)
        await session.commit()

        await status_msg.edit_text(
            f"✅ <b>E'lon tarqatildi!</b>\n\n"
            f"• Jami a'zolar: {len(uids)}\n"
            f"• Muvaffaqiyatli yetkazildi: <b>{sent}</b> ta\n"
            f"• Yetkazib bo'lmadi (bloklaganlar): {failed} ta",
            parse_mode=ParseMode.HTML
        )


# Foydalanuvchini bloklash
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


# Foydalanuvchini blokdan chiqarish
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


# Karta tekshirish buyrug'i (/card 8600...)
@dp.message(Command("card"))
async def cmd_check_card(message: types.Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Foydalanish: <code>/card 8600123456789012</code>\n16 talik bank karta raqamini kiriting.", parse_mode=ParseMode.HTML)
        return

    card_raw = parts[1].strip()
    analysis = analyze_card_number(card_raw)
    clean_card = "".join(filter(str.isdigit, card_raw))

    # Qora ro'yxatni tekshirish
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


# Telegram Bot tekshirish (/botcheck @...)
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


# SOS Favqulodda Yo'riqnoma (/sos)
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
        "3️⃣ <b>IIv KIBERXAVFSIZLIK MARKAZI:</b>\n"
        "📞 Ishonch telefoni: <b>1102</b> yoki <b>102</b>\n"
        "Barcha yozishmalar, cheklar va telefon raqamlarni skrinshot qilib saqlang!"
    )
    await message.answer(sos_text, parse_mode=ParseMode.HTML)


# Kiber-Savodxonlik Testi (/quiz)
@dp.message(Command("quiz"))
async def cmd_quiz(message: types.Message):
    quiz_welcome = (
        "🧠 <b>SHIELDGUARD KIBER-SAVODXONLIK TESTI:</b>\n\n"
        "Siz o'zingizni internetdagi firibgarlik va kiber-tuzoqlardan himoya qila olasizmi?\n\n"
        "Ushbu interaktiv testda real hayotdagi 5 ta eng xavfli firibgarlik sxemasi keltirilgan. "
        "Sinovdan o'ting va 'Kiber-Qalqon Sertifikati'ga ega bo'ling!\n\n"
        "👇 <i>Testni boshlash uchun WebApp ilovasini oching:</i>"
    )
    await message.answer(
        quiz_welcome,
        reply_markup=get_main_inline_keyboard(message.from_user.id),
        parse_mode=ParseMode.HTML
    )


# Callbacks
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


@dp.callback_query(F.data == "btn_report_info")
async def cb_report_info(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "🚫 <b>Firibgarlik manzilini xabar qilish:</b>\n\n"
        "Siz duch kelgan soxta kanal, fishing havola yoki firibgar bot manzilini shu chatga yuboring. "
        "Biz uni tekshirib, butun O'zbekiston foydalanuvchilari uchun umumiy qora ro'yxatga kiritamiz!",
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


# Hujjat va Fayllarni (APK, PDF) qabul qilish
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

        # 2. Shartnoma (PDF)
        elif lower_name.endswith(".pdf") or "shartnoma" in lower_name or "dogovor" in lower_name:
            res = await analyze_contract_file(filename, file_bytes, mime_type="application/pdf")
            safety = res["overall_safety_score"]

            if safety < 50:
                badge = "🔴 <b>O'TA NOQULAY VA TUZOQLARGA BOY SHARTNOMA</b>"
            elif safety < 75:
                badge = "🟡 <b>SHUBHALI VA EHTIYOTKORLIK TALAB ETILADI</b>"
            else:
                badge = "🟢 <b>STANDART VA NISBATAN XAVFSIZ SHARTNOMA</b>"

            report = (
                f"📄 <b>SHARTNOMA RENTGENI NATIJASI:</b>\n\n"
                f"📁 <b>Hujjat:</b> <code>{filename}</code>\n"
                f"📑 <b>Turi:</b> {res['contract_type']}\n"
                f"🛡️ <b>Xavfsizlik indeksi:</b> <b>{safety}/100</b> ({badge})\n\n"
                f"📋 <b>Xulosa:</b>\n{res['summary_uz']}\n"
            )

            if res.get("dangerous_clauses"):
                report += "\n⚠️ <b>Topilgan xavfli moddalar:</b>\n"
                for c in res["dangerous_clauses"][:3]:
                    report += f"• <b>{c.get('clause_num', 'Band')}:</b> {c.get('explanation_uz', '')}\n"

            if res.get("financial_traps"):
                report += "\n💸 <b>Moliyaviy xavflar:</b>\n"
                for t in res["financial_traps"][:3]:
                    report += f"• {t}\n"

            async with AsyncSessionLocal() as session:
                hist = ScanHistory(
                    user_telegram_id=user_id,
                    scan_type="contract",
                    target_name=filename,
                    risk_score=float(100 - safety),
                    verdict=res["verdict"],
                    summary_uz=res["summary_uz"],
                    details_json=json.dumps(res, ensure_ascii=False)
                )
                session.add(hist)
                await session.commit()

            await wait_msg.edit_text(report, reply_markup=get_main_inline_keyboard(user_id), parse_mode=ParseMode.HTML)

        else:
            res = analyze_file_security(filename, file_bytes)
            await wait_msg.edit_text(
                f"📁 <b>Fayl tekshirildi:</b> <code>{filename}</code>\n"
                f"Hukm: {res['verdict_uz']}\n"
                f"Xulosa: {res['summary_uz']}",
                reply_markup=get_main_inline_keyboard(user_id),
                parse_mode=ParseMode.HTML
            )

    except Exception as e:
        logger.error(f"Fayl tahlilida xatolik: {e}")
        await wait_msg.edit_text("❌ Faylni tahlil qilishda texnik xatolik yuz berdi. Iltimos qayta urinib ko'ring.")


# Fotosuratlarni tahlil qilish
@dp.message(F.photo)
async def handle_photo(message: types.Message):
    user_id = message.from_user.id
    wait_msg = await message.answer("🔍 <i>Fotosurat qabul qilindi. AI tasvir tahlilini amalga oshirmoqda...</i>", parse_mode=ParseMode.HTML)

    try:
        photo = message.photo[-1]
        file_io = io.BytesIO()
        await bot.download(photo, destination=file_io)
        img_bytes = file_io.getvalue()

        res = await analyze_contract_file("hujjat_surati.jpg", img_bytes, mime_type="image/jpeg")

        report = (
            f"📸 <b>FOTOSURAT TAHLILI (Shartnoma / Hujjat):</b>\n\n"
            f"📑 <b>Turi:</b> {res['contract_type']}\n"
            f"🛡️ <b>Xavfsizlik darajasi:</b> {res['overall_safety_score']}/100\n"
            f"📋 <b>Xulosa:</b> {res['summary_uz']}\n"
        )

        if res.get("dangerous_clauses"):
            report += "\n⚠️ <b>Topilgan xavflar:</b>\n"
            for c in res["dangerous_clauses"][:2]:
                report += f"• {c.get('explanation_uz', '')}\n"

        await wait_msg.edit_text(report, reply_markup=get_main_inline_keyboard(user_id), parse_mode=ParseMode.HTML)

    except Exception as e:
        logger.error(f"Rasm tahlilida xatolik: {e}")
        await wait_msg.edit_text("❌ Tasvirni qayta ishlashda xatolik yuz berdi.")


# Matnli xabarlar (URL, Karta raqam, Bot user yoki oddiy fishing xabar)
@dp.message(F.text)
async def handle_text_message(message: types.Message):
    text = message.text.strip()
    user = message.from_user
    user_id = user.id if user else 0

    db_user = None
    if user:
        db_user = await get_or_create_user(user.id, user.username, user.full_name)
        if db_user and db_user.is_banned:
            await message.answer("🚫 Sizning hisobingiz ShieldGuard qoidalarini buzganlik sababli bloklangan.")
            return

    # 1. Agar foydalanuvchi bank kartasi raqamini kiritgan bo'lsa (16 ta raqam)
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

    # 2. Agar foydalanuvchi Telegram bot userini kiritgan bo'lsa (@...bot)
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

    # 3. URL yoki umumiy firibgarlik xabari
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
