from db import init_db, SessionLocal
from db import crud

def main():
    print("Initializing Database...")
    init_db()
    
    db = SessionLocal()
    
    try:
        tg_id = "123456"
        print(f"\nCreating/Fetching User: {tg_id}")
        user = crud.create_user(db, tg_id)
        print(f"   User ID in DB: {user.id}")

        # 新增監控地址
        test_addr = "0x7ca0b75e67e33c0014325b739a8d019c4fe445f0"
        print(f"\nAdding Monitor: {test_addr}")
        monitor, created = crud.add_monitor(db, tg_id, test_addr, "Main Vault")
        if created:
            print("   Created new monitor!")
        else:
            print("  Monitor already exists.")

        # 查詢該用戶的所有監控
        print(f"\nListing Monitors for {tg_id}:")
        monitors = crud.get_user_monitors(db, tg_id)
        for m in monitors:
            print(f"   - {m.name} ({m.safe_address}) | Threshold: {m.alert_threshold}%")

        # 模擬更新警報時間
        print(f"\nUpdating alert timestamp for monitor ID {monitor.id}")
        crud.update_last_alert(db, monitor.id)
        
        # 再次查詢確認時間變了
        updated_monitor = db.query(crud.Monitor).get(monitor.id)
        print(f"Last Alert Time: {updated_monitor.last_alert_at}")

    finally:
        # 記得關閉連線
        db.close()

if __name__ == "__main__":
    main()