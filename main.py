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

# --- Employees API (!!! 修改 !!!) ---
@app.post("/api/v1/employees/", response_model=schemas.Employee, summary="建立新員工")
def create_employee_api(employee: schemas.EmployeeCreate, db: Session = Depends(get_db)):
    db_employee = crud.get_employee_by_emp_no(db, emp_no=employee.emp_no)
    if db_employee:
        raise HTTPException(status_code=400, detail=f"員工編號 {employee.emp_no} 已存在")
    
    # 建立完後，用 get_employee 重新查詢，以包含空的 violations 列表
    new_emp = crud.create_employee(db=db, employee=employee)
    return crud.get_employee(db, employee_id=new_emp.id)


@app.get("/api/v1/employees/", response_model=List[schemas.Employee], summary="查詢員工列表")
def read_employees_api(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    # crud.get_employees 現在會自動載入 violations
    employees = crud.get_employees(db, skip=skip, limit=limit)
    return employees


@app.get("/api/v1/employees/{employee_id}", response_model=schemas.Employee, summary="查詢單一員工")
def read_employee_api(employee_id: int, db: Session = Depends(get_db)):
    # crud.get_employee 現在會自動載入 violations
    db_employee = crud.get_employee(db, employee_id=employee_id)
    if db_employee is None:
        raise HTTPException(status_code=404, detail="找不到該員工")
    return db_employee


# --- Vehicles API (!!! 修改 !!!) ---
@app.post("/api/v1/vehicles/", response_model=schemas.Vehicle, summary="建立新車輛")
def create_vehicle_api(vehicle: schemas.VehicleCreate, db: Session = Depends(get_db)):
    db_vehicle = crud.get_vehicle_by_plate_no(db, plate_no=vehicle.plate_no)
    if db_vehicle:
        raise HTTPException(status_code=400, detail=f"車牌號碼 {vehicle.plate_no} 已存在")
    
    # crud.get_vehicle 會載入所有關聯 (包含空的合規列表)
    new_vehicle = crud.create_vehicle(db=db, vehicle=vehicle)
    return crud.get_vehicle(db, vehicle_id=new_vehicle.id)


@app.get("/api/v1/vehicles/", response_model=List[schemas.Vehicle], summary="查詢車輛列表")
def read_vehicles_api(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    # crud.get_vehicles 現在會自動載入所有關聯
    vehicles = crud.get_vehicles(db, skip=skip, limit=limit)
    return vehicles


@app.get("/api/v1/vehicles/{vehicle_id}", response_model=schemas.Vehicle, summary="查詢單一車輛")
def read_vehicle_api(vehicle_id: int, db: Session = Depends(get_db)):
    # crud.get_vehicle 現在會自動載入所有關聯
    db_vehicle = crud.get_vehicle(db, vehicle_id=vehicle_id)
    if db_vehicle is None:
        raise HTTPException(status_code=404, detail="找不到該車輛")
    return db_vehicle

# --- Vehicle Documents API ---

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

@app.post("/api/v1/violations/", 
          response_model=schemas.Violation, 
          summary="建立新違規紀錄")
def create_violation_api(
    violation: schemas.ViolationCreate, 
    db: Session = Depends(get_db)
):
    """
    建立一筆交通違規紀錄 (罰單)。
    - **vehicle_id**: 必須指定
    - **driver_id**: (選填) 違規駕駛 (員工 ID)
    - **points**: (選填) 駕駛積點
    """
    try:
        return crud.create_violation(db=db, violation=violation)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/vehicles/{vehicle_id}/violations/", 
         response_model=List[schemas.Violation],
         summary="查詢特定車輛的所有違規")
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