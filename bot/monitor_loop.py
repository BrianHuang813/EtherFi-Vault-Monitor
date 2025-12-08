import asyncio
from datetime import datetime
from telegram.ext import Application
from logs.logger import setup_logger
from blockchain.fetcher import Fetcher
from db import SessionLocal
from db.crud import get_all_active_monitors, update_last_alert

# 初始化 Logger
logger = setup_logger("monitor_loop", "./logs")

# 全域變數儲存 application 實例
app_instance = None

async def monitor_ltv_check():
    """
    後台監控迴圈：每 5 分鐘檢查一次所有監控地址的 LTV。
    
    邏輯：
    1. 從資料庫抓出所有 is_active = True 的監控。
    2. 批次查詢區塊鏈上的最新 LTV。
    3. 如果 LTV 超過警報閾值，發送警告。
    4. 更新上次警報時間。
    
    頻率：5 分鐘
    """
    if not app_instance:
        logger.warning("app_instance not set, skipping monitor check")
        return

    try:
        db = SessionLocal()
        monitors = get_all_active_monitors(db)

        if not monitors:
            logger.debug("No active monitors to check")
            db.close()
            return

        logger.info(f"Starting LTV check for {len(monitors)} monitors")

        # 按用戶分組監控地址
        user_monitors = {}
        for monitor in monitors:
            user_id = monitor.owner.telegram_id
            if user_id not in user_monitors:
                user_monitors[user_id] = []
            user_monitors[user_id].append(monitor)

        # 批次獲取所有地址的 LTV
        all_addresses = [m.safe_address for m in monitors]
        ltv_data = await asyncio.get_running_loop().run_in_executor(
            None, Fetcher.get_ltv_batch, all_addresses
        )

        # 檢查每個監控並發送警告
        for user_id, user_monitor_list in user_monitors.items():
            for monitor in user_monitor_list:
                addr = monitor.safe_address
                ltv = ltv_data.get(addr, -1.0)

                # 檢查是否超過閾值
                if ltv > monitor.alert_threshold:
                    try:
                        # 發送警告訊息
                        short_addr = f"{addr[:6]}...{addr[-4:]}"
                        message = (
                            f"⚠️ LTV Alert\n\n"
                            f"Address: {short_addr}\n"
                            f"Current LTV: {ltv:.2f}%\n"
                            f"Threshold: {monitor.alert_threshold}%\n\n"
                            f"Please take action to reduce your leverage."
                        )
                        
                        await app_instance.bot.send_message(
                            chat_id=int(user_id),
                            text=message
                        )
                        
                        logger.info(
                            f"Sent alert to user {user_id} for address {addr} "
                            f"(LTV: {ltv:.2f}%)"
                        )
                        
                        # 更新上次警報時間
                        update_last_alert(db, monitor.id)

                    except Exception as e:
                        logger.error(
                            f"Failed to send alert to user {user_id}: {e}",
                            exc_info=True
                        )
                else:
                    logger.debug(
                        f"Monitor {addr}: LTV {ltv:.2f}% (threshold: {monitor.alert_threshold}%)"
                    )

        db.close()
        logger.info(f"Completed LTV check at {datetime.utcnow().isoformat()}")

    except Exception as e:
        logger.error(f"Error in monitor_ltv_check: {e}", exc_info=True)


def setup_monitor_scheduler(application: Application):
    """
    設置監控迴圈排程。
    每 5 分鐘執行一次 LTV 檢查。
    
    Args:
        application: Telegram Application 實例
    """
    global app_instance
    app_instance = application

    # 使用 application 的 job_queue 來排程任務
    # 5 分鐘 = 300 秒
    job_queue = application.job_queue
    job_queue.run_repeating(
        callback=_scheduler_callback,
        interval=3600,  # 1 小時
        first=30,      # 延遲 30 秒後開始執行（讓機器人完全初始化）
        name="ltv_monitor_loop"
    )

    logger.info("LTV monitor scheduler set up (1 hour interval)")


async def _scheduler_callback(context):
    """
    APScheduler 回調函數包裝器，用於在 job_queue 中執行非同步任務。
    """
    try:
        await monitor_ltv_check()
    except Exception as e:
        logger.error(f"Scheduler callback error: {e}", exc_info=True)
