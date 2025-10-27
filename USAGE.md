# 使用指南

## 快速開始

### 1. 設定環境

建立 `.env` 檔案：

```env
DATABASE_URL=postgresql://username:password@localhost:5432/fleet_system
```

### 2. 安裝依賴

```bash
pip install -r requirements.txt
```

### 3. 初始化資料庫

```bash
python create_tables.py
```

### 4. 啟動應用程式

```bash
uvicorn main:app --reload
```

瀏覽 `http://localhost:8000/docs` 查看 API 文件。

## 常見使用場景

### 場景 1: 新增車輛與基本資料

#### 步驟 1: 建立供應商

```bash
curl -X POST "http://localhost:8000/api/v1/vendors/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "富邦產險",
    "category": "insurance",
    "contact": "02-1234-5678"
  }'
```

#### 步驟 2: 建立車輛

```bash
curl -X POST "http://localhost:8000/api/v1/vehicles/" \
  -H "Content-Type: application/json" \
  -d '{
    "plate_no": "ABC-1234",
    "vin": "1HGCM82633A123456",
    "make": "Toyota",
    "model": "Camry",
    "year": 2023,
    "powertrain": "油電混合",
    "displacement_cc": 2500,
    "seats": 5,
    "vehicle_type": "car",
    "acquired_on": "2023-01-01",
    "status": "active"
  }'
```

#### 步驟 3: 上傳強制險

```bash
curl -X POST "http://localhost:8000/api/v1/vehicles/1/documents/" \
  -F "doc_type=insurance" \
  -F "issued_on=2024-01-01" \
  -F "expires_on=2025-01-01" \
  -F "tags=2024年強制險" \
  -F "file=@insurance.pdf"
```

#### 步驟 4: 建立保險紀錄

```bash
curl -X POST "http://localhost:8000/api/v1/insurances/" \
  -H "Content-Type: application/json" \
  -d '{
    "vehicle_id": 1,
    "policy_type": "CALI",
    "policy_no": "POL-2024-001",
    "insurer_id": 1,
    "effective_on": "2024-01-01",
    "expires_on": "2025-01-01",
    "premium": 3500.00
  }'
```

### 場景 2: 借車流程

#### 步驟 1: 建立借車申請

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

系統會自動檢查：
- 車輛是否可用（狀態為 active）
- 強制險是否有效
- 是否有時間衝突

#### 步驟 2: 回報行程（還車）

```bash
curl -X POST "http://localhost:8000/api/v1/reservations/1/trip/" \
  -H "Content-Type: application/json" \
  -d '{
    "vehicle_id": 1,
    "driver_id": 1,
    "odometer_start": 10000,
    "odometer_end": 10200,
    "fuel_liters": 15.5,
    "notes": "車輛正常"
  }'
```

### 場景 3: 維護與工單

#### 建立保養計畫

```bash
curl -X POST "http://localhost:8000/api/v1/vehicles/1/maintenance-plans/" \
  -H "Content-Type: application/json" \
  -d '{
    "policy_name": "原廠定保",
    "interval_km": 10000,
    "next_due_odometer": 11000,
    "interval_months": 12,
    "next_due_date": "2025-12-31"
  }'
```

#### 建立工單

```bash
curl -X POST "http://localhost:8000/api/v1/work-orders/" \
  -H "Content-Type: application/json" \
  -d '{
    "vehicle_id": 1,
    "type": "maintenance",
    "status": "pending_approval",
    "vendor_id": 2,
    "scheduled_on": "2025-01-25",
    "notes": "更換機油、機油濾芯",
    "odometer_at_service": 10500,
    "cost_amount": 1500.00
  }'
```

### 場景 4: 合規管理

#### 查詢即將到期的項目

```bash
curl "http://localhost:8000/api/v1/analytics/compliance-report?days_ahead=30"
```

回應範例：
```json
{
  "report_date": "2025-01-15",
  "days_ahead": 30,
  "total_vehicles": 5,
  "compliant_vehicles": 3,
  "compliance_rate": 60.0,
  "items": [
    {
      "vehicle_id": 1,
      "plate_no": "ABC-1234",
      "issues": ["強制險將於 2025-02-01 到期"]
    }
  ]
}
```

#### 建立違規紀錄

```bash
curl -X POST "http://localhost:8000/api/v1/violations/" \
  -H "Content-Type: application/json" \
  -d '{
    "vehicle_id": 1,
    "driver_id": 1,
    "law_ref": "道路交通管理處罰條例 第56條第1項",
    "violation_date": "2025-01-15T10:30:00+08:00",
    "amount": 600.00,
    "points": 1,
    "status": "open"
  }'
```

#### 上傳罰單影像

```bash
curl -X POST "http://localhost:8000/api/v1/vehicles/1/documents/" \
  -F "doc_type=fine" \
  -F "issued_on=2025-01-15" \
  -F "tags=違規停車罰單" \
  -F "file=@ticket.jpg"
```

### 場景 5: 分析報表

#### 車輛使用率

```bash
curl "http://localhost:8000/api/v1/analytics/vehicle-utilization/1?start_date=2025-01-01&end_date=2025-01-31"
```

#### 每公里成本

```bash
curl "http://localhost:8000/api/v1/analytics/cost-per-km/1?start_date=2025-01-01&end_date=2025-01-31"
```

#### 違規統計

```bash
curl "http://localhost:8000/api/v1/analytics/violation-stats?start_date=2025-01-01&end_date=2025-01-31"
```

## 資料匯入

### 匯入員工資料

```python
from database import SessionLocal
import import_data

db = SessionLocal()
try:
    count, errors = import_data.import_employees_from_csv(db, "employees.csv")
    print(f"成功匯入 {count} 筆，錯誤: {len(errors)} 筆")
finally:
    db.close()
```

## 背景排程

系統會自動在每天凌晨 4:00 檢查即將到期的項目：
- 保險到期提醒
- 定檢到期提醒
- 排氣定檢到期提醒

## API 認證（暫時）

目前系統使用簡易的身份驗證：
- 所有操作預設由 ID=1 的員工執行
- 系統會自動建立 "System Admin" 帳號（如果不存在）

未來將實作：
- JWT Token 認證
- SSO 單點登入
- RBAC 權限控制

## 疑難排解

### 問題: 資料庫連線失敗

檢查 `.env` 檔案中的 `DATABASE_URL` 是否正確。

### 問題: 檔案上傳失敗

確認 `uploads/` 目錄存在且有寫入權限。

### 問題: 預約被拒絕

檢查：
1. 車輛強制險是否有效
2. 車輛狀態是否為 active
3. 是否有時間衝突

### 問題: 排程器未執行

檢查 `scheduler.py` 是否正確載入，查看應用程式啟動日誌。

## 下一步

1. 閱讀 `README.md` 了解完整功能
2. 瀏覽 `http://localhost:8000/docs` 查看所有 API
3. 參考 `models.py` 了解資料結構
4. 根據需求擴充功能


