# 檔案名稱: schemas.py
from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import List, Optional, Any
from decimal import Decimal

# 匯入我們在 models.py 中定義的 Enum
from models import (
    VehicleTypeEnum, VehicleStatusEnum, EmployeeStatusEnum,
    DocumentTypeEnum, AssetTypeEnum, AssetStatusEnum,
    VendorCategoryEnum, WorkOrderTypeEnum, WorkOrderStatusEnum,
    InsurancePolicyTypeEnum, FeeTypeEnum, InspectionTypeEnum, 
    InspectionResultEnum, ViolationStatusEnum,
    ReservationPurposeEnum, ReservationStatusEnum
)

# --- Trip Schemas ---
class TripBase(BaseModel):
    odometer_start: int | None = None
    odometer_end: int | None = None
    fuel_liters: Decimal | None = None
    charge_kwh: Decimal | None = None
    evidence_photo_url: str | None = None
    notes: str | None = None

class TripCreate(TripBase):
    # 建立時，必須指定 vehicle_id 和 driver_id
    vehicle_id: int
    driver_id: int

class Trip(TripBase):
    id: int
    reservation_id: int
    vehicle_id: int
    driver_id: int
    returned_at: datetime
    
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

# --- Reservation Schemas ---
class ReservationBase(BaseModel):
    purpose: ReservationPurposeEnum
    vehicle_type_pref: VehicleTypeEnum | None = None
    start_ts: datetime # 預計開始時間 (含時區 e.g., 2025-10-25T09:00:00+08:00)
    end_ts: datetime   # 預計結束時間
    destination: str | None = None

class ReservationCreate(ReservationBase):
    # 建立時，必須指定申請人
    requester_id: int
    # 建立時，可(選填)直接指定車輛
    vehicle_id: int | None = None 

class Reservation(ReservationBase):
    id: int
    requester_id: int
    vehicle_id: int | None = None
    status: ReservationStatusEnum
    created_at: datetime
    updated_at: datetime | None = None
    
    # 巢狀回傳還車時的行程
    trip: Optional[Trip] = None
    
    model_config = ConfigDict(from_attributes=True)

class ReservationUpdate(BaseModel):
    """(U) 更新預約時用的 Schema"""
    status: Optional[ReservationStatusEnum] = None
    vehicle_id: Optional[int] = None

class ViolationBase(BaseModel):
    vehicle_id: int
    driver_id: int | None = None
    law_ref: str | None = None
    violation_date: datetime
    amount: Decimal
    points: int = 0
    paid_on: date | None = None
    ticket_doc_id: int | None = None
    status: ViolationStatusEnum = ViolationStatusEnum.open

class ViolationCreate(ViolationBase):
    pass

class Violation(ViolationBase):
    id: int
    created_at: datetime
    
    # (選填) 巢狀回傳駕駛員 (避免循環參照)
    # driver: Optional[Employee] = None # <- 這會造成循環 import
    
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

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
    violations: List[Violation] = [] # 顯示該員工的違規紀錄
    reservations_requested: List[Reservation] = []
    trips_driven: List[Trip] = []
    model_config = ConfigDict(from_attributes=True)

class EmployeeUpdate(BaseModel):
    """(U) 更新員工時用的 Schema"""
    # emp_no (員工編號) 通常不允許修改
    name: Optional[str] = None
    dept_name: Optional[str] = None
    license_class: Optional[str] = None
    status: Optional[EmployeeStatusEnum] = None

    model_config = ConfigDict(extra='forbid') # 不允許 schema 外的欄位

# --- VehicleDocument Schemas ---
class VehicleDocumentBase(BaseModel):
    doc_type: DocumentTypeEnum
    # (!!! file_url 和 sha256 移到下面 !!!)
    # file_url: str 
    # sha256: str | None = None
    issued_on: date | None = None
    expires_on: date | None = None
    tags: str | None = None

class VehicleDocumentCreate(VehicleDocumentBase):
    # 建立時，我們稍後會從 API 路徑 (path) 傳入 vehicle_id
    # 所以 body 裡面不需要 vehicle_id
    # 現在只需要文件的元資料
    # file_url 和 sha256 會在 API 層從檔案上傳結果取得
    pass

class VehicleDocument(VehicleDocumentBase):
    """(R) 讀取/回傳時用的 Schema"""
    id: int
    vehicle_id: int
    created_at: datetime
    file_url: str 
    sha256: str | None = None    
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

class WorkOrderUpdate(BaseModel):
    """(U) 更新工單時用的 Schema"""
    # 這裡列出允許前端更新的欄位
    # 通常 vehicle_id 和 type 不允許變更
    status: Optional[WorkOrderStatusEnum] = None
    vendor_id: Optional[int] = None
    scheduled_on: Optional[date] = None
    completed_on: Optional[date] = None
    cost_amount: Optional[Decimal] = None
    invoice_doc_id: Optional[int] = None # 允許更新關聯的發票
    notes: Optional[str] = None
    odometer_at_service: Optional[int] = None

    # Pydantic v2: Use model_config
    model_config = ConfigDict(extra='forbid', arbitrary_types_allowed=True) # 不允許 schema 外的欄位, 允許 Decimal
    
# --- Insurance Schemas ---
class InsuranceBase(BaseModel):
    vehicle_id: int
    policy_type: InsurancePolicyTypeEnum
    policy_no: str
    insurer_id: int | None = None # 供應商 ID (保險公司)
    coverage: str | None = None
    effective_on: date
    expires_on: date
    premium: Decimal | None = None

class InsuranceCreate(InsuranceBase):
    pass

class Insurance(InsuranceBase):
    id: int
    created_at: datetime
    
    # (選填) 巢狀回傳保險公司資訊
    insurer: Optional[Vendor] = None 
    
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

# --- TaxFee Schemas ---
class TaxFeeBase(BaseModel):
    vehicle_id: int
    fee_type: FeeTypeEnum
    period_start: date
    period_end: date
    amount: Decimal
    paid_on: date | None = None
    evidence_doc_id: int | None = None

class TaxFeeCreate(TaxFeeBase):
    pass

class TaxFee(TaxFeeBase):
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

# --- Inspection Schemas ---
class InspectionBase(BaseModel):
    vehicle_id: int
    inspection_type: InspectionTypeEnum
    result: InspectionResultEnum = InspectionResultEnum.pending
    inspection_date: date | None = None
    next_due_date: date | None = None
    inspector_id: int | None = None # 供應商 ID (檢驗站)
    cert_doc_id: int | None = None

class InspectionCreate(InspectionBase):
    pass

class Inspection(InspectionBase):
    id: int
    created_at: datetime
    
    # (選填) 巢狀回傳檢驗站資訊
    inspector: Optional[Vendor] = None
    
    model_config = ConfigDict(from_attributes=True)

class VehicleBasic(BaseModel):
    """(R) 用於列表顯示的基本車輛資訊 Schema"""
    id: int
    plate_no: str
    make: Optional[str] = None
    model: Optional[str] = None
    vehicle_type: Optional[VehicleTypeEnum] = None
    status: VehicleStatusEnum

    model_config = ConfigDict(from_attributes=True) # 允許從 ORM 物件轉換

class VehicleBase(BaseModel):
    plate_no: str
    vin: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    powertrain: Optional[str] = None
    displacement_cc: Optional[int] = None
    seats: Optional[int] = None
    vehicle_type: Optional[VehicleTypeEnum] = None
    acquired_on: Optional[date] = None
    status: VehicleStatusEnum = VehicleStatusEnum.active
    helmet_required: bool = False

class VehicleCreate(VehicleBase):
    pass

class VehicleUpdate(BaseModel):
    """(U) 更新車輛時用的 Schema"""
    # 允許更新 VIN, 狀態, 里程數 (未來), etc.
    # 車牌 (plate_no) 通常不允許修改
    vin: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    powertrain: Optional[str] = None
    displacement_cc: Optional[int] = None
    seats: Optional[int] = None
    owned_or_leased: Optional[str] = None
    acquired_on: Optional[date] = None
    status: Optional[VehicleStatusEnum] = None
    helmet_required: Optional[bool] = None
    
    # model_config = ConfigDict(extra='forbid')

class Vehicle(VehicleBase):
    """(R) 讀取/回傳時用的 Schema"""
    id: int
    created_at: datetime
    updated_at: datetime | None = None
    
    # --- 巢狀回傳關聯資料 ---
    documents: List[VehicleDocument] = []
    assets: List[VehicleAsset] = []
    maintenance_plans: List[MaintenancePlan] = [] 
    work_orders: List[WorkOrder] = []            
    insurances: List[Insurance] = [] # 保險
    taxes_fees: List[TaxFee] = []     # 稅費
    inspections: List[Inspection] = [] # 檢驗
    violations: List[Violation] = []   # 違規

    reservations: List[Reservation] = [] # 這台車的所有預約
    trips: List[Trip] = []               # 這台車的所有行程
    model_config = ConfigDict(from_attributes=True)

# --- AuditLog Schemas ---
class AuditLog(BaseModel):
    id: int
    actor_id: int | None
    ts: datetime
    action: str
    entity: str
    entity_id: int
    old_value: Any | None = None # 對應 JSONB
    new_value: Any | None = None # 對應 JSONB
    ip_address: str | None
    # 巢狀回傳簡易的操作者資訊
    actor: Optional[EmployeeBase] = None # 使用 EmployeeBase 避免過多資訊
    model_config = ConfigDict(from_attributes=True)


# --- PrivacyAccessLog Schemas ---
class PrivacyAccessLog(BaseModel):
    id: int
    actor_id: int
    ts: datetime
    resource: str
    resource_id: int
    reason: str | None
    ip_address: str | None
    actor: Optional[EmployeeBase] = None
    model_config = ConfigDict(from_attributes=True)