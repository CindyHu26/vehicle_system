# 公務車與機車管理系統

## 系統概述

這是一個基於 Python + FastAPI + PostgreSQL 的公務車與機車管理系統，支援台灣法規情境（牌照稅、燃料費、強制險、定檢、違規與駕駛積點）。

## 已實現功能

### 1. 車輛管理
- ✅ 車輛主檔（四輪/二輪）
- ✅ 文件上傳（行照、保險、定檢證、罰單等）
- ✅ 備品管理（安全帽、鎖具等）
- ✅ 車輛狀態管理

### 2. 借車與排程
- ✅ 借車申請
- ✅ 衝突檢測
- ✅ 合規性檢查（強制險、定檢）
- ✅ 行程回報
- ✅ 里程與油耗回報

### 3. 維護與工單
- ✅ 保養計畫
- ✅ 工單管理（保養、維修、清潔等）
- ✅ 供應商管理
- ✅ 工單狀態追蹤

### 4. 合規與稅保
- ✅ 保險管理（強制險、任意險）
- ✅ 稅費管理（牌照稅、燃料費）
- ✅ 檢驗管理（四輪定檢、機車排氣）
- ✅ 違規紀錄（罰單、積點）

### 5. 稽核與分析
- ✅ 不可竄改稽核軌跡
- ✅ 車輛使用率分析
- ✅ 每公里成本分析
- ✅ 合規性報表
- ✅ 違規統計

### 6. 自動化
- ✅ 到期提醒（保險、定檢）
- ✅ 背景排程器

## 系統要求

- Python 3.13+
- PostgreSQL 17
- Windows 11 (或任何支援 Python + PostgreSQL 的環境)

## 安裝步驟

### 1. 安裝 Python 套件

```bash
pip install -r requirements.txt
```

### 2. 設定資料庫

在 `.env` 檔案中設定資料庫連線：

```
DATABASE_URL=postgresql://username:password@localhost:5432/fleet_system
```

### 3. 建立資料表

```bash
python create_tables.py
```

### 4. 啟動應用程式

```bash
uvicorn main:app --reload
```

應用程式將在 `http://localhost:8000` 啟動。

## API 文件

啟動後可瀏覽：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 主要 API 端點

### 車輛管理
- `POST /api/v1/vehicles/` - 建立車輛
- `GET /api/v1/vehicles/` - 查詢車輛列表
- `GET /api/v1/vehicles/{vehicle_id}` - 查詢單一車輛
- `PUT /api/v1/vehicles/{vehicle_id}` - 更新車輛
- `DELETE /api/v1/vehicles/{vehicle_id}` - 刪除車輛

### 員工管理
- `POST /api/v1/employees/` - 建立員工
- `GET /api/v1/employees/` - 查詢員工列表
- `GET /api/v1/employees/{employee_id}` - 查詢單一員工

### 借車申請
- `POST /api/v1/reservations/` - 建立借車申請
- `GET /api/v1/reservations/` - 查詢預約列表
- `PATCH /api/v1/reservations/{reservation_id}/` - 更新預約狀態
- `POST /api/v1/reservations/{reservation_id}/trip/` - 回報行程

### 工單管理
- `POST /api/v1/work-orders/` - 建立工單
- `GET /api/v1/work-orders/{work_order_id}` - 查詢單一工單
- `GET /api/v1/vehicles/{vehicle_id}/work-orders/` - 查詢車輛的所有工單

### 合規管理
- `POST /api/v1/insurances/` - 建立保險
- `POST /api/v1/taxes-fees/` - 建立稅費
- `POST /api/v1/inspections/` - 建立檢驗
- `POST /api/v1/violations/` - 建立違規

### 文件管理
- `POST /api/v1/vehicles/{vehicle_id}/documents/` - 上傳文件
- `GET /api/v1/vehicles/{vehicle_id}/documents/` - 查詢車輛文件
- `GET /files/{file_path}` - 下載文件

### 分析報表
- `GET /api/v1/analytics/vehicle-utilization/{vehicle_id}` - 車輛使用率
- `GET /api/v1/analytics/cost-per-km/{vehicle_id}` - 每公里成本
- `GET /api/v1/analytics/compliance-report` - 合規性報表
- `GET /api/v1/analytics/violation-stats` - 違規統計

## 使用範例

### 1. 建立員工

```bash
curl -X POST "http://localhost:8000/api/v1/employees/" \
  -H "Content-Type: application/json" \
  -d '{
    "emp_no": "E001",
    "name": "張三",
    "dept_name": "業務部",
    "license_class": "普通小型車",
    "status": "active"
  }'
```

### 2. 建立車輛

```bash
curl -X POST "http://localhost:8000/api/v1/vehicles/" \
  -H "Content-Type: application/json" \
  -d '{
    "plate_no": "ABC-1234",
    "make": "Toyota",
    "model": "Camry",
    "year": 2023,
    "displacement_cc": 2500,
    "vehicle_type": "car",
    "status": "active"
  }'
```

### 3. 建立借車申請

```bash
curl -X POST "http://localhost:8000/api/v1/reservations/" \
  -H "Content-Type: application/json" \
  -d '{
    "requester_id": 1,
    "vehicle_id": 1,
    "purpose": "business",
    "start_ts": "2025-01-20T09:00:00+08:00",
    "end_ts": "2025-01-20T18:00:00+08:00",
    "destination": "桃園機場"
  }'
```

### 4. 回報行程

```bash
curl -X POST "http://localhost:8000/api/v1/reservations/1/trip/" \
  -H "Content-Type: application/json" \
  -d '{
    "vehicle_id": 1,
    "driver_id": 1,
    "odometer_start": 10000,
    "odometer_end": 10200,
    "fuel_liters": 15.5,
    "notes": "正常"
  }'
```

## 系統架構

```
fleet_system/
├── main.py              # FastAPI 主應用程式
├── models.py            # SQLAlchemy 資料模型
├── schemas.py           # Pydantic 資料驗證
├── crud.py              # 資料庫操作 (CRUD)
├── database.py          # 資料庫連線設定
├── analytics.py         # 分析與報表功能
├── scheduler.py         # 背景排程任務
├── import_data.py       # 資料匯入功能
├── utils.py             # 工具函式
├── dependencies.py      # FastAPI 依賴注入
├── create_tables.py     # 建立資料表
└── uploads/             # 上傳檔案存放目錄
```

## 資料模型

### 核心表
- `employees` - 員工
- `vehicles` - 車輛
- `reservations` - 借車申請
- `trips` - 行程回報

### 維護相關
- `vendors` - 供應商
- `maintenance_plans` - 保養計畫
- `work_orders` - 工單

### 合規相關
- `insurances` - 保險
- `taxes_fees` - 稅費
- `inspections` - 檢驗
- `violations` - 違規

### 文件與稽核
- `vehicle_documents` - 車輛文件
- `vehicle_assets` - 備品資產
- `audit_logs` - 稽核軌跡
- `privacy_access_logs` - 隱私存取紀錄

## 未來規劃

- [ ] 實現 OCR 功能（罰單自動識別）
- [ ] 整合通知系統（Email/Line Notify）
- [ ] 實作權限管理（RBAC）
- [ ] 新增資料匯入功能 (CSV/Excel)
- [ ] 整合 GPS/OBD-II 資料
- [ ] 建立前端介面
- [ ] 實現單點登入 (SSO)

## 授權

Copyright © 2025

## 聯絡資訊

如有問題或建議，歡迎聯絡開發團隊。


