# 檔案名稱: crud.py
from sqlalchemy.orm import Session, joinedload # <-- joinedload
import models
import schemas

# --- Employee CRUD ---
def get_employee(db: Session, employee_id: int):
    """ (R) 依據 ID 查詢單一員工 (!!! 修改 !!!) """
    return db.query(models.Employee).options(
        joinedload(models.Employee.violations) # 載入違規紀錄
    ).filter(models.Employee.id == employee_id).first()
def get_employee_by_emp_no(db: Session, emp_no: str):
    return db.query(models.Employee).filter(models.Employee.emp_no == emp_no).first()
def get_employees(db: Session, skip: int = 0, limit: int = 100):
    """ (R) 查詢多筆員工 (分頁) (!!! 修改 !!!) """
    return db.query(models.Employee).options(
        joinedload(models.Employee.violations) # 載入違規紀錄
    ).offset(skip).limit(limit).all()
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
        joinedload(models.Vehicle.work_orders),        # 載入工單
        joinedload(models.Vehicle.insurances),         # 加入合規性關聯
        joinedload(models.Vehicle.taxes_fees),
        joinedload(models.Vehicle.inspections),
        joinedload(models.Vehicle.violations)
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
        joinedload(models.Vehicle.work_orders),
        joinedload(models.Vehicle.insurances),
        joinedload(models.Vehicle.taxes_fees),
        joinedload(models.Vehicle.inspections),
        joinedload(models.Vehicle.violations)
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

# --- Insurance CRUD ---

def create_insurance(db: Session, insurance: schemas.InsuranceCreate):
    """ (C) 建立新保險紀錄 """
    # 檢查關聯的 vehicle_id
    db_vehicle = get_vehicle(db, insurance.vehicle_id)
    if not db_vehicle:
        raise ValueError(f"ID 為 {insurance.vehicle_id} 的車輛不存在")
    # 檢查關聯的 insurer_id (供應商)
    if insurance.insurer_id:
        db_vendor = get_vendor(db, insurance.insurer_id)
        if not db_vendor:
            raise ValueError(f"ID 為 {insurance.insurer_id} 的供應商不存在")
        if db_vendor.category != models.VendorCategoryEnum.insurance:
            raise ValueError(f"供應商 {db_vendor.name} 不是保險公司")
            
    db_insurance = models.Insurance(**insurance.model_dump())
    db.add(db_insurance)
    db.commit()
    db.refresh(db_insurance)
    return db_insurance

def get_insurance(db: Session, insurance_id: int):
    """ (R) 查詢單一保險 (並載入保險公司資訊) """
    return db.query(models.Insurance).options(
        joinedload(models.Insurance.insurer)
    ).filter(models.Insurance.id == insurance_id).first()

def get_insurances_for_vehicle(db: Session, vehicle_id: int):
    """ (R) 查詢特定車輛的所有保險 """
    return db.query(models.Insurance).options(
        joinedload(models.Insurance.insurer)
    ).filter(models.Insurance.vehicle_id == vehicle_id).all()


# --- TaxFee CRUD ---

def create_tax_fee(db: Session, tax_fee: schemas.TaxFeeCreate):
    """ (C) 建立新稅費紀錄 """
    db_vehicle = get_vehicle(db, tax_fee.vehicle_id)
    if not db_vehicle:
        raise ValueError(f"ID 為 {tax_fee.vehicle_id} 的車輛不存在")
        
    db_tax_fee = models.TaxFee(**tax_fee.model_dump())
    db.add(db_tax_fee)
    db.commit()
    db.refresh(db_tax_fee)
    return db_tax_fee

def get_taxes_fees_for_vehicle(db: Session, vehicle_id: int):
    """ (R) 查詢特定車輛的所有稅費 """
    return db.query(models.TaxFee)\
             .filter(models.TaxFee.vehicle_id == vehicle_id)\
             .all()


# --- Inspection CRUD ---

def create_inspection(db: Session, inspection: schemas.InspectionCreate):
    """ (C) 建立新檢驗紀錄 """
    db_vehicle = get_vehicle(db, inspection.vehicle_id)
    if not db_vehicle:
        raise ValueError(f"ID 為 {inspection.vehicle_id} 的車輛不存在")
    if inspection.inspector_id:
        db_vendor = get_vendor(db, inspection.inspector_id)
        if not db_vendor:
            raise ValueError(f"ID 為 {inspection.inspector_id} 的供應商不存在")
        if db_vendor.category not in (models.VendorCategoryEnum.inspection, models.VendorCategoryEnum.emission_check):
             raise ValueError(f"供應商 {db_vendor.name} 不是檢驗站")
             
    db_inspection = models.Inspection(**inspection.model_dump())
    db.add(db_inspection)
    db.commit()
    db.refresh(db_inspection)
    return db_inspection

def get_inspection(db: Session, inspection_id: int):
    """ (R) 查詢單一檢驗 (並載入檢驗站資訊) """
    return db.query(models.Inspection).options(
        joinedload(models.Inspection.inspector)
    ).filter(models.Inspection.id == inspection_id).first()

def get_inspections_for_vehicle(db: Session, vehicle_id: int):
    """ (R) 查詢特定車輛的所有檢驗 """
    return db.query(models.Inspection).options(
        joinedload(models.Inspection.inspector)
    ).filter(models.Inspection.vehicle_id == vehicle_id).all()


# --- Violation CRUD ---

def create_violation(db: Session, violation: schemas.ViolationCreate):
    """ (C) 建立新違規紀錄 """
    db_vehicle = get_vehicle(db, violation.vehicle_id)
    if not db_vehicle:
        raise ValueError(f"ID 為 {violation.vehicle_id} 的車輛不存在")
    if violation.driver_id:
        db_driver = get_employee(db, violation.driver_id)
        if not db_driver:
            raise ValueError(f"ID 為 {violation.driver_id} 的員工不存在")
            
    db_violation = models.Violation(**violation.model_dump())
    db.add(db_violation)
    db.commit()
    db.refresh(db_violation)
    return db_violation

def get_violation(db: Session, violation_id: int):
    """ (R) 查詢單一違規 """
    return db.query(models.Violation).filter(models.Violation.id == violation_id).first()

def get_violations_for_vehicle(db: Session, vehicle_id: int):
    """ (R) 查詢特定車輛的所有違規 """
    return db.query(models.Violation)\
             .filter(models.Violation.vehicle_id == vehicle_id)\
             .all()

def get_violations_for_driver(db: Session, driver_id: int):
    """ (R) 查詢特定駕駛的所有違規 """
    return db.query(models.Violation)\
             .filter(models.Violation.driver_id == driver_id)\
             .all()