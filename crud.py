# 檔案名稱: crud.py
from sqlalchemy.orm import Session, joinedload # <-- (新增) joinedload
import models
import schemas

# --- Employee CRUD ---
def get_employee(db: Session, employee_id: int):
    return db.query(models.Employee).filter(models.Employee.id == employee_id).first()
def get_employee_by_emp_no(db: Session, emp_no: str):
    return db.query(models.Employee).filter(models.Employee.emp_no == emp_no).first()
def get_employees(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Employee).offset(skip).limit(limit).all()
def create_employee(db: Session, employee: schemas.EmployeeCreate):
    db_employee = models.Employee(**employee.model_dump())
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    return db_employee

def get_vehicle(db: Session, vehicle_id: int):
    """ 
    (R) 依據 ID 查詢單一車輛
    (!!! 修改 !!!) 加入 plans 和 orders
    """
    return db.query(models.Vehicle).options(
        joinedload(models.Vehicle.documents),         # 載入文件
        joinedload(models.Vehicle.assets),            # 載入備品
        joinedload(models.Vehicle.maintenance_plans), # 載入保養計畫
        joinedload(models.Vehicle.work_orders)        # 載入工單
    ).filter(models.Vehicle.id == vehicle_id).first()

def get_vehicle_by_plate_no(db: Session, plate_no: str):
    """ (R) 依據 車牌號碼 查詢單一車輛 (用於檢查重複) """
    # 建立車輛時，不需要載入關聯資料，保持原樣
    return db.query(models.Vehicle).filter(models.Vehicle.plate_no == plate_no).first()

def get_vehicles(db: Session, skip: int = 0, limit: int = 100):
    """ 
    (R) 查詢多筆車輛 (分頁)
    (!!! 修改 !!!) 使用 joinedload 主動載入關聯資料
    """
    return db.query(models.Vehicle).options(
        joinedload(models.Vehicle.documents), # 載入文件
        joinedload(models.Vehicle.assets),    # 載入備品
        joinedload(models.Vehicle.maintenance_plans),
        joinedload(models.Vehicle.work_orders)
    ).offset(skip).limit(limit).all()

def create_vehicle(db: Session, vehicle: schemas.VehicleCreate):
    if vehicle.vehicle_type in (schemas.VehicleTypeEnum.motorcycle, schemas.VehicleTypeEnum.ev_scooter):
        vehicle.helmet_required = True
    db_vehicle = models.Vehicle(**vehicle.model_dump())
    db.add(db_vehicle)
    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle

def create_vehicle_document(
    db: Session, 
    document: schemas.VehicleDocumentCreate, 
    vehicle_id: int
):
    """ (C) 建立新的車輛文件，並綁定到 vehicle_id """
    db_document = models.VehicleDocument(
        **document.model_dump(), 
        vehicle_id=vehicle_id
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document

def get_vehicle_documents(db: Session, vehicle_id: int):
    """ (R) 查詢特定車輛的所有文件 """
    return db.query(models.VehicleDocument)\
             .filter(models.VehicleDocument.vehicle_id == vehicle_id)\
             .all()


def create_vehicle_asset(
    db: Session, 
    asset: schemas.VehicleAssetCreate
):
    """ (C) 建立新的備品資產 """
    # 檢查 vehicle_id 是否存在 (如果有的話)
    if asset.vehicle_id:
        db_vehicle = get_vehicle(db, asset.vehicle_id)
        if not db_vehicle:
            raise ValueError(f"ID 為 {asset.vehicle_id} 的車輛不存在")
            
    # 檢查 Serial No. 是否重複
    db_asset = db.query(models.VehicleAsset)\
                 .filter(models.VehicleAsset.serial_no == asset.serial_no)\
                 .first()
    if db_asset:
        raise ValueError(f"資產編號 {asset.serial_no} 已存在")

    db_asset = models.VehicleAsset(**asset.model_dump())
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    return db_asset

def get_assets(db: Session, skip: int = 0, limit: int = 100):
    """ (R) 查詢所有備品 (不分車輛) """
    return db.query(models.VehicleAsset).offset(skip).limit(limit).all()

# --- Vendor CRUD ---
def create_vendor(db: Session, vendor: schemas.VendorCreate):
    """ (C) 建立新供應商 """
    db_vendor = models.Vendor(**vendor.model_dump())
    db.add(db_vendor)
    db.commit()
    db.refresh(db_vendor)
    return db_vendor

def get_vendor(db: Session, vendor_id: int):
    """ (R) 查詢單一供應商 """
    return db.query(models.Vendor).filter(models.Vendor.id == vendor_id).first()

def get_vendors(db: Session, skip: int = 0, limit: int = 100):
    """ (R) 查詢多筆供應商 """
    return db.query(models.Vendor).offset(skip).limit(limit).all()


# --- MaintenancePlan CRUD ---
def create_maintenance_plan_for_vehicle(
    db: Session, 
    plan: schemas.MaintenancePlanCreate, 
    vehicle_id: int
):
    """ (C) 為車輛建立保養計畫 """
    db_plan = models.MaintenancePlan(
        **plan.model_dump(), 
        vehicle_id=vehicle_id
    )
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return db_plan

def get_maintenance_plans_for_vehicle(db: Session, vehicle_id: int):
    """ (R) 查詢特定車輛的所有保養計畫 """
    return db.query(models.MaintenancePlan)\
             .filter(models.MaintenancePlan.vehicle_id == vehicle_id)\
             .all()


# --- WorkOrder CRUD ---
def create_work_order(db: Session, work_order: schemas.WorkOrderCreate):
    """ (C) 建立新工單 """
    # 檢查關聯的 vehicle_id 是否存在
    db_vehicle = get_vehicle(db, work_order.vehicle_id)
    if not db_vehicle:
        raise ValueError(f"ID 為 {work_order.vehicle_id} 的車輛不存在")
        
    # 檢查關聯的 vendor_id 是否存在 (如果有的話)
    if work_order.vendor_id:
        db_vendor = get_vendor(db, work_order.vendor_id)
        if not db_vendor:
            raise ValueError(f"ID 為 {work_order.vendor_id} 的供應商不存在")

    db_work_order = models.WorkOrder(**work_order.model_dump())
    db.add(db_work_order)
    db.commit()
    db.refresh(db_work_order)
    return db_work_order

def get_work_order(db: Session, work_order_id: int):
    """ (R) 查詢單一工單 (並載入供應商資訊) """
    return db.query(models.WorkOrder).options(
        joinedload(models.WorkOrder.vendor) # 主動載入供應商
    ).filter(models.WorkOrder.id == work_order_id).first()

def get_work_orders_for_vehicle(db: Session, vehicle_id: int):
    """ (R) 查詢特定車輛的所有工單 (並載入供應商資訊) """
    return db.query(models.WorkOrder).options(
        joinedload(models.WorkOrder.vendor)
    ).filter(models.WorkOrder.vehicle_id == vehicle_id).all()