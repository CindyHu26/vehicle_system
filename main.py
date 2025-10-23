# 檔案名稱: main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

import crud
import models
import schemas
from database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="公務車與機車管理系統 API",
    description="規格書 v0.2 實作",
    version="0.2.0"
)

# --- Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- API Endpoints (API 路由) ---

# --- Employees API ---
# ... (保持不變) ...
@app.post("/api/v1/employees/", response_model=schemas.Employee, summary="建立新員工")
def create_employee_api(employee: schemas.EmployeeCreate, db: Session = Depends(get_db)):
    db_employee = crud.get_employee_by_emp_no(db, emp_no=employee.emp_no)
    if db_employee:
        raise HTTPException(status_code=400, detail=f"員工編號 {employee.emp_no} 已存在")
    return crud.create_employee(db=db, employee=employee)

@app.get("/api/v1/employees/", response_model=List[schemas.Employee], summary="查詢員工列表")
def read_employees_api(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    employees = crud.get_employees(db, skip=skip, limit=limit)
    return employees

@app.get("/api/v1/employees/{employee_id}", response_model=schemas.Employee, summary="查詢單一員工")
def read_employee_api(employee_id: int, db: Session = Depends(get_db)):
    db_employee = crud.get_employee(db, employee_id=employee_id)
    if db_employee is None:
        raise HTTPException(status_code=44, detail="找不到該員工")
    return db_employee


# --- Vehicles API ---
# (注意：查詢車輛的 response_model 會自動更新，因為我們改了 schemas.Vehicle)

@app.post("/api/v1/vehicles/", response_model=schemas.Vehicle, summary="建立新車輛")
def create_vehicle_api(vehicle: schemas.VehicleCreate, db: Session = Depends(get_db)):
    db_vehicle = crud.get_vehicle_by_plate_no(db, plate_no=vehicle.plate_no)
    if db_vehicle:
        raise HTTPException(status_code=400, detail=f"車牌號碼 {vehicle.plate_no} 已存在")
    # 建立車輛 (crud.create_vehicle)
    new_vehicle = crud.create_vehicle(db=db, vehicle=vehicle)
    
    # (!!! 重要 !!!)
    # 雖然車輛建立了，但 new_vehicle 物件是剛 refresh() 的，
    # 它還沒有我們在 schema.Vehicle 中定義的 .documents 和 .assets 屬性
    # (這些屬性是 []，是 Pydantic schema 層的預設值，不是 SQLAlchemy 載入的)
    # 為了讓回傳的資料格式正確 (包含空的 documents 和 assets 列表)，
    # 我們重新查詢一次，這次使用會 Eager Loading 的 get_vehicle
    return crud.get_vehicle(db, vehicle_id=new_vehicle.id)


@app.get("/api/v1/vehicles/", response_model=List[schemas.Vehicle], summary="查詢車輛列表")
def read_vehicles_api(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    # crud.get_vehicles 現在會自動載入 documents 和 assets
    vehicles = crud.get_vehicles(db, skip=skip, limit=limit)
    return vehicles


@app.get("/api/v1/vehicles/{vehicle_id}", response_model=schemas.Vehicle, summary="查詢單一車輛")
def read_vehicle_api(vehicle_id: int, db: Session = Depends(get_db)):
    # crud.get_vehicle 現在會自動載入 documents 和 assets
    db_vehicle = crud.get_vehicle(db, vehicle_id=vehicle_id)
    if db_vehicle is None:
        raise HTTPException(status_code=404, detail="找不到該車輛")
    return db_vehicle


# --- (新增) Vehicle Documents API ---

@app.post("/api/v1/vehicles/{vehicle_id}/documents/", 
          response_model=schemas.VehicleDocument, 
          summary="為車輛新增文件")
def create_document_for_vehicle(
    vehicle_id: int, 
    document: schemas.VehicleDocumentCreate, 
    db: Session = Depends(get_db)
):
    """
    為指定的車輛 ID 新增一筆文件索引。
    - **vehicle_id**: 車輛的資料庫 ID
    - **doc_type**: 'registration', 'insurance', 'fine', 'emission' 等
    - **file_url**: 檔案儲存路徑 (e.g., "C:\\share\\abc-1234_insurance.pdf")
    - **expires_on**: (選填) 文件到期日
    """
    # 先確認車輛存在
    db_vehicle = crud.get_vehicle(db, vehicle_id=vehicle_id)
    if db_vehicle is None:
        raise HTTPException(status_code=404, detail="找不到該車輛")
        
    return crud.create_vehicle_document(db=db, document=document, vehicle_id=vehicle_id)


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


# --- (新增) Vehicle Assets API ---

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

# --- (新增) Vendors API ---

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


# --- (新增) MaintenancePlans API ---

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


# --- (新增) WorkOrders API ---

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