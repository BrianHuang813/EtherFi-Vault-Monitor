from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    # Telegram User ID (注意：雖然是數字，存成 String 比較保險，避免溢位)
    telegram_id = Column(String, unique=True, index=True, nullable=False)
    is_premium = Column(Boolean, default=False) # 預留給付費功能
    created_at = Column(DateTime, default=datetime.now)

    # 建立關聯：一個 User 可以有多個 Monitors
    monitors = relationship("Monitor", back_populates="owner")

    def __repr__(self):
        return f"<User(tg_id={self.telegram_id})>"

class Monitor(Base):
    __tablename__ = "monitors"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 被監控的 Safe 地址 (存成 Checksum 格式)
    safe_address = Column(String, nullable=False)
    # 自訂名稱 (例如: "我的主錢包")
    name = Column(String, default="My Safe")
    
    # 設定：LTV 超過多少通知 (預設 90%)
    alert_threshold = Column(Float, default=90.0)
    
    # 狀態追蹤
    is_active = Column(Boolean, default=True) # 用戶可以暫停監控
    last_alert_at = Column(DateTime, nullable=True) # 上次發警報時間

    # 關聯回 User
    owner = relationship("User", back_populates="monitors")

    def __repr__(self):
        return f"<Monitor(addr={self.safe_address}, threshold={self.alert_threshold})>"