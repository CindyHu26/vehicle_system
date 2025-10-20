# 檔案名稱: schemas.py
from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import List # <-- (新增)

# 匯入我們在 models.py 中定義的 Enum
from models import (
    VehicleTypeEnum, VehicleStatusEnum, EmployeeStatusEnum,
    DocumentTypeEnum, AssetTypeEnum, AssetStatusEnum # <-- (新增)
)

# --- Employee Schemas ---
class EmployeeBase(BaseModel):
    emp_no: str
    name: str
    dept_name: str | None = None
    license_class: str | None = None
    status: EmployeeStatusEnum = EmployeeStatusEnum.active

class EmployeeCreate(EmployeeBase):
    pass

class Employee(EmployeeBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


# --- (新增) VehicleDocument Schemas ---

class VehicleDocumentBase(BaseModel):
    doc_type: DocumentTypeEnum
    file_url: str
    sha256: str | None = None
    issued_on: date | None = None
    expires_on: date | None = None
    tags: str | None = None

class VehicleDocumentCreate(VehicleDocumentBase):
    # 建立時，我們稍後會從 API 路徑 (path) 傳入 vehicle_id
    # 所以 body 裡面不需要 vehicle_id
    pass

class VehicleDocument(VehicleDocumentBase):
    """(R) 讀取/回傳時用的 Schema"""
    id: int
    vehicle_id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class VehicleAssetBase(BaseModel):
    asset_type: AssetTypeEnum
    serial_no: str # 資產編號
    status: AssetStatusEnum = AssetStatusEnum.available
    expires_on: date | None = None
    notes: str | None = None
    
    # 允許建立時就直接綁定給某台車
    vehicle_id: int | None = None 

class VehicleAssetCreate(VehicleAssetBase):
    pass

class VehicleAsset(VehicleAssetBase):
    """(R) 讀取/回傳時用的 Schema"""
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class VehicleBase(BaseModel):
    plate_no: str
    vin: str | None = None
    make: str
    model: str
    year: int
    powertrain: str | None = None
    displacement_cc: int
    seats: int = 4
    vehicle_type: VehicleTypeEnum
    acquired_on: date | None = None
    status: VehicleStatusEnum = VehicleStatusEnum.active
    helmet_required: bool = False

class VehicleCreate(VehicleBase):
    pass

class Vehicle(VehicleBase): # <-- (!!! 修改這裡 !!!)
    """(R) 讀取/回傳時用的 Schema"""
    id: int
    created_at: datetime
    updated_at: datetime | None = None
    
    # --- (新增) 巢狀回傳關聯資料 ---
    documents: List[VehicleDocument] = [] # 回傳文件清單
    assets: List[VehicleAsset] = []     # 回傳備品清單
    
    model_config = ConfigDict(from_attributes=True)