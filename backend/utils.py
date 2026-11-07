import json
import logging
import httpx
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.config import settings
from backend.models import FamilyLink, User

logger = logging.getLogger(__name__)

async def send_telegram_message(chat_id: int, text: str, parse_mode: str = "HTML") -> bool:
    """Telegram API orqali bevosita xabar yuborish."""
    if not settings.TELEGRAM_BOT_TOKEN:
        return False

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode
    }

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(url, json=payload)
            return resp.status_code == 200
    except Exception as e:
        logger.error(f"Telegramga xabar jo'natishda xatolik ({chat_id}): {e}")
        return False


async def notify_family_guardians(
    db: AsyncSession,
    user_telegram_id: int,
    target_name: str,
    risk_score: float,
    summary_uz: str
):
    """Agar ota-ona yoki yaqin inson xavfli tuzoqqa duch kelsa, qaramog'idagi vasiyga (farzandiga) tezkor signal yuborish."""
    try:
        # Ushbu foydalanuvchini vasiylikka olgan farzand/vasiylarni qidirish
        stmt = select(FamilyLink).where(FamilyLink.parent_telegram_id == user_telegram_id)
        res = await db.execute(stmt)
        links = res.scalars().all()

        if not links:
            return

        # Foydalanuvchi ismini olish
        user_stmt = select(User).where(User.telegram_id == user_telegram_id)
        user_res = await db.execute(user_stmt)
        parent_user = user_res.scalar_one_or_none()
        parent_name = parent_user.full_name if parent_user and parent_user.full_name else f"ID: {user_telegram_id}"

        alert_message = (
            f"🚨 <b>SHIELDGUARD: OILA XAVFSIZLIGI SIGNAL!</b>\n\n"
            f"Hurmatli foydalanuvchi, sizning yaqin insoningiz <b>{parent_name}</b> "
            f"hozirgina jiddiy kiber-tuzoq yoki firibgarlikka duch keldi!\n\n"
            f"🎯 <b>Nishon:</b> <code>{target_name[:80]}</code>\n"
            f"⚠️ <b>Xavf darajasi:</b> {int(risk_score)}% (Kritik xavfli!)\n"
            f"📋 <b>Tafsilot:</b> {summary_uz}\n\n"
            f"💡 <b>Tavsiya:</b> Iltimos, darhol yaqiningiz bilan bog'laning va ulardan hech qanday "
            f"SMS-kod yoki karta ma'lumotlarini hech kimga bermaslikni so'rang!"
        )

        for link in links:
            await send_telegram_message(link.child_telegram_id, alert_message)

    except Exception as e:
        logger.error(f"Oila xavfsizligi xabarnomasida xatolik: {e}")
