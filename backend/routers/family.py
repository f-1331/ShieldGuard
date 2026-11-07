from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.database import get_db
from backend.models import FamilyLink, User

router = APIRouter(prefix="/api/family", tags=["Family Shield"])

class LinkFamilyRequest(BaseModel):
    parent_telegram_id: int
    child_telegram_id: int
    relationship_name: str = "Yaqin insonim"


class ToggleAlertRequest(BaseModel):
    telegram_id: int
    enabled: bool


@router.post("/link")
async def link_family_member(payload: LinkFamilyRequest, db: AsyncSession = Depends(get_db)):
    """Oila a'zosini (masalan, ota-onani) himoyaga ulash."""
    # Bog'lanish avval mavjudligini tekshirish
    stmt = select(FamilyLink).where(
        FamilyLink.parent_telegram_id == payload.parent_telegram_id,
        FamilyLink.child_telegram_id == payload.child_telegram_id
    )
    res = await db.execute(stmt)
    existing = res.scalar_one_or_none()

    if existing:
        existing.relationship_name = payload.relationship_name
        await db.commit()
        return {"status": "updated", "message": "Oila a'zosi yangilandi.", "link_id": existing.id}

    new_link = FamilyLink(
        parent_telegram_id=payload.parent_telegram_id,
        child_telegram_id=payload.child_telegram_id,
        relationship_name=payload.relationship_name
    )
    db.add(new_link)
    await db.commit()
    await db.refresh(new_link)

    return {
        "status": "success",
        "message": f"'{payload.relationship_name}' muvaffaqiyatli himoyaga ulandi!",
        "link_id": new_link.id
    }


@router.get("/{telegram_id}")
async def get_family_members(telegram_id: int, db: AsyncSession = Depends(get_db)):
    """Foydalanuvchining ulangan oila a'zolari va vasiylari ro'yxatini olish."""
    # 1. Men kimlarni himoya qilaman (Men vasiyman, ular ota-onam/qarindoshim)
    guardian_stmt = select(FamilyLink).where(FamilyLink.child_telegram_id == telegram_id)
    guardian_res = await db.execute(guardian_stmt)
    protecting = guardian_res.scalars().all()

    # 2. Meni kim himoya qiladi (Mening vasiylarim)
    protected_stmt = select(FamilyLink).where(FamilyLink.parent_telegram_id == telegram_id)
    protected_res = await db.execute(protected_stmt)
    guardians = protected_res.scalars().all()

    return {
        "telegram_id": telegram_id,
        "protecting": [
            {
                "link_id": p.id,
                "relative_telegram_id": p.parent_telegram_id,
                "relationship_name": p.relationship_name,
                "created_at": p.created_at.strftime("%Y-%m-%d %H:%M")
            } for p in protecting
        ],
        "guardians": [
            {
                "link_id": g.id,
                "guardian_telegram_id": g.child_telegram_id,
                "relationship_name": g.relationship_name,
                "created_at": g.created_at.strftime("%Y-%m-%d %H:%M")
            } for g in guardians
        ]
    }


@router.delete("/link/{link_id}")
async def delete_family_link(link_id: int, db: AsyncSession = Depends(get_db)):
    """Oila a'zosi himoyasini bekor qilish."""
    link = await db.get(FamilyLink, link_id)
    if not link:
        raise HTTPException(status_code=404, detail="Bog'lanish topilmadi.")

    await db.delete(link)
    await db.commit()
    return {"status": "success", "message": "Oila a'zosi himoyadan chiqarildi."}
