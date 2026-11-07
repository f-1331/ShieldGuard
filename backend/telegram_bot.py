import io
import json
import logging
from typing import Optional
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
from backend.config import settings
from backend.database import AsyncSessionLocal
from backend.models import User, ScanHistory
from backend.security_engine.url_analyzer import analyze_url_or_text
from backend.security_engine.apk_analyzer import analyze_file_security
from backend.security_engine.contract_analyzer import analyze_contract_file
from backend.utils import notify_family_guardians

logger = logging.getLogger(__name__)

bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()


async def get_or_create_user(telegram_id: int, username: Optional[str], full_name: Optional[str]):
    """Foydalanuvchini bazaga kiritish yoki yangilash (Xavfsiz qidiruv)."""
    async with AsyncSessionLocal() as session:
        from sqlalchemy.future import select
        stmt = select(User).where(User.telegram_id == telegram_id)
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()

        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                full_name=full_name or "Foydalanuvchi"
            )
            session.add(user)
            try:
                await session.commit()
            except Exception:
                await session.rollback()
        else:
            changed = False
            if username and user.username != username:
                user.username = username
                changed = True
            if full_name and user.full_name != full_name:
                user.full_name = full_name
                changed = True
            if changed:
                try:
                    await session.commit()
                except Exception:
                    await session.rollback()
        return user


def get_main_inline_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Asosiy WebApp va tezkor tugmalar (Telegram HTTPS talabiga mos)."""
    webapp_url = (settings.WEBAPP_URL or "").strip()
    
    first_row = []
    # Faqat haqiqiy HTTPS havola bo'lsa (Vercel yoki domen) Mini App ochiladi
    if webapp_url.startswith("https://"):
        first_row.append(
            InlineKeyboardButton(
                text="🛡️ Ilovada ochish (Mini App)",
                web_app=WebAppInfo(url=webapp_url)
            )
        )
    else:
        # Telegram API localhost URL larini qabul qilmaydi, shuning uchun xavfsiz callback tugma
        first_row.append(
            InlineKeyboardButton(
                text="📱 Ilovada ko'rish (Mini App)",
                callback_data="btn_webapp_info"
            )
        )

    return InlineKeyboardMarkup(
        inline_keyboard=[
            first_row,
            [
                InlineKeyboardButton(text="📄 Shartnoma auditi", callback_data="btn_contract_info"),
                InlineKeyboardButton(text="👨‍👩‍👧‍👦 Oila Qalqoni", callback_data="btn_family_info")
            ],
            [
                InlineKeyboardButton(text="🚫 Shubhali saytni xabar qilish", callback_data="btn_report_info")
            ]
        ]
    )


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    """Start buyrug'i uchun salomlashish va qo'llanma."""
    user = message.from_user
    if user:
        await get_or_create_user(user.id, user.username, user.full_name)

    welcome_text = (
        f"👋 <b>Assalomu alaykum, {user.first_name if user else 'qadrdon yurtdosh'}!</b>\n\n"
        f"🛡️ <b>ShieldGuard AI</b> — siz va oilangizni internetdagi har qanday firibgarlik, "
        f"soxta fishing havolalar, xavfli APK-viruslar hamda noqulay shartnoma tuzoqlaridan "
        f"himoya qiluvchi intellektual qalqondir.\n\n"
        f"⚡ <b>Menga quyidagilarni yuborishingiz mumkin:</b>\n"
        f"• Shubhali havola (URL) yoki xabar (fishing tekshiruvi);\n"
        f"• Telegramdan kelgan fayl (masalan, <code>To'y taklifnomasi.apk</code>);\n"
        f"• Kredit, ijara yoki lizing shartnomasi (PDF yoki fotosurat).\n\n"
        f"👇 <i>Qulay interaktiv tahlil uchun Mini App-ni oching:</i>"
    )

    await message.answer(
        text=welcome_text,
        reply_markup=get_main_inline_keyboard(user.id if user else 0),
        parse_mode=ParseMode.HTML
    )


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Qo'llanma va bot imkoniyatlari."""
    help_text = (
        "📖 <b>ShieldGuard AI Botidan foydalanish qo'llanmasi:</b>\n\n"
        "1️⃣ <b>Havola yoki matn tekshiruvi:</b>\n"
        "Sizga kelgan shubhali xabarni yoki havolani to'g'ridan-to'g'ri menga yuboring yoki forward qiling. "
        "Men bir necha soniyada uning qanchalik xavfsiz ekanini aytib beraman.\n\n"
        "2️⃣ <b>APK va viruslar tahlili:</b>\n"
        "Noma'lum kishilar yuborgan '.apk' kengaytmali ilovalarni o'rnatishdan oldin botga jo'nating. "
        "Ilova SMSlaringizni o'g'irlashi mumkin bo'lsa, ogohlantiramiz.\n\n"
        "3️⃣ <b>Shartnoma Rentgeni:</b>\n"
        "Kredit yoki qarz shartnomasining PDF yoki fotosuratini yuklang. "
        "Yashirin komissiyalar va asossiz penya jarimalarini oddiy tilda ochib beramiz.\n\n"
        "4️⃣ <b>Oila Qalqoni:</b>\n"
        "Ota-onangizni tizimga ulab qo'ysangiz, ular xavfli fishing tuzog'iga tushganda sizga darhol ogohlantirish boradi."
    )
    await message.answer(help_text, reply_markup=get_main_inline_keyboard(message.from_user.id), parse_mode=ParseMode.HTML)


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
        # Faylni xotiraga yuklab olish
        file_io = io.BytesIO()
        await bot.download(doc, destination=file_io)
        file_bytes = file_io.getvalue()

        # 1. Agar bu APK yoki shubhali ilova bo'lsa
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

            # Tarixga yozish
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

        # 2. Agar bu Shartnoma (PDF) bo'lsa
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

            # Tarixga yozish
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
            # Oddiy fayl tekshiruvi
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


# Rasmlarni (Shartnoma surati yoki skrinshot) qabul qilish
@dp.message(F.photo)
async def handle_photo(message: types.Message):
    user_id = message.from_user.id
    wait_msg = await message.answer("🔍 <i>Fotosurat qabul qilindi. AI tasvir tahlilini amalga oshirmoqda...</i>", parse_mode=ParseMode.HTML)

    try:
        photo = message.photo[-1]
        file_io = io.BytesIO()
        await bot.download(photo, destination=file_io)
        img_bytes = file_io.getvalue()

        # Shartnoma yoki firibgarlik skrinshoti tahlili
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


# Matnli xabarlar va Havolalarni qabul qilish
@dp.message(F.text)
async def handle_text_message(message: types.Message):
    text = message.text.strip()
    user = message.from_user
    user_id = user.id if user else 0

    if user:
        await get_or_create_user(user.id, user.username, user.full_name)

    # Agar juda qisqa bo'lsa
    if len(text) < 4:
        await message.answer("Iltimos, tekshirish uchun to'liqroq havola yoki shubhali xabar matnini yuboring.")
        return

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

    # Bazaga saqlash
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
