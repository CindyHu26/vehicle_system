# 檔案名稱: utils.py
import os
import shutil
import hashlib
from fastapi import UploadFile
from pathlib import Path # 用於處理路徑

# 定義上傳檔案的儲存基底路徑
UPLOAD_DIRECTORY = Path("uploads") 

# 確保目錄存在
UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)

def save_upload_file(upload_file: UploadFile) -> tuple[str, str]:
    """
    儲存上傳的檔案到本地，並計算 SHA-256 雜湊值。

    Args:
        upload_file: FastAPI 的 UploadFile 物件。

    Returns:
        一個 tuple 包含 (儲存的檔案路徑字串, SHA-256 雜湊值字串)。
        
    Raises:
        IOError: 如果檔案儲存失敗。
        Exception: 其他計算雜湊值時的錯誤。
    """
    sha256_hash = hashlib.sha256()
    
    # 組合檔案儲存路徑 (簡單起見，直接存放在 uploads/檔名)
    # 警告：如果檔名重複，舊檔案會被覆蓋！
    # 更好的做法是使用 UUID 或時間戳重新命名
    file_path = UPLOAD_DIRECTORY / upload_file.filename
    
    try:
        # 使用 shutil.copyfileobj 分塊讀取和寫入，適合大檔案
        with open(file_path, "wb") as buffer, upload_file.file as source_file:
            while True:
                chunk = source_file.read(8192) # 讀取 8KB
                if not chunk:
                    break
                sha256_hash.update(chunk) # 更新雜湊值
                buffer.write(chunk) # 寫入檔案
                
        # 重置檔案指標，以便 FastAPI 可以再次讀取 (雖然通常不需要)
        upload_file.file.seek(0) 
        
        # 取得十六進位的雜湊值字串
        hex_digest = sha256_hash.hexdigest()
        
        # 回傳相對路徑字串 (方便儲存到資料庫)
        # 注意：Windows 路徑是反斜線 '\'，URL 通常用正斜線 '/'
        # file_path.as_posix() 可以轉換成 '/'
        return file_path.as_posix(), hex_digest

    except IOError as e:
        print(f"儲存檔案失敗: {e}")
        # 如果儲存失敗，可能需要刪除不完整的檔案
        if file_path.exists():
            file_path.unlink()
        raise IOError(f"無法儲存檔案: {upload_file.filename}")
    except Exception as e:
        print(f"處理檔案時發生錯誤: {e}")
        if file_path.exists():
            file_path.unlink()
        raise Exception(f"處理檔案時出錯: {upload_file.filename}")