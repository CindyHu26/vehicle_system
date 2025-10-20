# 檔案名稱: database.py
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# --- 資料庫連線設定 ---
# 請將 'YOUR_USER'、'YOUR_PASSWORD' 和 'YOUR_DB_NAME' 換成您自己的設定
# 格式: postgresql+psycopg2://使用者名稱:密碼@主機:埠號/資料庫名稱
# 由於是在本機 (Windows 11)，主機通常是 'localhost'，埠號是 '5432'
DATABASE_URL = "postgresql+psycopg2://postgres:Ever1930@localhost:5432/vehicle_management"

# 建立資料庫引擎
# pool_pre_ping=True 確保每次從連線池取用連線前，都會檢查其有效性
engine = sqlalchemy.create_engine(DATABASE_URL, pool_pre_ping=True)

# 建立 SessionLocal 工廠
# 這將是我們未來與資料庫互動的主要入口
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 建立一個基礎類別 (Base)
# 我們所有的模型 (Models) 都將繼承這個類別
Base = declarative_base()

print("資料庫連線設定 (database.py) 載入完成。")

def get_db():
    """
    (未來給 FastAPI 用的)
    一個 dependency-injection 用的 generator，
    確保資料庫 session 在請求結束後會被關閉。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()