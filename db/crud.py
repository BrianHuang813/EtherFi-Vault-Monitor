from sqlalchemy.orm import Session
from db.models import User, Monitor
from datetime import datetime

# --- User 操作 ---

def get_user_by_tg_id(db: Session, telegram_id: str):
    return db.query(User).filter(User.telegram_id == str(telegram_id)).first()

def create_user(db: Session, telegram_id: str):
    """如果用戶不存在就建立，存在就回傳舊的"""
    user = get_user_by_tg_id(db, telegram_id)
    if user:
        return user
    
    new_user = User(telegram_id=str(telegram_id))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# --- Monitor 操作 ---

def add_monitor(db: Session, telegram_id: str, address: str, name: str = "My Safe"):
    """為用戶新增一個監控地址"""
    # 1. 確保用戶存在
    user = create_user(db, telegram_id)
    
    # 2. 檢查是否已經監控過這個地址 (避免重複)
    existing = db.query(Monitor).filter(
        Monitor.user_id == user.id,
        Monitor.safe_address == address
    ).first()
    
    if existing:
        return existing, False # False 代表沒新增(已存在)

    # 3. 新增監控
    new_monitor = Monitor(
        user_id=user.id,
        safe_address=address,
        name=name,
        alert_threshold=80.0 # 預設 80%
    )
    db.add(new_monitor)
    db.commit()
    db.refresh(new_monitor)
    return new_monitor, True # True 代表新增成功

def get_user_monitors(db: Session, telegram_id: str):
    """取得某個用戶的所有監控"""
    user = get_user_by_tg_id(db, telegram_id)
    if not user:
        return []
    return user.monitors

def get_all_active_monitors(db: Session):
    """[核心] 給 Monitor Loop 用的：抓出所有需要檢查的地址"""
    # 我們只抓 is_active = True 的
    return db.query(Monitor).filter(Monitor.is_active == True).all()

def update_last_alert(db: Session, monitor_id: int):
    """更新上次警報時間 (避免重複發送)"""
    monitor = db.query(Monitor).filter(Monitor.id == monitor_id).first()
    if monitor:
        monitor.last_alert_at = datetime.utcnow()
        db.commit()

def delete_monitor(db: Session, telegram_id: str, address: str):
    """刪除監控"""
    user = get_user_by_tg_id(db, telegram_id)
    if not user:
        return False
        
    monitor = db.query(Monitor).filter(
        Monitor.user_id == user.id,
        Monitor.safe_address == address
    ).first()
    
    if monitor:
        db.delete(monitor)
        db.commit()
        return True
    return False