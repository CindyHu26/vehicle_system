# 檔案名稱: crud.py
from sqlalchemy.orm import Session, joinedload, subqueryload
import models
import schemas
from datetime import datetime

# --- Employee CRUD ---
def get_employee(db: Session, employee_id: int):
    """ (R) 依據 ID 查詢單一員工 (!!! 修改 !!!) """
    return db.query(models.Employee).options(
        joinedload(models.Employee.violations),
        # 使用 subqueryload 避免過多 JOIN
        subqueryload(models.Employee.reservations_requested), 
        subqueryload(models.Employee.trips_driven)
    ).filter(models.Employee.id == employee_id).first()

def get_employee_by_emp_no(db: Session, emp_no: str):
    return db.query(models.Employee).filter(models.Employee.emp_no == emp_no).first()
def get_employees(db: Session, skip: int = 0, limit: int = 100):
    """ (R) 查詢多筆員工 (分頁) (!!! 修改 !!!) """
    return db.query(models.Employee).options(
        subqueryload(models.Employee.violations),
        subqueryload(models.Employee.reservations_requested),
        subqueryload(models.Employee.trips_driven)
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
    (!!! 修改 !!!) 加入預約與行程
    """
    return db.query(models.Vehicle).options(
        # (使用 subqueryload 提高效能)
        subqueryload(models.Vehicle.documents),
        subqueryload(models.Vehicle.assets),
        subqueryload(models.Vehicle.maintenance_plans),
        subqueryload(models.Vehicle.work_orders).joinedload(models.WorkOrder.vendor), # 工單要含供應商
        subqueryload(models.Vehicle.insurances).joinedload(models.Insurance.insurer), # 保險要含供應商
        subqueryload(models.Vehicle.taxes_fees),
        subqueryload(models.Vehicle.inspections).joinedload(models.Inspection.inspector), # 檢驗要含供應商
        subqueryload(models.Vehicle.violations),
        subqueryload(models.Vehicle.reservations),
        subqueryload(models.Vehicle.trips)
    ).filter(models.Vehicle.id == vehicle_id).first()

def get_vehicle_by_plate_no(db: Session, plate_no: str):
    """ (R) 依據 車牌號碼 查詢單一車輛 (用於檢查重複) """
    # 建立車輛時，不需要載入關聯資料，保持原樣
    return db.query(models.Vehicle).filter(models.Vehicle.plate_no == plate_no).first()

def get_vehicles(db: Session, skip: int = 0, limit: int = 100):
    """ 
    (R) 查詢多筆車輛 (分頁)
    (!!! 修改 !!!) 加入預約與行程
    """
    return db.query(models.Vehicle).options(
        # (使用 subqueryload 提高效能)
        subqueryload(models.Vehicle.documents),
        subqueryload(models.Vehicle.assets),
        subqueryload(models.Vehicle.maintenance_plans),
        subqueryload(models.Vehicle.work_orders),
        subqueryload(models.Vehicle.insurances),
        subqueryload(models.Vehicle.taxes_fees),
        subqueryload(models.Vehicle.inspections),
        subqueryload(models.Vehicle.violations),
        subqueryload(models.Vehicle.reservations),
        subqueryload(models.Vehicle.trips)
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

# --- (新增) Reservation CRUD ---

def create_reservation(db: Session, reservation: schemas.ReservationCreate):
    """ (C) 建立新預約申請 """
    # 檢查申請人是否存在
    db_requester = get_employee(db, reservation.requester_id)
    if not db_requester:
        raise ValueError(f"ID 為 {reservation.requester_id} 的申請人不存在")
    
    # 檢查車輛是否存在 (如果指定)
    if reservation.vehicle_id:
        db_vehicle = get_vehicle(db, reservation.vehicle_id)
        if not db_vehicle:
            raise ValueError(f"ID 為 {reservation.vehicle_id} 的車輛不存在")
    
    # (!!! 核心) 檢查時段衝突 (簡易版)
    # 我們檢查「被指定的車輛」在「該時段」是否已有「已核准」的預約
    if reservation.vehicle_id:
        existing_reservation = db.query(models.Reservation).filter(
            models.Reservation.vehicle_id == reservation.vehicle_id,
            models.Reservation.status == models.ReservationStatusEnum.approved,
            # (B.start < A.end) AND (B.end > A.start) -> 表示重疊
            models.Reservation.start_ts < reservation.end_ts,
            models.Reservation.end_ts > reservation.start_ts
        ).first()
        
        if existing_reservation:
            raise ValueError(f"車輛 {reservation.vehicle_id} 在該時段已被 {existing_reservation.id} 預約")

    # (!!! 核心) 檢查法規 (簡易版)
    # 規格書 4.6, 12: 檢查保險/定檢是否有效
    if reservation.vehicle_id:
        db_vehicle = get_vehicle(db, reservation.vehicle_id) # 拿 Eager loaded data
        # 1. 檢查強制險
        cali_valid = False
        today = datetime.now(reservation.start_ts.tzinfo).date() # 以預約日的時區為主
        for ins in db_vehicle.insurances:
            if ins.policy_type == models.InsurancePolicyTypeEnum.CALI and ins.expires_on >= today:
                cali_valid = True
                break
        if not cali_valid:
            raise ValueError(f"車輛 {db_vehicle.plate_no} 強制險已過期或不存在，禁止派車")
            
        # 2. 檢查車況 (未來可擴充定檢)
        if db_vehicle.status != models.VehicleStatusEnum.active:
             raise ValueError(f"車輛 {db_vehicle.plate_no} 目前狀態為 {db_vehicle.status.name}，禁止派車")

    # 如果沒指定車輛，或指定了且通過檢查，則建立預約
    # (簡化流程：建立即核准)
    db_reservation = models.Reservation(
        **reservation.model_dump(),
        status=models.ReservationStatusEnum.approved if reservation.vehicle_id else models.ReservationStatusEnum.pending
    )
    db.add(db_reservation)
    db.commit()
    db.refresh(db_reservation)
    return db_reservation

def get_reservation(db: Session, reservation_id: int):
    """ (R) 查詢單一預約 (含行程回報) """
    return db.query(models.Reservation).options(
        joinedload(models.Reservation.trip) # 載入行程
    ).filter(models.Reservation.id == reservation_id).first()

def get_reservations(db: Session, skip: int = 0, limit: int = 100):
    """ (R) 查詢所有預約 """
    return db.query(models.Reservation).options(
        joinedload(models.Reservation.trip)
    ).offset(skip).limit(limit).all()


# --- (新增) Trip CRUD ---

def create_trip_for_reservation(
    db: Session, 
    trip: schemas.TripCreate, 
    reservation_id: int
):
    """ (C) 為預約建立行程回報 (還車) """
    # 1. 檢查預約是否存在
    db_reservation = get_reservation(db, reservation_id)
    if not db_reservation:
        raise ValueError(f"ID 為 {reservation_id} 的預約不存在")
        
    # 2. 檢查是否已回報過
    if db_reservation.trip:
        raise ValueError(f"預約 {reservation_id} 已經回報過行程 (Trip ID: {db_reservation.trip.id})")
        
    # 3. 檢查還車的車輛/駕駛是否與預約單上一致
    if db_reservation.vehicle_id != trip.vehicle_id:
        raise ValueError("回報的車輛 ID 與預約單不符")
    if db_reservation.requester_id != trip.driver_id:
        # (未來可擴充：允許調度員指派不同駕駛)
        raise ValueError("回報的駕駛 ID 與預約申請人不符")
        
    # 4. 建立 Trip
    db_trip = models.Trip(
        **trip.model_dump(),
        reservation_id=reservation_id
    )
    db.add(db_trip)
    
    # 5. (!!! 核心) 更新預約單狀態
    db_reservation.status = models.ReservationStatusEnum.completed
    db.add(db_reservation)
    
    db.commit()
    db.refresh(db_trip)
    return db_trip