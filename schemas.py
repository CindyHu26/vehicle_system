# 檔案名稱: schemas.py
from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import List, Optional
from decimal import Decimal

# 匯入我們在 models.py 中定義的 Enum
from models import (
    VehicleTypeEnum, VehicleStatusEnum, EmployeeStatusEnum,
    DocumentTypeEnum, AssetTypeEnum, AssetStatusEnum,
    VendorCategoryEnum, WorkOrderTypeEnum, WorkOrderStatusEnum
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


# --- VehicleDocument Schemas ---
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

# --- Vendor Schemas ---
class VendorBase(BaseModel):
    name: str
    category: VendorCategoryEnum
    contact: str | None = None
    notes: str | None = None

class VendorCreate(VendorBase):
    pass

class Vendor(VendorBase):
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# --- MaintenancePlan Schemas ---
class MaintenancePlanBase(BaseModel):
    policy_name: str
    interval_km: int | None = None
    next_due_odometer: int | None = None
    interval_months: int | None = None
    next_due_date: date | None = None

class MaintenancePlanCreate(MaintenancePlanBase):
    # 建立時計畫時，必須指定 vehicle_id
    # 但我們會從 URL 傳入，所以 body 中不用
    pass

class MaintenancePlan(MaintenancePlanBase):
    id: int
    vehicle_id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# --- WorkOrder Schemas ---
class WorkOrderBase(BaseModel):
    type: WorkOrderTypeEnum
    status: WorkOrderStatusEnum = WorkOrderStatusEnum.draft
    vendor_id: int | None = None
    scheduled_on: date | None = None
    completed_on: date | None = None
    cost_amount: Decimal | None = None # 使用 Decimal 處理金額
    invoice_doc_id: int | None = None
    notes: str | None = None
    odometer_at_service: int | None = None

class WorkOrderCreate(WorkOrderBase):
    # 建立工單時，必須指定 vehicle_id
    vehicle_id: int

class WorkOrder(WorkOrderBase):
    id: int
    vehicle_id: int
    created_at: datetime
    updated_at: datetime | None = None

    # (選填) 巢狀回傳供應商的簡易資訊
    vendor: Optional[Vendor] = None # Optional 表示可以是 None
    
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True) # 允許 Decimal

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

class Vehicle(VehicleBase):
    """(R) 讀取/回傳時用的 Schema"""
    id: int
    created_at: datetime
    updated_at: datetime | None = None
    
    # --- (擴充) 巢狀回傳關聯資料 ---
    documents: List[VehicleDocument] = []
    assets: List[VehicleAsset] = []
    maintenance_plans: List[MaintenancePlan] = [] 
    work_orders: List[WorkOrder] = []            
    
    model_config = ConfigDict(from_attributes=True)