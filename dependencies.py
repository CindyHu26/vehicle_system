# 檔案名稱: dependencies.py
from fastapi import Depends
from sqlalchemy.orm import Session
import crud
import models
from database import SessionLocal

def get_db():
    """ 
    (這是從 main.py 複製過來的)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_actor_id(db: Session = Depends(get_db)) -> int:
    """
    (暫時的 Dependency) 模擬取得目前登入的使用者 ID。

    在我們建置步驟 8 (SSO/JWT 身分驗證) 之前，
    我們先假設操作者永遠是系統中的第一位員工 (ID: 1)。

    如果員工 ID: 1 不存在，我們會自動建立一個 "System Admin" 帳號。
    """
    
    # 嘗試取得 ID: 1 的員工
    # 注意：我們用 crud.get_employee_by_emp_no 來避免循環 import
    # 但這裡用 get_employee 較單純，我們先確保 crud.py 裡有
    
    # 檢查 ID 1 是否存在
    db_actor = db.query(models.Employee).filter(models.Employee.id == 1).first()
    
    if db_actor:
        return db_actor.id
    else:
        # 如果 ID 1 不存在 (例如全新的資料庫)，
        # 自動建立一個 "System Admin" 員工 (ID 會是 1)
        print("注意：找不到 ID: 1 的員工，將自動建立 'System Admin'...")
        
        # 檢查 emp_no "ADMIN" 是否存在，避免重複
        admin_user = db.query(models.Employee).filter(models.Employee.emp_no == "ADMIN").first()
        if admin_user:
            return admin_user.id

        try:
            db_admin = models.Employee(
                emp_no="ADMIN",
                name="System Admin",
                dept_name="IT",
                license_class="N/A",
                status=models.EmployeeStatusEnum.active
            )
            db.add(db_admin)
            db.commit()
            db.refresh(db_admin)
            print(f"已建立 'System Admin'，ID 為: {db_admin.id}")
            return db_admin.id
        except Exception as e:
            db.rollback()
            print(f"建立 Admin 失敗: {e}")
            # 這是最後防線，如果連 Admin 都建不起來，就回傳 0
            return 0