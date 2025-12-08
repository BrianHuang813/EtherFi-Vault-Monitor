import asyncio
from telegram import Update
from telegram.ext import ContextTypes

from logs.logger import setup_logger
from blockchain.fetcher import Fetcher
from db import SessionLocal
from db.crud import add_monitor, get_user_monitors, create_user, delete_monitor, get_all_active_monitors, update_last_alert

# 初始化 Logger
logger = setup_logger("bot_handlers", "./logs")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    回應 /start 指令。
    """
    await update.message.reply_text(
        "Ether.fi Cash Monitor Bot initialized.\n\n"
        "Commands:\n"
        "/add <address> - Monitor an address\n"
        "/list - View your monitored addresses\n"
        "/remove <address> - Stop monitoring an address\n"
        "This monitor checks LTV every hour and alerts you if it exceeds safe limits."
    )

async def add_address_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    處理 /add <address> 指令。
    
    流程：
    1. 驗證輸入參數。
    2. 使用 ThreadPoolExecutor 在背景執行區塊鏈查詢 (Blocking I/O)。
    3. 寫入資料庫。
    4. 回報結果。
    """
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # 1. 輸入驗證
    if not context.args:
        await update.message.reply_text("Usage: /add <0x_address>")
        return

    target_address = context.args[0]
    
    # 顯示打字中狀態，避免用戶以為機器人卡死
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    
    logger.info(f"User {user_id} requested to add address: {target_address}")

    db = SessionLocal()
    try:
        # 獲取當前的 asyncio 事件迴圈
        loop = asyncio.get_running_loop()
        
        # 2. 區塊鏈驗證 (關鍵修正：避免阻塞 Main Thread)
        # run_in_executor(None, ...) 會使用預設的 ThreadPoolExecutor
        # is_safe 是同步函式，必須丟到執行緒中跑，否則 Bot 會凍結
        is_valid_safe = await loop.run_in_executor(None, Fetcher.is_safe, target_address)

        if not is_valid_safe:
            logger.warning(f"Address {target_address} validation failed for user {user_id}")
            await update.message.reply_text(f"Address {target_address} is invalid or has no active position on Ether.fi Cash.")
            return

        # 3. 寫入資料庫 (DB 操作也是 Blocking I/O，同樣建議丟入 Executor)
        # 確保用戶存在
        await loop.run_in_executor(None, create_user, db, str(user_id)) 
        
        # 新增監控
        # 假設 add_monitor 內部有處理重複新增的邏輯
        await loop.run_in_executor(None, add_monitor, db, str(user_id), target_address)

        logger.info(f"Successfully added monitor for {target_address}")
        
        await update.message.reply_text(
            f"Success. Address {target_address} has been added to your watchlist.\n"
            f"LTV monitoring is now active."
        )

    except Exception as e:
        # 記錄完整錯誤堆疊以便除錯
        logger.error(f"Error in add_address_handler: {e}", exc_info=True)
        await update.message.reply_text("An internal error occurred while processing your request.")
    finally:
        db.close()

async def list_monitors_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    處理 /list 指令。
    
    流程：
    1. 從資料庫讀取該用戶的監控清單。
    2. 批次查詢區塊鏈上的最新 LTV。
    3. 格式化輸出。
    """
    user_id = update.effective_user.id
    
    db = SessionLocal()

    try:
        loop = asyncio.get_running_loop()

        # 1. 讀取 DB
        monitors = await loop.run_in_executor(None, get_user_monitors, db, user_id)

        if not monitors:
            await update.message.reply_text("You are not monitoring any addresses.")
            return

        await update.message.reply_text(f"Fetching data for {len(monitors)} addresses...")

        # 提取地址列表
        addresses = [m.safe_address for m in monitors]

        # 2. 批次查詢 LTV (使用 Multicall 避免多次請求)
        ltv_data = await loop.run_in_executor(None, Fetcher.get_ltv_batch, addresses)

        # 3. 格式化訊息
        message_lines = ["Your Watchlist:", ""]
        
        for addr, ltv_value in ltv_data.items():
            # 簡單的狀態標記 [SAFE], [WARN], [RISK]
            status = "[SAFE]"
            if ltv_value > 80: status = "[WARN]"
            if ltv_value > 90: status = "[RISK]"

            # 顯示地址前6後4碼
            short_addr = f"{addr[:6]}...{addr[-4:]}"
            message_lines.append(f"{status} {short_addr}: {ltv_value:.2f}% LTV")

        await update.message.reply_text("\n".join(message_lines))

    except Exception as e:
        logger.error(f"Error in list_monitors_handler: {e}", exc_info=True)
        await update.message.reply_text("Failed to retrieve your watchlist data.")
    finally:
        db.close()

async def remove_monitor_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    處理 /remove <address> 指令。
    
    流程：
    1. 驗證輸入參數。
    2. 從資料庫刪除監控。
    3. 回報結果。
    """
    user_id = update.effective_user.id
    
    # 1. 輸入驗證
    if not context.args:
        await update.message.reply_text("Usage: /remove <0x_address>")
        return

    target_address = context.args[0]
    logger.info(f"User {user_id} requested to remove address: {target_address}")

    db = SessionLocal()
    try:
        loop = asyncio.get_running_loop()
        
        # 2. 刪除監控
        deleted = await loop.run_in_executor(None, delete_monitor, db, str(user_id), target_address)

        if deleted:
            logger.info(f"Successfully removed monitor for {target_address}")
            await update.message.reply_text(
                f"Address {target_address} has been removed from your watchlist."
            )
        else:
            logger.warning(f"Address {target_address} not found for user {user_id}")
            await update.message.reply_text(
                f"Address {target_address} is not in your watchlist."
            )

    except Exception as e:
        logger.error(f"Error in remove_monitor_handler: {e}", exc_info=True)
        await update.message.reply_text("An internal error occurred while processing your request.")
    finally:
        db.close()