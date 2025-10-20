# 檔案名稱: create_tables.py
from database import engine, Base
import models # 匯入 models.py 確保所有模型都被載入

def main():
    print("開始建立資料表...")
    
    try:
        # Base.metadata.create_all() 會檢查資料庫中是否已存在同名資料表
        # 如果不存在，它會建立新的資料表
        # 如果已存在，它不會更新或刪除它們 (這是未來 Alembic 要做的事)
        Base.metadata.create_all(bind=engine)
        
        print("=" * 30)
        print("資料表 'employees' 和 'vehicles' 已成功建立 (或已存在)！")
        print("=" * 30)
        print("\n您現在可以執行下一步：開始編寫 API 來新增資料。")
        
    except Exception as e:
        print(f"建立資料表時發生錯誤: {e}")

if __name__ == "__main__":
    main()