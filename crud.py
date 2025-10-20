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
    (!!! 修改 !!!) 使用 joinedload 主動載入關聯資料
    """
    return db.query(models.Vehicle).options(
        joinedload(models.Vehicle.documents), # 載入文件
        joinedload(models.Vehicle.assets)    # 載入備品
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
        joinedload(models.Vehicle.assets)    # 載入備品
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