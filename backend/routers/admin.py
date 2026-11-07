import json
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, or_
from backend.config import settings
from backend.database import get_db
from backend.models import User, ScanHistory, CardBlacklist, AdminAuditLog, BroadcastMessage, CommunityBlacklist
from backend.utils import send_telegram_message

router = APIRouter(prefix="/api/admin", tags=["Admin & Owner"])


def verify_owner(telegram_id: int):
    """Faqat yagona haqiqiy Owner ruxsatini tekshirish."""
    if telegram_id != settings.OWNER_TELEGRAM_ID:
        raise HTTPException(
            status_code=403,
            detail="Faqat yagona Super Owner (@fayzbek1331) ushbu amalni bajarishi mumkin!"
        )


async def verify_admin_or_owner(db: AsyncSession, telegram_id: int) -> User:
    """Admin yoki Owner ekanligini tasdiqlash."""
    if telegram_id == settings.OWNER_TELEGRAM_ID:
        # Owner har doim ruxsatga ega
        stmt = select(User).where(User.telegram_id == telegram_id)
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=settings.OWNER_USERNAME,
                role="owner",
                active_mode="owner"
            )
            db.add(user)
            await db.commit()
        return user

    stmt = select(User).where(User.telegram_id == telegram_id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user or user.role not in ("admin", "owner") or user.is_banned:
        raise HTTPException(status_code=403, detail="Ruxsat berilmadi: Siz Admin emassiz.")
    return user


class ToggleModeRequest(BaseModel):
    telegram_id: int


class AddAdminRequest(BaseModel):
    owner_telegram_id: int
    target_telegram_id: int
    username: Optional[str] = None
    note: Optional[str] = None


class RemoveAdminRequest(BaseModel):
    owner_telegram_id: int
    target_telegram_id: int


class BanUserRequest(BaseModel):
    admin_telegram_id: int
    target_telegram_id: int
    ban: bool = True
    reason: Optional[str] = None


class BroadcastRequest(BaseModel):
    admin_telegram_id: int
    message: str


class AddCardBlacklistRequest(BaseModel):
    admin_telegram_id: int
    card_number: str
    bank_name: Optional[str] = None
    owner_name: Optional[str] = None
    reason: str


@router.get("/status/{telegram_id}")
async def get_admin_status(telegram_id: int, db: AsyncSession = Depends(get_db)):
    """Foydalanuvchining ma'murlik darajasi va rejimini tekshirish."""
    is_owner = (telegram_id == settings.OWNER_TELEGRAM_ID)

    stmt = select(User).where(User.telegram_id == telegram_id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user and is_owner:
        user = User(
            telegram_id=telegram_id,
            username=settings.OWNER_USERNAME,
            role="owner",
            active_mode="owner"
        )
        db.add(user)
        await db.commit()

    role = "owner" if is_owner else (user.role if user else "user")
    active_mode = user.active_mode if user else ("owner" if is_owner else "user")
    is_admin = is_owner or (user and user.role == "admin")

    return {
        "telegram_id": telegram_id,
        "is_owner": is_owner,
        "is_admin": is_admin,
        "role": role,
        "active_mode": active_mode, # 'owner' yoki 'user'
        "owner_username": settings.OWNER_USERNAME
    }


@router.post("/toggle-mode")
async def toggle_owner_mode(payload: ToggleModeRequest, db: AsyncSession = Depends(get_db)):
    """Owner rejimini o'zgartirish (Owner rejimi <-> Oddiy foydalanuvchi rejimi)."""
    verify_owner(payload.telegram_id)

    stmt = select(User).where(User.telegram_id == payload.telegram_id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user:
        user = User(
            telegram_id=payload.telegram_id,
            username=settings.OWNER_USERNAME,
            role="owner",
            active_mode="owner"
        )
        db.add(user)

    # Rejimni almashtirish
    new_mode = "user" if user.active_mode == "owner" else "owner"
    user.active_mode = new_mode
    await db.commit()

    return {
        "status": "success",
        "active_mode": new_mode,
        "message": f"Rejim o'zgartirildi: {'👑 Owner Boshqaruv Rejimi' if new_mode == 'owner' else '👤 Oddiy Foydalanuvchi Rejimi'}"
    }


@router.post("/add-admin")
async def add_admin(payload: AddAdminRequest, db: AsyncSession = Depends(get_db)):
    """Faqat Super Owner tomonidan yangi Admin tayinlash."""
    verify_owner(payload.owner_telegram_id)

    stmt = select(User).where(User.telegram_id == payload.target_telegram_id)
    res = await db.execute(stmt)
    target_user = res.scalar_one_or_none()

    if not target_user:
        target_user = User(
            telegram_id=payload.target_telegram_id,
            username=payload.username,
            role="admin",
            full_name=f"Admin {payload.target_telegram_id}"
        )
        db.add(target_user)
    else:
        target_user.role = "admin"

    # Audit log
    audit = AdminAuditLog(
        admin_telegram_id=payload.owner_telegram_id,
        action="add_admin",
        target=str(payload.target_telegram_id),
        details=payload.note or "Yangi admin tayinlandi"
    )
    db.add(audit)
    await db.commit()

    # Yangi adminga bildirishnoma yuborish
    await send_telegram_message(
        payload.target_telegram_id,
        "🎉 <b>Tabriklaymiz!</b>\nSiz ShieldGuard AI tizimida <b>Admin</b> etib tayinlandingiz! Boshqaruv uchun /admin buyrug'idan foydalanishingiz mumkin."
    )

    return {"status": "success", "message": f"Foydalanuvchi (ID: {payload.target_telegram_id}) admin etib tayinlandi."}


@router.post("/remove-admin")
async def remove_admin(payload: RemoveAdminRequest, db: AsyncSession = Depends(get_db)):
    """Adminni vazifasidan ozod qilish (Faqat Owner)."""
    verify_owner(payload.owner_telegram_id)

    if payload.target_telegram_id == settings.OWNER_TELEGRAM_ID:
        raise HTTPException(status_code=400, detail="Ownerni adminga tushirib bo'lmaydi!")

    stmt = select(User).where(User.telegram_id == payload.target_telegram_id)
    res = await db.execute(stmt)
    target_user = res.scalar_one_or_none()

    if target_user:
        target_user.role = "user"
        audit = AdminAuditLog(
            admin_telegram_id=payload.owner_telegram_id,
            action="remove_admin",
            target=str(payload.target_telegram_id),
            details="Admin vazifasidan ozod qilindi"
        )
        db.add(audit)
        await db.commit()

        await send_telegram_message(
            payload.target_telegram_id,
            "ℹ️ ShieldGuard tizimidagi adminlik vakolatingiz to'xtatildi."
        )

    return {"status": "success", "message": "Admin vakolati bekor qilindi."}


@router.get("/admins")
async def list_admins(caller_id: int = Query(...), db: AsyncSession = Depends(get_db)):
    """Barcha adminlar va Owner ro'yxati."""
    await verify_admin_or_owner(db, caller_id)

    stmt = select(User).where(or_(User.role == "admin", User.telegram_id == settings.OWNER_TELEGRAM_ID))
    res = await db.execute(stmt)
    admins = res.scalars().all()

    return [
        {
            "telegram_id": a.telegram_id,
            "username": a.username,
            "full_name": a.full_name,
            "is_owner": (a.telegram_id == settings.OWNER_TELEGRAM_ID),
            "role": "owner" if a.telegram_id == settings.OWNER_TELEGRAM_ID else "admin",
            "created_at": a.created_at.strftime("%Y-%m-%d %H:%M")
        } for a in admins
    ]


@router.get("/users")
async def list_all_users(
    caller_id: int = Query(...),
    query: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Foydalanuvchilar ro'yxati va qidiruv."""
    await verify_admin_or_owner(db, caller_id)

    stmt = select(User).order_by(User.created_at.desc())
    if query:
        stmt = stmt.where(or_(User.username.ilike(f"%{query}%"), User.full_name.ilike(f"%{query}%")))
    stmt = stmt.limit(limit)

    res = await db.execute(stmt)
    users = res.scalars().all()

    return [
        {
            "telegram_id": u.telegram_id,
            "username": u.username,
            "full_name": u.full_name,
            "role": "owner" if u.telegram_id == settings.OWNER_TELEGRAM_ID else u.role,
            "is_banned": u.is_banned,
            "created_at": u.created_at.strftime("%Y-%m-%d %H:%M")
        } for u in users
    ]


@router.post("/ban-user")
async def ban_user(payload: BanUserRequest, db: AsyncSession = Depends(get_db)):
    """Foydalanuvchini bloklash yoki blokdan chiqarish."""
    await verify_admin_or_owner(db, payload.admin_telegram_id)

    if payload.target_telegram_id == settings.OWNER_TELEGRAM_ID:
        raise HTTPException(status_code=400, detail="Ownerni bloklab bo'lmaydi!")

    stmt = select(User).where(User.telegram_id == payload.target_telegram_id)
    res = await db.execute(stmt)
    target = res.scalar_one_or_none()

    if not target:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi.")

    target.is_banned = payload.ban

    audit = AdminAuditLog(
        admin_telegram_id=payload.admin_telegram_id,
        action="ban_user" if payload.ban else "unban_user",
        target=str(payload.target_telegram_id),
        details=payload.reason or ""
    )
    db.add(audit)
    await db.commit()

    return {
        "status": "success",
        "message": f"Foydalanuvchi {'bloklandi' if payload.ban else 'blokdan chiqarildi'}."
    }


@router.post("/broadcast")
async def broadcast_alert(payload: BroadcastRequest, db: AsyncSession = Depends(get_db)):
    """Barcha bot foydalanuvchilariga xavfsizlik ogohlantirishini yuborish."""
    await verify_admin_or_owner(db, payload.admin_telegram_id)

    # Barcha ban qilinmagan foydalanuvchilar
    stmt = select(User.telegram_id).where(User.is_banned == False)
    res = await db.execute(stmt)
    user_ids = res.scalars().all()

    success = 0
    failed = 0

    formatted_message = (
        f"📢 <b>SHIELDGUARD RASMIY OGOHLANTIRISH</b>\n\n"
        f"{payload.message}\n\n"
        f"🛡️ <i>ShieldGuard AI — Doimo xavfsizligingiz himoyasida.</i>"
    )

    for uid in user_ids:
        sent = await send_telegram_message(uid, formatted_message)
        if sent:
            success += 1
        else:
            failed += 1

    # Saqlash
    broadcast_log = BroadcastMessage(
        sender_telegram_id=payload.admin_telegram_id,
        text=payload.message,
        total_recipients=len(user_ids),
        success_count=success,
        failed_count=failed
    )
    db.add(broadcast_log)
    await db.commit()

    return {
        "status": "success",
        "total": len(user_ids),
        "sent_success": success,
        "sent_failed": failed
    }


# Karta qora ro'yxati boshqaruvi
@router.get("/card-blacklist")
async def get_card_blacklist(db: AsyncSession = Depends(get_db)):
    """Firibgar bank kartalari ro'yxati."""
    stmt = select(CardBlacklist).order_by(CardBlacklist.created_at.desc()).limit(100)
    res = await db.execute(stmt)
    cards = res.scalars().all()
    return [
        {
            "id": c.id,
            "card_number": c.card_number,
            "bank_name": c.bank_name,
            "owner_name": c.owner_name,
            "reason": c.reason,
            "report_count": c.report_count,
            "created_at": c.created_at.strftime("%Y-%m-%d %H:%M")
        } for c in cards
    ]


@router.post("/card-blacklist")
async def add_card_blacklist(payload: AddCardBlacklistRequest, db: AsyncSession = Depends(get_db)):
    """Firibgar bank kartasini qora ro'yxatga kiritish."""
    await verify_admin_or_owner(db, payload.admin_telegram_id)

    clean_card = "".join(filter(str.isdigit, payload.card_number))
    stmt = select(CardBlacklist).where(CardBlacklist.card_number == clean_card)
    res = await db.execute(stmt)
    existing = res.scalar_one_or_none()

    if existing:
        existing.report_count += 1
        existing.reason += f"\nQo'shimcha: {payload.reason}"
        await db.commit()
        return {"status": "updated", "message": "Karta allaqachon mavjud edi, shikoyatlar soni oshirildi."}

    new_card = CardBlacklist(
        card_number=clean_card,
        bank_name=payload.bank_name or "Noma'lum",
        owner_name=payload.owner_name,
        reason=payload.reason
    )
    db.add(new_card)
    await db.commit()

    return {"status": "success", "message": f"Karta ({clean_card}) qora ro'yxatga kiritildi."}


@router.delete("/card-blacklist/{card_id}")
async def delete_card_blacklist(card_id: int, admin_id: int = Query(...), db: AsyncSession = Depends(get_db)):
    """Firibgar kartani qora ro'yxatdan o'chirish."""
    await verify_admin_or_owner(db, admin_id)

    card = await db.get(CardBlacklist, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Karta topilmadi.")

    await db.delete(card)
    await db.commit()
    return {"status": "success", "message": "Karta qora ro'yxatdan chiqarildi."}


@router.get("/audit-logs")
async def get_audit_logs(admin_id: int = Query(...), db: AsyncSession = Depends(get_db)):
    """Barcha admin amallari tarixi."""
    await verify_admin_or_owner(db, admin_id)

    stmt = select(AdminAuditLog).order_by(AdminAuditLog.created_at.desc()).limit(50)
    res = await db.execute(stmt)
    logs = res.scalars().all()

    return [
        {
            "id": l.id,
            "admin_telegram_id": l.admin_telegram_id,
            "action": l.action,
            "target": l.target,
            "details": l.details,
            "created_at": l.created_at.strftime("%Y-%m-%d %H:%M")
        } for l in logs
    ]
