# 檔案名稱: main.py
from fastapi import FastAPI, Depends, HTTPException, Request, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from pathlib import Path

import crud
import models
import schemas
from database import SessionLocal, engine
from dependencies import get_db, get_current_actor_id

import utils
import analytics
import import_data

from fastapi.responses import FileResponse
import mimetypes

# 匯入排程器
from scheduler import start_scheduler, stop_scheduler, check_upcoming_expirations_job

app = FastAPI(
    title="公務車與機車管理系統 API",
    description="規格書 v0.2 實作",
    version="0.2.0"
)

# 啟用 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- FastAPI 啟動與關閉事件 ---
@app.on_event("startup")
async def app_startup():
    """
    API 伺服器啟動時，執行此函式
    """
    print("應用程式啟動中...")
    # 啟動背景排程器
    start_scheduler()
    
    # (!!! 測試用 !!!)
    # 為了立刻看到效果，我們在啟動時「手動」觸發一次任務
    print("正在手動觸發一次 'check_upcoming_expirations_job'...")
    check_upcoming_expirations_job()
    

@app.on_event("shutdown")
async def app_shutdown():
    """
    API 伺服器關閉時 (e.g., Ctrl+C)，執行此函式
    """
    print("應用程式關閉中...")
    # 安全關閉排程器
    stop_scheduler()

models.Base.metadata.create_all(bind=engine)

# --- Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- API Endpoints (API 路由) ---
# --- Employees API ---
@app.post("/api/v1/employees/", response_model=schemas.Employee, summary="建立新員工")
def create_employee_api(employee: schemas.EmployeeCreate, db: Session = Depends(get_db)):
    db_employee = crud.get_employee_by_emp_no(db, emp_no=employee.emp_no)
    if db_employee:
        raise HTTPException(status_code=400, detail=f"員工編號 {employee.emp_no} 已存在")
    
    # crud.get_employee 會載入所有關聯 (包含空的 reservations)
    new_emp = crud.create_employee(db=db, employee=employee)
    return crud.get_employee(db, employee_id=new_emp.id)

@app.get("/api/v1/employees/", response_model=List[schemas.Employee], summary="查詢員工列表")
def read_employees_api(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    # crud.get_employees 現在會自動載入所有關聯
    employees = crud.get_employees(db, skip=skip, limit=limit)
    return employees

@app.get("/api/v1/employees/{employee_id}", response_model=schemas.Employee, summary="查詢單一員工")
def read_employee_api(employee_id: int, db: Session = Depends(get_db)):
    # crud.get_employee 現在會自動載入所有關聯
    db_employee = crud.get_employee(db, employee_id=employee_id)
    if db_employee is None:
        raise HTTPException(status_code=404, detail="找不到該員工")
    return db_employee

@app.get("/api/v1/employees/emp-no/{emp_no}", response_model=schemas.Employee, summary="依據員工編號查詢員工")
def read_employee_by_emp_no_api(emp_no: str, db: Session = Depends(get_db)):
    """
    依據員工編號查詢員工。
    """
    db_employee = crud.get_employee_by_emp_no(db, emp_no=emp_no)
    if db_employee is None:
        raise HTTPException(status_code=404, detail="找不到該員工編號")
    return crud.get_employee(db, employee_id=db_employee.id)

@app.get("/api/v1/vehicles/{vehicle_id}", response_model=schemas.Vehicle, summary="查詢單一車輛")
def read_vehicle_api(vehicle_id: int, db: Session = Depends(get_db)):
    # crud.get_vehicle 現在會自動載入所有關聯
    db_vehicle = crud.get_vehicle(db, vehicle_id=vehicle_id)
    if db_vehicle is None:
        raise HTTPException(status_code=404, detail="找不到該車輛")
    return db_vehicle

# --- Vehicles API (!!! 新增 Update 和 Delete !!!) ---

@app.post("/api/v1/vehicles/", response_model=schemas.Vehicle, summary="建立新車輛")
def create_vehicle_api(vehicle: schemas.VehicleCreate, db: Session = Depends(get_db)):
    db_vehicle = crud.get_vehicle_by_plate_no(db, plate_no=vehicle.plate_no)
    if db_vehicle:
        raise HTTPException(status_code=400, detail=f"車牌號碼 {vehicle.plate_no} 已存在")
    new_vehicle = crud.create_vehicle(db=db, vehicle=vehicle)
    return crud.get_vehicle(db, vehicle_id=new_vehicle.id)

@app.put("/api/v1/vehicles/{vehicle_id}", 
         response_model=schemas.Vehicle, 
         summary="更新車輛資料 (完整替換)")
def update_vehicle_api(
    vehicle_id: int, 
    vehicle_update: schemas.VehicleUpdate, # 使用 Update Schema
    db: Session = Depends(get_db),
    actor_id: int = Depends(get_current_actor_id)
):
    """
    更新指定 ID 的車輛資料。
    注意：PUT 通常表示「完整替換」，但我們實作成「部分更新」。
    (更符合語意的應該是 PATCH，但 PUT 較常用)
    
    會記錄 Audit Log。
    """
    updated_vehicle = crud.update_vehicle(
        db=db, 
        vehicle_id=vehicle_id, 
        vehicle_update=vehicle_update,
        actor_id=actor_id
    )
    if updated_vehicle is None:
        raise HTTPException(status_code=404, detail="找不到該車輛")
    
    # crud.update_vehicle 返回的是更新後的 SQLAlchemy 物件
    # 我們需要重新查詢一次，以獲得包含所有關聯的 Pydantic 物件
    return crud.get_vehicle(db, vehicle_id=vehicle_id)

@app.delete("/api/v1/vehicles/{vehicle_id}", 
            response_model=schemas.Vehicle, # 回傳被刪除的資料
            summary="刪除車輛")
def delete_vehicle_api(
    vehicle_id: int,
    db: Session = Depends(get_db),
    actor_id: int = Depends(get_current_actor_id)
):
    """
    刪除指定 ID 的車輛。
    
    警告：如果該車輛仍有關聯的預約、工單等，刪除可能會失敗 (資料庫限制)。
    建議優先使用 PUT 將 status 更新為 'retired' (軟刪除)。
    
    會記錄 Audit Log。
    """
    try:
        deleted_vehicle_data = crud.delete_vehicle(
            db=db, 
            vehicle_id=vehicle_id, 
            actor_id=actor_id
        )
        if deleted_vehicle_data is None:
            raise HTTPException(status_code=404, detail="找不到該車輛")
        
        # 因為物件已被刪除，我們無法用 get_vehicle 查詢
        # 直接用刪除前回傳的資料轉換成 Pydantic Schema 回傳
        # (注意：這可能不包含完整的關聯，取決於 deepcopy 的深度)
        return schemas.Vehicle.model_validate(deleted_vehicle_data) 
        
    except Exception as e:
        # 捕捉 ForeignKey 錯誤等
        raise HTTPException(status_code=400, detail=f"刪除失敗: {e}")

@app.get("/api/v1/vehicles/", response_model=List[schemas.Vehicle], summary="查詢車輛列表")
def read_vehicles_api(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    讀取車輛列表，支援分頁。
    會一併回傳所有關聯資料 (文件、備品、保養計畫、工單、合規紀錄、預約、行程)。
    """
    # crud.get_vehicles 現在會自動載入所有關聯
    vehicles = crud.get_vehicles(db, skip=skip, limit=limit)
    return vehicles

@app.get("/api/v1/vehicles/{vehicle_id}", response_model=schemas.Vehicle, summary="查詢單一車輛")
def read_vehicle_api(vehicle_id: int, db: Session = Depends(get_db)):
    """
    依據資料庫 ID 查詢特定車輛。
    會一併回傳所有關聯資料。
    """
    # crud.get_vehicle 現在會自動載入所有關聯
    db_vehicle = crud.get_vehicle(db, vehicle_id=vehicle_id)
    if db_vehicle is None:
        raise HTTPException(status_code=404, detail="找不到該車輛")
    return db_vehicle

@app.get("/api/v1/vehicles/plate/{plate_no}", response_model=schemas.Vehicle, summary="依據車牌查詢車輛")
def read_vehicle_by_plate_api(plate_no: str, db: Session = Depends(get_db)):
    """
    依據車牌號碼查詢車輛。
    """
    db_vehicle = crud.get_vehicle_by_plate_no(db, plate_no=plate_no)
    if db_vehicle is None:
        raise HTTPException(status_code=404, detail="找不到該車牌")
    return crud.get_vehicle(db, vehicle_id=db_vehicle.id)

# --- Vehicle Documents API ---
@app.post("/api/v1/vehicles/{vehicle_id}/documents/", 
          response_model=schemas.VehicleDocument, 
          summary="為車輛新增文件 (包含檔案上傳)")
async def create_document_for_vehicle( # (!!! 改成 async def !!!)
    vehicle_id: int, 
    # (!!! 修改 !!!) 
    # 文件元資料現在作為表單欄位傳入，而不是 JSON body
    # 我們使用 Depends() 將 Pydantic schema 注入
    doc_meta: schemas.VehicleDocumentCreate = Depends(), 
    # (!!! 新增 !!!) 接收上傳的檔案
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    actor_id: int = Depends(get_current_actor_id) # (加入 actor_id for Audit Log)
):
    """
    為指定的車輛 ID 新增一筆文件索引，並同時上傳檔案。
    
    使用 multipart/form-data 格式提交：
    - **doc_type**: 文件類型 (e.g., 'insurance')
    - **issued_on**: (選填) 核發日期
    - **expires_on**: (選填) 到期日期
    - **tags**: (選填) 標籤
    - **file**: 要上傳的檔案 (PDF, JPG, PNG etc.)
    
    (此 API 會自動儲存檔案、計算 SHA256，並記錄 Audit Log)
    """
    # 1. 確認車輛存在
    db_vehicle = crud.get_vehicle(db, vehicle_id=vehicle_id)
    if db_vehicle is None:
        raise HTTPException(status_code=404, detail="找不到該車輛")
        
    # 2. 處理檔案上傳
    try:
        # 呼叫 utils 儲存檔案並取得路徑/雜湊值
        # (改成 await，因為 UploadFile 的操作可能是異步的)
        # (注意：我們的 utils.save_upload_file 不是 async，但 FastAPI 會處理)
        file_path, sha256_hash = utils.save_upload_file(file) 
    except IOError as e:
        raise HTTPException(status_code=500, detail=f"檔案儲存失敗: {e}")
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"檔案處理失敗: {e}")

    # 3. 建立文件紀錄到資料庫
    try:
        db_document = crud.create_vehicle_document(
            db=db, 
            document=doc_meta, # 傳入從表單來的元資料
            vehicle_id=vehicle_id,
            file_url=file_path, # 傳入儲存的路徑
            sha256=sha256_hash # 傳入計算出的雜湊值
        )
        
        # (!!! 新增 Audit Log !!!)
        # 在 commit 之前加入 Log
        # 注意: create_vehicle_document 內部有 commit，
        # 所以 Log 和 Document 建立不在同一個 transaction
        # 更好的做法是將 commit 移出 create_vehicle_document
        # 但我們先保持簡單
        crud.create_audit_log(
            db=db,
            actor_id=actor_id,
            action="CREATE",
            entity="VehicleDocument",
            entity_id=db_document.id, # Commit 後已有 ID
            new_value=db_document # 傳入 SQLAlchemy 物件
        )
        # Commit the audit log
        try:
             db.commit()
        except Exception as e:
             db.rollback()
             print(f"寫入 Document Audit Log 失敗: {e}") # 記錄錯誤，但不影響主流程

        return db_document
        
    except Exception as e:
        # 如果資料庫寫入失敗，理論上應該刪除剛上傳的檔案
        # (這裡先省略)
        raise HTTPException(status_code=500, detail=f"建立文件紀錄失敗: {e}")

@app.get("/files/{file_path:path}", 
         response_class=FileResponse, # 直接回傳檔案
         summary="下載已上傳的檔案")
async def download_file(file_path: str):
    """
    根據相對路徑下載 uploads 資料夾中的檔案。
    (警告：沒有任何權限檢查！僅供測試)
    """
    # 組合完整路徑
    full_path = Path("uploads") / file_path
    
    if not full_path.is_file():
        raise HTTPException(status_code=404, detail="找不到檔案")

    # 猜測檔案類型 (MIME type)
    media_type, _ = mimetypes.guess_type(full_path)
    
    return FileResponse(path=full_path, media_type=media_type, filename=full_path.name)

@app.get("/api/v1/vehicles/{vehicle_id}/documents/", 
         response_model=List[schemas.VehicleDocument],
         summary="查詢特定車輛的所有文件")
def read_vehicle_documents(
    vehicle_id: int, 
    db: Session = Depends(get_db)
):
    """
    取得指定車輛 ID 的所有文件清單。
    """
    # 先確認車輛存在
    db_vehicle = crud.get_vehicle(db, vehicle_id=vehicle_id)
    if db_vehicle is None:
        raise HTTPException(status_code=404, detail="找不到該車輛")
        
    return crud.get_vehicle_documents(db=db, vehicle_id=vehicle_id)


# --- Vehicle Assets API ---
@app.post("/api/v1/assets/", 
          response_model=schemas.VehicleAsset, 
          summary="建立備品資產 (如安全帽)")
def create_asset_api(
    asset: schemas.VehicleAssetCreate, 
    db: Session = Depends(get_db)
):
    """
    建立一個新的備品資產 (例如：安全帽、鎖具)。
    - **asset_type**: 'helmet', 'lock', 'raincoat' 等
    - **serial_no**: 資產編號 (必須唯一)
    - **vehicle_id**: (選填) 建立時直接綁定給某台車
    """
    try:
        return crud.create_vehicle_asset(db=db, asset=asset)
    except ValueError as e:
        # 捕捉 crud 中拋出的錯誤 (e.g., 編號重複, 車輛不存在)
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/assets/", 
         response_model=List[schemas.VehicleAsset],
         summary="查詢備品資產列表")
def read_assets_api(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """
    取得系統中所有的備品資產清單 (分頁)。
    """
    assets = crud.get_assets(db, skip=skip, limit=limit)
    return assets

# --- Vendors API ---
@app.post("/api/v1/vendors/", 
          response_model=schemas.Vendor, 
          summary="建立新供應商")
def create_vendor_api(
    vendor: schemas.VendorCreate, 
    db: Session = Depends(get_db)
):
    """
    建立新供應商 (維修廠、保險公司等)。
    """
    return crud.create_vendor(db=db, vendor=vendor)

@app.get("/api/v1/vendors/", 
         response_model=List[schemas.Vendor], 
         summary="查詢供應商列表")
def read_vendors_api(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """
    查詢供應商列表 (分頁)。
    """
    return crud.get_vendors(db, skip=skip, limit=limit)


# --- MaintenancePlans API ---

@app.post("/api/v1/vehicles/{vehicle_id}/maintenance-plans/", 
          response_model=schemas.MaintenancePlan, 
          summary="為車輛建立保養計畫")
def create_maintenance_plan_api(
    vehicle_id: int, 
    plan: schemas.MaintenancePlanCreate, 
    db: Session = Depends(get_db)
):
    """
    為指定的車輛 ID 建立一個保養計畫 (e.g., 每 5000km 保養)。
    """
    # 先確認車輛存在
    db_vehicle = crud.get_vehicle(db, vehicle_id=vehicle_id)
    if db_vehicle is None:
        raise HTTPException(status_code=404, detail="找不到該車輛")
        
    return crud.create_maintenance_plan_for_vehicle(db=db, plan=plan, vehicle_id=vehicle_id)


@app.get("/api/v1/vehicles/{vehicle_id}/maintenance-plans/", 
         response_model=List[schemas.MaintenancePlan],
         summary="查詢特定車輛的保養計畫")
def read_maintenance_plans_api(
    vehicle_id: int, 
    db: Session = Depends(get_db)
):
    """
    取得指定車輛 ID 的所有保養計畫清單。
    """
    db_vehicle = crud.get_vehicle(db, vehicle_id=vehicle_id)
    if db_vehicle is None:
        raise HTTPException(status_code=404, detail="找不到該車輛")
        
    return crud.get_maintenance_plans_for_vehicle(db=db, vehicle_id=vehicle_id)


# --- WorkOrders API ---

@app.post("/api/v1/work-orders/", 
          response_model=schemas.WorkOrder, 
          summary="建立新工單")
def create_work_order_api(
    work_order: schemas.WorkOrderCreate, 
    db: Session = Depends(get_db)
):
    """
    建立一筆新的工單 (保養、維修、定檢等)。
    - **vehicle_id**: 必須指定要維修的車輛 ID
    - **vendor_id**: (選填) 執行工單的供應商 ID
    """
    try:
        new_order = crud.create_work_order(db=db, work_order=work_order)
        # 重新查詢以載入 vendor 資訊
        return crud.get_work_order(db, work_order_id=new_order.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/work-orders/{work_order_id}", 
         response_model=schemas.WorkOrder,
         summary="查詢單一工單")
def read_work_order_api(
    work_order_id: int, 
    db: Session = Depends(get_db)
):
    """
    依據 ID 查詢單一工單，會一併回傳供應商資訊。
    """
    db_work_order = crud.get_work_order(db, work_order_id=work_order_id)
    if db_work_order is None:
        raise HTTPException(status_code=404, detail="找不到該工單")
    return db_work_order

@app.get("/api/v1/work-orders/",
         response_model=List[schemas.WorkOrder],
         summary="查詢工單列表")
def read_work_orders_api(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    取得系統中所有的工單清單 (分頁)，包含供應商和車輛資訊。
    """
    work_orders = crud.get_work_orders(db, skip=skip, limit=limit)
    return work_orders

@app.get("/api/v1/vehicles/{vehicle_id}/work-orders/", 
         response_model=List[schemas.WorkOrder],
         summary="查詢特定車輛的所有工單")
def read_vehicle_work_orders_api(
    vehicle_id: int, 
    db: Session = Depends(get_db)
):
    """
    取得指定車輛 ID 的所有工單清單。
    """
    db_vehicle = crud.get_vehicle(db, vehicle_id=vehicle_id)
    if db_vehicle is None:
        raise HTTPException(status_code=404, detail="找不到該車輛")
        
    return crud.get_work_orders_for_vehicle(db=db, vehicle_id=vehicle_id)

@app.put("/api/v1/work-orders/{work_order_id}",
         response_model=schemas.WorkOrder,
         summary="更新工單資料")
def update_work_order_api(
    work_order_id: int,
    work_order_update: schemas.WorkOrderUpdate, # 使用 Update Schema
    db: Session = Depends(get_db),
    actor_id: int = Depends(get_current_actor_id)
):
    """
    更新指定 ID 的工單資料。
    僅會更新請求中提供的欄位。

    會記錄 Audit Log。
    """
    try:
        updated_work_order = crud.update_work_order(
            db=db,
            work_order_id=work_order_id,
            work_order_update=work_order_update,
            actor_id=actor_id
        )
        if updated_work_order is None:
            raise HTTPException(status_code=404, detail="找不到該工單")

        # crud.update_work_order 返回的是更新後的物件
        # 我們需要重新查詢一次，以包含關聯的 vendor 和 vehicle
        # (或者修改 update_work_order 讓它回傳前先 refresh 關聯)
        # 為了確保資料最新，重新查詢比較保險
        return crud.get_work_order(db, work_order_id=work_order_id)

    except ValueError as e: # 捕捉 crud 中可能的 ValueError (例如 vendor_id 無效)
         raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # 捕捉可能的資料庫錯誤或其他例外
        raise HTTPException(status_code=500, detail=f"更新失敗: {e}")

@app.delete("/api/v1/work-orders/{work_order_id}",
            response_model=schemas.WorkOrder, # 回傳被刪除的工單資料
            summary="刪除工單")
def delete_work_order_api(
    work_order_id: int,
    db: Session = Depends(get_db),
    actor_id: int = Depends(get_current_actor_id)
):
    """
    刪除指定 ID 的工單。

    會記錄 Audit Log。
    """
    try:
        deleted_work_order_data = crud.delete_work_order(
            db=db,
            work_order_id=work_order_id,
            actor_id=actor_id
        )
        if deleted_work_order_data is None:
            raise HTTPException(status_code=404, detail="找不到該工單")

        # 因為物件已被刪除，無法重新查詢，直接用刪除前複製的資料回傳
        # 確保回傳的資料符合 schemas.WorkOrder (可能需要手動處理關聯欄位)
        # 為了簡化，我們先假設 Pydantic 可以處理 SQLAlchemy 刪除前的物件
        # 注意：這裡的 vendor 可能不會被正確序列化，如果需要，要手動組裝
        return schemas.WorkOrder.model_validate(deleted_work_order_data)

    except Exception as e:
        # 捕捉可能的資料庫錯誤或其他例外
        raise HTTPException(status_code=400, detail=f"刪除失敗: {e}")

# --- Insurances API ---

@app.post("/api/v1/insurances/", 
          response_model=schemas.Insurance, 
          summary="建立新保險紀錄")
def create_insurance_api(
    insurance: schemas.InsuranceCreate, 
    db: Session = Depends(get_db)
):
    """
    為車輛建立一筆保險紀錄 (強制險或任意險)。
    - **vehicle_id**: 必須指定
    - **insurer_id**: (選填) 關聯到已建立的供應商 (保險公司)
    """
    try:
        new_insurance = crud.create_insurance(db=db, insurance=insurance)
        # 重新查詢以載入 insurer (保險公司) 資訊
        return crud.get_insurance(db, insurance_id=new_insurance.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/vehicles/{vehicle_id}/insurances/", 
         response_model=List[schemas.Insurance],
         summary="查詢特定車輛的所有保險")
def read_vehicle_insurances_api(
    vehicle_id: int, 
    db: Session = Depends(get_db)
):
    """ 取得指定車輛 ID 的所有保險清單。 """
    db_vehicle = crud.get_vehicle(db, vehicle_id=vehicle_id)
    if db_vehicle is None:
        raise HTTPException(status_code=404, detail="找不到該車輛")
    return crud.get_insurances_for_vehicle(db=db, vehicle_id=vehicle_id)


# --- TaxesFees API ---

@app.post("/api/v1/taxes-fees/", 
          response_model=schemas.TaxFee, 
          summary="建立新稅費紀錄")
def create_tax_fee_api(
    tax_fee: schemas.TaxFeeCreate, 
    db: Session = Depends(get_db)
):
    """
    為車輛建立一筆稅費紀錄 (e.g., 2025年牌照稅)。
    - **vehicle_id**: 必須指定
    - **fee_type**: 'license_tax' (牌照稅) 或 'fuel_fee' (燃料費)
    """
    try:
        return crud.create_tax_fee(db=db, tax_fee=tax_fee)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/vehicles/{vehicle_id}/taxes-fees/", 
         response_model=List[schemas.TaxFee],
         summary="查詢特定車輛的所有稅費")
def read_vehicle_taxes_fees_api(
    vehicle_id: int, 
    db: Session = Depends(get_db)
):
    """ 取得指定車輛 ID 的所有稅費 (牌照/燃料) 清單。 """
    db_vehicle = crud.get_vehicle(db, vehicle_id=vehicle_id)
    if db_vehicle is None:
        raise HTTPException(status_code=404, detail="找不到該車輛")
    return crud.get_taxes_fees_for_vehicle(db=db, vehicle_id=vehicle_id)


# --- Inspections API ---
@app.post("/api/v1/inspections/", 
          response_model=schemas.Inspection, 
          summary="建立新檢驗紀錄")
def create_inspection_api(
    inspection: schemas.InspectionCreate, 
    db: Session = Depends(get_db)
):
    """
    為車輛建立一筆檢驗紀錄 (定檢或排氣檢驗)。
    - **vehicle_id**: 必須指定
    - **inspection_type**: 'periodic' (定檢) 或 'emission' (排氣)
    """
    try:
        new_inspection = crud.create_inspection(db=db, inspection=inspection)
        # 重新查詢以載入 inspector (檢驗站) 資訊
        return crud.get_inspection(db, inspection_id=new_inspection.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/vehicles/{vehicle_id}/inspections/", 
         response_model=List[schemas.Inspection],
         summary="查詢特定車輛的所有檢驗")
def read_vehicle_inspections_api(
    vehicle_id: int, 
    db: Session = Depends(get_db)
):
    """ 取得指定車輛 ID 的所有檢驗紀錄清單。 """
    db_vehicle = crud.get_vehicle(db, vehicle_id=vehicle_id)
    if db_vehicle is None:
        raise HTTPException(status_code=404, detail="找不到該車輛")
    return crud.get_inspections_for_vehicle(db=db, vehicle_id=vehicle_id)


# --- Violations API ---
# --- Vehicles API (!!! 修改 !!!) ---
@app.post("/api/v1/violations/", 
          response_model=schemas.Violation, 
          summary="建立新違規紀錄")
def create_violation_api(
    violation: schemas.ViolationCreate, 
    # (!!! 修改 !!!) 
    # 我們不再依賴 main.py 的 get_db，改用 dependencies.py 的
    db: Session = Depends(get_db), 
    # (!!! 新增 !!!) 
    # 自動從依賴取得 actor_id，並從 Request 取得 IP
    actor_id: int = Depends(get_current_actor_id),
    request: Request = None 
):
    """
    建立一筆交通違規紀錄 (罰單)。
    - **vehicle_id**: 必須指定
    - **driver_id**: (選填) 違規駕駛 (員工 ID)
    - **points**: (選填) 駕駛積點
    
    (此 API 現在會自動記錄 Audit Log)
    """
    try:
        # (!!! 修改 !!!) 將 actor_id 傳入 crud
        return crud.create_violation(
            db=db, 
            violation=violation, 
            actor_id=actor_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    # (!!! 補充 !!!)
    # 我們還沒有傳遞 IP 和 User-Agent
    # 完整的 crud.create_audit_log 呼叫應該是：
    # ip = request.client.host if request else None
    # ua = request.headers.get("user-agent") if request else None
    # (這需要修改 crud.create_violation 函式簽名，我們先簡化)

def read_vehicle_violations_api(
    vehicle_id: int, 
    db: Session = Depends(get_db)
):
    """ 取得指定車輛 ID 的所有違規紀錄清單。 """
    db_vehicle = crud.get_vehicle(db, vehicle_id=vehicle_id)
    if db_vehicle is None:
        raise HTTPException(status_code=404, detail="找不到該車輛")
    return crud.get_violations_for_vehicle(db=db, vehicle_id=vehicle_id)

@app.get("/api/v1/employees/{employee_id}/violations/", 
         response_model=List[schemas.Violation],
         summary="查詢特定駕駛的所有違規")
def read_driver_violations_api(
    employee_id: int, 
    db: Session = Depends(get_db)
):
    """ 取得指定員工 ID 的所有違規紀錄清單 (用於計算積點)。 """
    db_driver = crud.get_employee(db, employee_id=employee_id)
    if db_driver is None:
        raise HTTPException(status_code=404, detail="找不到該員工")
    return crud.get_violations_for_driver(db=db, driver_id=employee_id)

# --- Reservations API ---
@app.post("/api/v1/reservations/", 
          response_model=schemas.Reservation, 
          summary="建立新借車申請 (預約)")
def create_reservation_api(
    reservation: schemas.ReservationCreate, 
    db: Session = Depends(get_db)
):
    """
    建立一筆新的借車申請。
    - **requester_id**: 申請員工 ID
    - **vehicle_id**: (選填) 指定車輛 ID
    - **start_ts / end_ts**: 預計起迄時間
    
    (簡易版邏輯): 
    - 若指定 vehicle_id，系統會檢查衝突與合規性 (強制險/車況)，
      若通過，狀態會直接設為 'approved' (已核准)。
    - 若未指定 vehicle_id，狀態會設為 'pending' (待審核)，
      等待調度員後續指派車輛 (Update API 未來實作)。
    """
    try:
        new_reservation = crud.create_reservation(db=db, reservation=reservation)
        # 重新查詢以載入 trip (會是 null)
        return crud.get_reservation(db, reservation_id=new_reservation.id)
    except ValueError as e:
        # 捕捉 crud 中拋出的錯誤 (e.g., 衝突, 合規失敗)
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/reservations/", 
         response_model=List[schemas.Reservation],
         summary="查詢預約列表")
def read_reservations_api(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """
    取得系統中所有的預約申請 (分頁)，包含已完成的行程回報。
    """
    return crud.get_reservations(db, skip=skip, limit=limit)

@app.get("/api/v1/reservations/{reservation_id}", 
         response_model=schemas.Reservation,
         summary="查詢單一預約")
def read_reservation_api(
    reservation_id: int, 
    db: Session = Depends(get_db)
):
    """
    依據 ID 查詢單一預約，包含已完成的行程回報。
    """
    db_reservation = crud.get_reservation(db, reservation_id=reservation_id)
    if db_reservation is None:
        raise HTTPException(status_code=404, detail="找不到該預約")
    return db_reservation

@app.patch("/api/v1/reservations/{reservation_id}/", 
          response_model=schemas.Reservation, 
          summary="更新預約狀態或指派車輛 (部分更新)")
def update_reservation_status_api(
    reservation_id: int,
    status_update: schemas.ReservationUpdate, # 使用 Update Schema
    db: Session = Depends(get_db),
    actor_id: int = Depends(get_current_actor_id)
):
    """
    更新預約的狀態 (e.g., pending -> approved/rejected/cancelled)
    或為 pending 的預約指派 vehicle_id。
    
    - 更新狀態為 cancelled 或 rejected 會自動清空 vehicle_id。
    - 為 pending 預約指派 vehicle_id 會自動將狀態更新為 approved (若無衝突)。
    - 指派 vehicle_id 時會檢查衝突。
    
    會記錄 Audit Log。
    """
    try:
        updated_reservation = crud.update_reservation_status(
            db=db,
            reservation_id=reservation_id,
            status_update=status_update,
            actor_id=actor_id
        )
        if updated_reservation is None:
             raise HTTPException(status_code=404, detail="找不到該預約")
             
        # crud.update_reservation_status 返回更新後的物件
        # 我們需要重新查詢以包含 trip
        return crud.get_reservation(db, reservation_id=reservation_id)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- Trips API ---
@app.post("/api/v1/reservations/{reservation_id}/trip/", 
          response_model=schemas.Trip, 
          summary="回報行程 (還車)")
def create_trip_api(
    reservation_id: int, 
    trip: schemas.TripCreate,
    db: Session = Depends(get_db)
):
    """
    為一筆「已核准」的預約回報行程 (還車)。
    - **reservation_id**: 要回報的預約 ID
    - **vehicle_id / driver_id**: 必須與預約單上一致
    - **odometer_start / odometer_end**: 起迄里程
    
    (簡易版邏輯): 
    - 成功回報後，會自動將預約 (Reservation) 狀態更新為 'completed'。
    """
    try:
        return crud.create_trip_for_reservation(
            db=db, 
            trip=trip, 
            reservation_id=reservation_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
# --- AuditLogs API ---
@app.get("/api/v1/audit-logs/", 
         response_model=List[schemas.AuditLog],
         summary="查詢稽核軌跡 (Audit Log)")
def read_audit_logs_api(
    skip: int = 0, 
    limit: int = 25, # Log 預設筆數少一點
    db: Session = Depends(get_db)
):
    """
    查詢系統的變動紀錄 (CUD)。
    (此為高權限 API，未來應限制僅 '系統管理員' 或 '稽核' 角色可存取)
    """
    logs = crud.get_audit_logs(db, skip=skip, limit=limit)
    return logs

# --- Analytics API ---
@app.get("/api/v1/analytics/vehicle-utilization/{vehicle_id}", 
         summary="查詢車輛使用率")
def get_vehicle_utilization_api(
    vehicle_id: int,
    start_date: str,
    end_date: str,
    db: Session = Depends(get_db)
):
    """
    計算指定車輛在指定日期範圍內的使用率。
    """
    from datetime import datetime
    start = datetime.fromisoformat(start_date).date()
    end = datetime.fromisoformat(end_date).date()
    
    # 檢查車輛是否存在
    db_vehicle = crud.get_vehicle(db, vehicle_id=vehicle_id)
    if not db_vehicle:
        raise HTTPException(status_code=404, detail="找不到該車輛")
    
    return analytics.get_vehicle_utilization(db, vehicle_id, start, end)


@app.get("/api/v1/analytics/cost-per-km/{vehicle_id}",
         summary="查詢每公里成本")
def get_cost_per_km_api(
    vehicle_id: int,
    start_date: str,
    end_date: str,
    db: Session = Depends(get_db)
):
    """
    計算指定車輛在指定日期範圍內的每公里成本 (TCO)。
    """
    from datetime import datetime
    start = datetime.fromisoformat(start_date).date()
    end = datetime.fromisoformat(end_date).date()
    
    # 檢查車輛是否存在
    db_vehicle = crud.get_vehicle(db, vehicle_id=vehicle_id)
    if not db_vehicle:
        raise HTTPException(status_code=404, detail="找不到該車輛")
    
    return analytics.get_cost_per_km(db, vehicle_id, start, end)


@app.get("/api/v1/analytics/compliance-report",
         summary="查詢合規性報表")
def get_compliance_report_api(
    days_ahead: int = 30,
    db: Session = Depends(get_db)
):
    """
    產生合規性報表，顯示即將到期的保險、定檢等項目。
    """
    return analytics.get_compliance_report(db, days_ahead=days_ahead)


@app.get("/api/v1/analytics/violation-stats",
         summary="查詢違規統計")
def get_violation_stats_api(
    start_date: str,
    end_date: str,
    db: Session = Depends(get_db)
):
    """
    查詢指定日期範圍內的違規統計，包含按車輛和按駕駛的統計。
    """
    from datetime import datetime
    start = datetime.fromisoformat(start_date).date()
    end = datetime.fromisoformat(end_date).date()
    
    return analytics.get_violation_stats(db, start, end)

# --- Data Import API ---
@app.post("/api/v1/import/employees",
          summary="從 CSV 匯入員工資料")
def import_employees_api(
    skip_existing: bool = True,
    db: Session = Depends(get_db)
):
    """
    從上傳的 CSV 檔案匯入員工資料。
    """
    # 這裡應該接收上傳的檔案
    # 暫時返回說明
    return {"message": "請使用工具函式 import_employees_from_csv 來匯入資料"}

@app.post("/api/v1/import/vehicles",
          summary="從 CSV 匯入車輛資料")
def import_vehicles_api(
    skip_existing: bool = True,
    db: Session = Depends(get_db)
):
    """
    從上傳的 CSV 檔案匯入車輛資料。
    """
    return {"message": "請使用工具函式 import_vehicles_from_csv 來匯入資料"}

@app.post("/api/v1/import/insurances",
          summary="從 CSV 匯入保險資料")
def import_insurances_api(
    skip_existing: bool = True,
    db: Session = Depends(get_db)
):
    """
    從上傳的 CSV 檔案匯入保險資料。
    """
    return {"message": "請使用工具函式 import_insurances_from_csv 來匯入資料"}