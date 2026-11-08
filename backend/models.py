from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, BigInteger, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String(128), nullable=True)
    full_name = Column(String(256), nullable=True)
    role = Column(String(32), default="user")  # 'owner', 'admin', 'user'
    active_mode = Column(String(32), default="owner")  # 'owner' yoki 'user' (owner uchun rejim almashtirish)
    is_banned = Column(Boolean, default=False)
    risk_alerts_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)

    # Relationships
    scans = relationship("ScanHistory", back_populates="user", cascade="all, delete-orphan")


class FamilyLink(Base):
    __tablename__ = "family_links"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # The member being protected (e.g. parent)
    parent_telegram_id = Column(BigInteger, index=True, nullable=False)
    # The guardian receiving alerts (e.g. child)
    child_telegram_id = Column(BigInteger, index=True, nullable=False)
    relationship_name = Column(String(100), default="Yaqin insonim")
    created_at = Column(DateTime, default=datetime.utcnow)


class ScanHistory(Base):
    __tablename__ = "scan_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_telegram_id = Column(BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE"), index=True, nullable=False)
    scan_type = Column(String(50), nullable=False)  # 'url', 'text', 'file', 'contract'
    target_name = Column(String(512), nullable=False) # e.g. "click-bonus.uz" or "shartnoma.pdf"
    risk_score = Column(Float, default=0.0)
    verdict = Column(String(50), default="safe")  # 'safe', 'suspicious', 'dangerous'
    summary_uz = Column(Text, nullable=False)
    details_json = Column(Text, nullable=True)  # JSON formatted full diagnostics
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="scans")


class CommunityBlacklist(Base):
    __tablename__ = "community_blacklist"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    domain_or_pattern = Column(String(256), unique=True, index=True, nullable=False)
    category = Column(String(64), default="phishing") # phishing, fake_lottery, predatory_loan, apk_trojan
    reason = Column(Text, nullable=False)
    reported_by_telegram_id = Column(BigInteger, nullable=True)
    status = Column(String(50), default="verified") # pending, verified
    created_at = Column(DateTime, default=datetime.utcnow)


class CardBlacklist(Base):
    """Firibgarlarga tegishli bank kartalari qora ro'yxati."""
    __tablename__ = "card_blacklist"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    card_number = Column(String(32), unique=True, index=True, nullable=False) # Masalan: "8600123456789012"
    bank_name = Column(String(128), nullable=True)
    owner_name = Column(String(256), nullable=True)
    reason = Column(Text, nullable=False)
    report_count = Column(Integer, default=1)
    status = Column(String(50), default="verified")
    created_at = Column(DateTime, default=datetime.utcnow)


class AdminAuditLog(Base):
    """Admin va Owner amallari qaydnomasi."""
    __tablename__ = "admin_audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    admin_telegram_id = Column(BigInteger, index=True, nullable=False)
    action = Column(String(128), nullable=False) # e.g. "add_admin", "remove_admin", "broadcast", "ban_user"
    target = Column(String(256), nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class BroadcastMessage(Base):
    """Barcha foydalanuvchilarga yuborilgan e'lonlar arxivi."""
    __tablename__ = "broadcast_messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    sender_telegram_id = Column(BigInteger, nullable=False)
    text = Column(Text, nullable=False)
    total_recipients = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class SystemConfig(Base):
    """Tizim sozlamalari va AI API kalitlarini doimiy saqlash."""
    __tablename__ = "system_config"

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
