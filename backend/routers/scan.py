import json
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.database import get_db
from backend.models import ScanHistory, User
from backend.security_engine.url_analyzer import analyze_url_or_text
from backend.security_engine.apk_analyzer import analyze_file_security
from backend.security_engine.contract_analyzer import analyze_contract_file
from backend.utils import notify_family_guardians

router = APIRouter(prefix="/api/scan", tags=["Scanner"])

async def ensure_db_user(db: AsyncSession, telegram_id: int):
    """Foydalanuvchini bazadan qidirish yoki xavfsiz yaratish."""
    stmt = select(User).where(User.telegram_id == telegram_id)
    res = await db.execute(stmt)
    user_obj = res.scalar_one_or_none()
    if not user_obj:
        user_obj = User(telegram_id=telegram_id, full_name="Telegram User")
        db.add(user_obj)
        try:
            await db.commit()
        except Exception:
            await db.rollback()
    return user_obj

class UrlTextScanRequest(BaseModel):
    text: str
    telegram_id: Optional[int] = None


@router.post("/url-or-text")
async def scan_url_or_text(payload: UrlTextScanRequest, db: AsyncSession = Depends(get_db)):
    """Havola yoki shubhali xabarni tekshirish."""
    result = await analyze_url_or_text(payload.text)

    # Natijani bazaga saqlash
    if payload.telegram_id:
        await ensure_db_user(db, payload.telegram_id)

        history_item = ScanHistory(
            user_telegram_id=payload.telegram_id,
            scan_type="url_or_text",
            target_name=result.get("target", payload.text[:100]),
            risk_score=float(result.get("risk_score", 0)),
            verdict=result.get("verdict", "safe"),
            summary_uz=result.get("summary_uz", ""),
            details_json=json.dumps(result, ensure_ascii=False)
        )
        db.add(history_item)
        await db.commit()

        # Agar xavfli bo'lsa (risk_score >= 70), oila a'zolariga avtomatik signal yuborish
        if result.get("risk_score", 0) >= 70:
            await notify_family_guardians(
                db=db,
                user_telegram_id=payload.telegram_id,
                target_name=result.get("target", "Havola"),
                risk_score=result.get("risk_score", 0),
                summary_uz=result.get("summary_uz", "")
            )

    return result


@router.post("/file")
async def scan_file(
    file: UploadFile = File(...),
    telegram_id: Optional[int] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """APK, rasm yoki shubhali fayllarni tekshirish."""
    file_bytes = await file.read()
    result = analyze_file_security(file.filename, file_bytes)

    if telegram_id:
        await ensure_db_user(db, telegram_id)

        history_item = ScanHistory(
            user_telegram_id=telegram_id,
            scan_type="file",
            target_name=file.filename,
            risk_score=float(result.get("risk_score", 0)),
            verdict=result.get("verdict", "safe"),
            summary_uz=result.get("summary_uz", ""),
            details_json=json.dumps(result, ensure_ascii=False)
        )
        db.add(history_item)
        await db.commit()

        if result.get("risk_score", 0) >= 70:
            await notify_family_guardians(
                db=db,
                user_telegram_id=telegram_id,
                target_name=file.filename,
                risk_score=result.get("risk_score", 0),
                summary_uz=result.get("summary_uz", "")
            )

    return result


@router.post("/contract")
async def scan_contract(
    file: Optional[UploadFile] = File(None),
    raw_text: Optional[str] = Form(None),
    telegram_id: Optional[int] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """Shartnomani rentgen tahlilidan o'tkazish (PDF, rasm yoki matn)."""
    filename = file.filename if file else "shartnoma_matni.txt"
    file_bytes = await file.read() if file else b""
    mime_type = file.content_type if file else "text/plain"

    result = await analyze_contract_file(
        filename=filename,
        file_bytes=file_bytes,
        mime_type=mime_type,
        raw_text=raw_text
    )

    if telegram_id:
        await ensure_db_user(db, telegram_id)

        # Shartnomada risk_score = 100 - overall_safety_score
        calc_risk = max(0, 100 - result.get("overall_safety_score", 60))

        history_item = ScanHistory(
            user_telegram_id=telegram_id,
            scan_type="contract",
            target_name=filename,
            risk_score=float(calc_risk),
            verdict=result.get("verdict", "suspicious"),
            summary_uz=result.get("summary_uz", ""),
            details_json=json.dumps(result, ensure_ascii=False)
        )
        db.add(history_item)
        await db.commit()

    return result


@router.post("/image")
async def scan_image(
    file: UploadFile = File(...),
    telegram_id: Optional[int] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """Vision AI: Soxta cheklar, SMS/Chat skrinshotlari va QR-kodlarni tekshirish."""
    from backend.security_engine.image_fraud_analyzer import analyze_fraud_image
    file_bytes = await file.read()
    result = await analyze_fraud_image(file.filename, file_bytes, mime_type=file.content_type)

    if telegram_id:
        await ensure_db_user(db, telegram_id)

        history_item = ScanHistory(
            user_telegram_id=telegram_id,
            scan_type="image_vision",
            target_name=result.get("title_uz", file.filename)[:120],
            risk_score=float(result.get("risk_score", 0)),
            verdict=result.get("verdict", "safe"),
            summary_uz=result.get("summary_uz", ""),
            details_json=json.dumps(result, ensure_ascii=False)
        )
        db.add(history_item)
        await db.commit()

        if result.get("risk_score", 0) >= 70:
            await notify_family_guardians(
                db=db,
                user_telegram_id=telegram_id,
                target_name=result.get("title_uz", "Xavfli Rasm"),
                risk_score=result.get("risk_score", 0),
                summary_uz=result.get("summary_uz", "")
            )

    return result

