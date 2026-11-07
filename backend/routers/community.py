from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.database import get_db
from backend.models import CommunityBlacklist

router = APIRouter(prefix="/api/community", tags=["Community Blacklist"])

class ScamReportRequest(BaseModel):
    domain_or_pattern: str
    category: str = "phishing"  # phishing, fake_lottery, predatory_loan, apk_trojan
    reason: str
    reported_by_telegram_id: Optional[int] = None


# Dastlabki ma'lumotlar bazasi uchun eng ko'p uchraydigan scam tuzoqlar
INITIAL_SEEDS = [
    {
        "domain_or_pattern": "c1ick-oplata.com",
        "category": "phishing",
        "reason": "Click to'lov tizimining qalbaki nusxasi, karta ma'lumotlarini o'g'irlash uchun yaratilgan."
    },
    {
        "domain_or_pattern": "payme-subsidiyalar.top",
        "category": "fake_lottery",
        "reason": "Prezident nomidan 650,000 so'm tarqatilyapti deb aldovchi soxta fishing sayt."
    },
    {
        "domain_or_pattern": "uzum-bonus-aksiya.site",
        "category": "phishing",
        "reason": "Uzum Market nomidan foydalanib karta raqami va SMS kodni talab qiluvchi manzil."
    },
    {
        "domain_or_pattern": "humo-yutuqli-oyin.buzz",
        "category": "fake_lottery",
        "reason": "Humo kartalari o'rtasida yutuq chiqdi deb aldovchi kiber-tuzoq."
    },
    {
        "domain_or_pattern": "To'y taklifnomasi.pdf.apk",
        "category": "apk_trojan",
        "reason": "Telegram orqali tarqatilayotgan xavfli Android troyan virusi."
    }
]


@router.post("/report")
async def report_scam(payload: ScamReportRequest, db: AsyncSession = Depends(get_db)):
    """Foydalanuvchi tomonidan yangi fishing manzil yoki scam xabarini hisobot qilish."""
    domain_clean = payload.domain_or_pattern.strip().lower()

    stmt = select(CommunityBlacklist).where(CommunityBlacklist.domain_or_pattern == domain_clean)
    res = await db.execute(stmt)
    existing = res.scalar_one_or_none()

    if existing:
        return {"status": "exists", "message": "Ushbu manzil allaqachon ShieldGuard qora ro'yxatida mavjud!"}

    new_item = CommunityBlacklist(
        domain_or_pattern=domain_clean,
        category=payload.category,
        reason=payload.reason,
        reported_by_telegram_id=payload.reported_by_telegram_id,
        status="verified"
    )
    db.add(new_item)
    await db.commit()

    return {
        "status": "success",
        "message": "Firibgarlik manzilini xabar qilganingiz uchun rahmat! Ushbu manzil umumiy qora ro'yxatga kiritildi."
    }


@router.get("/blacklist")
async def get_community_blacklist(db: AsyncSession = Depends(get_db)):
    """Tasdiqlangan kiber-firibgarlik manzillari va tuzoqlari ro'yxati."""
    stmt = select(CommunityBlacklist).order_by(CommunityBlacklist.created_at.desc()).limit(100)
    res = await db.execute(stmt)
    items = res.scalars().all()

    # Agar baza bo'sh bo'lsa, urug' ma'lumotlarni qo'shish
    if not items:
        for seed in INITIAL_SEEDS:
            b_item = CommunityBlacklist(
                domain_or_pattern=seed["domain_or_pattern"],
                category=seed["category"],
                reason=seed["reason"],
                status="verified"
            )
            db.add(b_item)
        await db.commit()

        stmt = select(CommunityBlacklist).order_by(CommunityBlacklist.created_at.desc())
        res = await db.execute(stmt)
        items = res.scalars().all()

    return [
        {
            "id": i.id,
            "domain_or_pattern": i.domain_or_pattern,
            "category": i.category,
            "reason": i.reason,
            "status": i.status,
            "created_at": i.created_at.strftime("%Y-%m-%d %H:%M")
        } for i in items
    ]
