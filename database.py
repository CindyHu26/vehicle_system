# 檔案名稱: database.py
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

import os
from dotenv import load_dotenv

load_dotenv()
# 程式碼從 os.getenv() 讀取環境變數，而不是寫死
DATABASE_URL = os.getenv("DATABASE_URL")

# 防呆機制：如果 .env 檔案遺失或忘記設定，程式會直接報錯提醒
if not DATABASE_URL:
    raise ValueError("找不到 'DATABASE_URL' 環境變數。請檢查您的 .env 檔案。")

# 建立資料庫引擎
engine = sqlalchemy.create_engine(DATABASE_URL, pool_pre_ping=True)

# 建立 SessionLocal 工廠
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 建立一個基礎類別 (Base)
Base = declarative_base()

print("資料庫連線設定 (database.py) 載入完成。 (已使用 .env)")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()