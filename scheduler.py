# 檔案名稱: scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from database import SessionLocal
import crud
import logging
from datetime import datetime, timezone, timedelta

# 設定日誌
logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.INFO)

# --- 排程任務定義 ---

def check_upcoming_expirations_job():
    """
    (排程任務) 掃描即將到期的項目
    規格書 4.9 / 7.
    """
    print(f"\n[Scheduler Job] 執行 'check_upcoming_expirations_job' 於 {datetime.now()}...")
    
    db: Session | None = None
    try:
        # 排程任務必須自己建立 DB Session
        db = SessionLocal()
        
        # 查詢未來 30 天內到期的項目
        results = crud.get_items_expiring_soon(db, days_ahead=30)
        
        # --- 模擬通知 (Email/Line/Slack) ---
        
        if not results["insurances"] and not results["inspections"] and not results["emissions"]:
            print("[Scheduler Job] ... 檢查完畢，未來 30 天內無到期項目。")
            return

        if results["insurances"]:
            print(f"[Scheduler Job] !!! 發現 {len(results['insurances'])} 筆即將到期的保險:")
            for item in results["insurances"]:
                print(f"  - [保險] 車號: {item.vehicle.plate_no}, 類型: {item.policy_type.name}, 到期日: {item.expires_on}")
        
        if results["inspections"]:
            print(f"[Scheduler Job] !!! 發現 {len(results['inspections'])} 筆即將到期的(四輪)定檢:")
            for item in results["inspections"]:
                print(f"  - [定檢] 車號: {item.vehicle.plate_no}, 下次應檢日: {item.next_due_date}")

        if results["emissions"]:
            print(f"[Scheduler Job] !!! 發現 {len(results['emissions'])} 筆即將到期的(機車)排氣定檢:")
            for item in results["emissions"]:
                print(f"  - [排氣] 車號: {item.vehicle.plate_no}, 下次應檢日: {item.next_due_date}")

        print(f"[Scheduler Job] 任務完成。\n")

    except Exception as e:
        print(f"[Scheduler Job] 執行任務時發生錯誤: {e}")
    finally:
        if db:
            db.close()


# --- 排程器設定 ---

# 建立一個背景排程器
scheduler = BackgroundScheduler(timezone="Asia/Taipei")

def start_scheduler():
    """
    啟動排程器並加入任務
    """
    print("正在啟動排程器 (Scheduler)...")
    
    # (清空可能存在的舊任務)
    scheduler.remove_all_jobs()
    
    # (!! 測試用 !!)
    # 為了方便測試，我們先設定「每 1 分鐘」執行一次
    # scheduler.add_job(
    #     check_upcoming_expirations_job,
    #     trigger='interval',
    #     minutes=1,
    #     id='check_expirations_interval'
    # )
    
    # (!! 正式用 !!)
    # 規格書 4.9: 到期掃描 (我們設定每天凌晨 4 點執行)
    scheduler.add_job(
        check_upcoming_expirations_job,
        # 'cron' 觸發器，使用 crontab 語法
        # (分 時 日 月 週)
        trigger=CronTrigger(hour=4, minute=0, day_of_week='*'),
        id='check_expirations_daily_cron',
        replace_existing=True
    )
    
    try:
        scheduler.start()
        print("排程器已啟動。")
    except Exception as e:
        print(f"啟動排程器失敗: {e}")

def stop_scheduler():
    """
    安全關閉排程器
    """
    print("正在關閉排程器 (Scheduler)...")
    scheduler.shutdown()
    print("排程器已關閉。")