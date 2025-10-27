# 快速開始指南

本指南將協助您快速啟動並執行公務車管理系統。

## 系統架構

```
公務車管理系統/
├── 後端 (FastAPI + PostgreSQL)
│   ├── main.py           # API 主程式
│   ├── models.py         # 資料模型
│   ├── crud.py           # 資料庫操作
│   └── analytics.py      # 分析功能
└── 前端 (Next.js + React)
    ├── app/              # 頁面
    ├── components/        # 元件
    └── lib/              # 工具
```

## 前置需求

- **Python 3.13+**
- **PostgreSQL 17**
- **Node.js 18+**
- **npm 或 yarn**

## 步驟 1: 設定資料庫

### 1.1 安裝 PostgreSQL

確保 PostgreSQL 已安裝並正在執行。

### 1.2 建立資料庫

```bash
# 進入 PostgreSQL
psql -U postgres

# 建立資料庫
CREATE DATABASE fleet_system;

# 退出
\q
```

### 1.3 設定環境變數

在專案根目錄建立 `.env` 檔案：

```env
DATABASE_URL=postgresql://username:password@localhost:5432/fleet_system
```

**重要：** 將 `username` 和 `password` 替換為您的實際資料庫帳密。

## 步驟 2: 安裝後端依賴

```bash
# 建立虛擬環境（可選）
python -m venv venv

# 啟動虛擬環境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安裝依賴
pip install -r requirements.txt
```

## 步驟 3: 初始化資料庫

```bash
python create_tables.py
```

您應該會看到：

```
資料表 'employees' 和 'vehicles' 已成功建立 (或已存在)！
```

## 步驟 4: 啟動後端

```bash
uvicorn main:app --reload
```

後端將在 `http://localhost:8000` 啟動。

您可以瀏覽以下網址：
- API 文件: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 步驟 5: 設定前端

### 5.1 進入前端目錄

```bash
cd frontend
```

### 5.2 安裝依賴

```bash
npm install
```

### 5.3 建立環境變數檔案

建立 `frontend/.env.local` 檔案：

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 5.4 啟動前端

```bash
npm run dev
```

前端將在 `http://localhost:3000` 啟動。

## 步驟 6: 測試系統

### 6.1 建立測試資料

使用 API 或前端介面建立測試資料：

**透過 API (Swagger UI)**
1. 瀏覽 http://localhost:8000/docs
2. 使用 POST 端點新增員工和車輛

**透過前端**
1. 瀏覽 http://localhost:3000
2. 在瀏覽器中使用開發者工具觀察 API 呼叫

### 6.2 測試功能

1. **儀表板** - 查看車輛總數與合規狀態
2. **車輛管理** - 查看車輛列表與詳情
3. **借車申請** - 查看借車記錄
4. **員工管理** - 查看員工資訊

## 常見問題

### Q: 資料庫連線失敗

**A:** 檢查：
1. PostgreSQL 是否正在執行
2. `.env` 中的 `DATABASE_URL` 是否正確
3. 資料庫帳號是否有權限

### Q: 前端無法連接後端

**A:** 檢查：
1. 後端是否在 `http://localhost:8000` 執行
2. `frontend/.env.local` 中的 URL 是否正確
3. 瀏覽器控制台是否有錯誤訊息

### Q: CORS 錯誤

**A:** 後端已在 `main.py` 中啟用 CORS。如果仍有問題，檢查 `allow_origins` 設定。

### Q: 前端頁面空白

**A:** 檢查：
1. 後端 API 是否正常回應
2. 瀏覽器控制台是否有錯誤
3. Network 標籤是否顯示 API 請求成功

## 下一步

1. 閱讀 [README.md](README.md) 了解完整功能
2. 閱讀 [USAGE.md](USAGE.md) 了解使用範例
3. 閱讀 [FRONTEND_SETUP.md](FRONTEND_SETUP.md) 了解前端開發
4. 閱讀 [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) 了解實作進度

## 開發建議

### 後端開發

- 使用 Swagger UI 測試 API
- 檢視 `crud.py` 了解資料庫操作
- 檢視 `models.py` 了解資料結構

### 前端開發

- 使用 React DevTools 除錯
- 檢視 `lib/api.ts` 了解 API 呼叫
- 檢視 `app/` 了解頁面結構

## 取得協助

如有問題，請：

1. 檢查錯誤訊息
2. 查看日誌輸出
3. 閱讀相關文件
4. 查看 GitHub Issues（如果有的話）

## 授權

Copyright © 2025


