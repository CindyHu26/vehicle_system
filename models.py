# 檔案名稱: models.py
import enum
from sqlalchemy import (
    Column, Integer, String, Date, Enum, Boolean,
    ForeignKey, Numeric, DateTime, func, Text
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

from database import Base

# --- 列舉 (Enum) 定義 ---
# ... (所有 Enum 保持不變) ...
class VehicleTypeEnum(enum.Enum):
    car = "car"
    motorcycle = "motorcycle"
    van = "van"
    truck = "truck"
    ev_scooter = "ev_scooter"
    other = "other"

class VehicleStatusEnum(enum.Enum):
    active = "active"
    maintenance = "maintenance"
    idle = "idle"
    retired = "retired"

class EmployeeStatusEnum(enum.Enum):
    active = "active"
    inactive = "inactive"

class DocumentTypeEnum(str, enum.Enum):
    registration = "registration" # 行照
    insurance = "insurance"       # 保險 (強制/任意)
    contract = "contract"         # 合約 (租賃/採購)
    fine = "fine"                 # 罰單
    inspection = "inspection"     # (四輪)定檢
    emission = "emission"         # (機車)排氣定檢
    invoice = "invoice"           # 發票 (保養/維修)
    other = "other"               # 其他

class AssetTypeEnum(str, enum.Enum):
    helmet = "helmet"             # 安全帽
    lock = "lock"                 # 鎖具
    raincoat = "raincoat"         # 雨衣
    phone_mount = "phone_mount"   # 手機架
    dashcam = "dashcam"           # 行車紀錄器
    other = "other"

class AssetStatusEnum(str, enum.Enum):
    available = "available"       # 可用
    in_use = "in_use"             # 使用中
    maintenance = "maintenance"   # 維護中
    retired = "retired"           # 報廢

class VendorCategoryEnum(str, enum.Enum):
    maintenance = "maintenance"     # 維修保養廠
    insurance = "insurance"         # 保險公司
    parking = "parking"             # 停車場
    emission_check = "emission_check" # (機車)排氣定檢站
    inspection = "inspection"       # (四輪)定檢站
    other = "other"

class WorkOrderTypeEnum(str, enum.Enum):
    maintenance = "maintenance"     # 定期保養
    repair = "repair"               # 故障維修
    recall = "recall"               # 召回
    cleaning = "cleaning"           # 清潔 (洗車)
    emission_check = "emission_check" # (機車)排氣定檢
    inspection = "inspection"       # (四輪)定檢
    purification = "purification"
    other = "other"

class WorkOrderStatusEnum(str, enum.Enum):
    draft = "draft"                 # 草稿
    pending_approval = "pending_approval" # 待核准
    in_progress = "in_progress"     # 進行中
    completed = "completed"         # 完成
    billed = "billed"               # 待對帳
    closed = "closed"               # 結案

class InsurancePolicyTypeEnum(str, enum.Enum):
    CALI = "CALI"               # 強制汽車責任保險
    voluntary = "voluntary"     # 任意險
    other = "other"

class FeeTypeEnum(str, enum.Enum):
    license_tax = "license_tax" # 牌照稅
    fuel_fee = "fuel_fee"       # 燃料費
    parking_fee = "parking_fee" # 停車費 (月租等)
    other = "other"

class InspectionTypeEnum(str, enum.Enum):
    periodic = "periodic"       # (四輪) 定期檢驗
    emission = "emission"       # (機車) 排氣定期檢驗
    reinspection = "reinspection" # 複檢
    other = "other"

class InspectionResultEnum(str, enum.Enum):
    passed = "passed"
    failed = "failed"
    pending = "pending"

class ViolationStatusEnum(str, enum.Enum):
    open = "open"       # 未繳費
    paid = "paid"       # 已繳費
    appeal = "appeal"   # 申訴中
    closed = "closed"   # 結案 (申訴成功)

class ReservationPurposeEnum(str, enum.Enum):
    business = "business"   # 公務
    commute = "commute"     # 通勤
    errand = "errand"       # 跑腿/其他
    other = "other"

class ReservationStatusEnum(str, enum.Enum):
    pending = "pending"     # 待審核
    approved = "approved"   # 已核准 (待取車)
    rejected = "rejected"   # 已拒絕
    in_progress = "in_progress" # 進行中 (已取車)
    completed = "completed" # 已完成 (已還車)
    cancelled = "cancelled" # (使用者) 已取消

# --- 模型 (Table) 定義 ---
class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True, index=True)
    emp_no = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    dept_name = Column(String(100)) 
    license_class = Column(String(255), comment="駕照等級, e.g., '普通小型車,普通重型機車'")
    status = Column(Enum(EmployeeStatusEnum), default=EmployeeStatusEnum.active, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # --- (!!! MODIFICATION HERE: 加入 cascade 和 passive_deletes) ---
    violations = relationship("Violation", back_populates="driver", cascade="all, delete-orphan", passive_deletes=True)
    reservations_requested = relationship("Reservation", back_populates="requester", foreign_keys="[Reservation.requester_id]", cascade="all, delete-orphan", passive_deletes=True)
    trips_driven = relationship("Trip", back_populates="driver", cascade="all, delete-orphan", passive_deletes=True)
    # -----------------------------------------------------------------

    def __repr__(self):
        return f"<Employee(emp_no='{self.emp_no}', name='{self.name}')>"


class Vehicle(Base):
    __tablename__ = "vehicles"
    id = Column(Integer, primary_key=True, index=True)
    plate_no = Column(String(20), unique=True, nullable=False, index=True)
    vin = Column(String(50), unique=True, nullable=True, index=True)
    make = Column(String(50), nullable=True, comment="品牌 (e.g., Toyota, Kymco)")
    model = Column(String(100), nullable=True, comment="型號 (e.g., Camry, GP125)")
    year = Column(Integer, nullable=True, comment="出廠年份")
    powertrain = Column(String(50), nullable=True)
    displacement_cc = Column(Integer, nullable=True)
    seats = Column(Integer, default=4, nullable=True)
    vehicle_type = Column(Enum(VehicleTypeEnum), nullable=True, index=True)
    owned_or_leased = Column(String(20), default="owned", comment="自有或租賃")
    acquired_on = Column(Date, comment="取得日期")
    status = Column(Enum(VehicleStatusEnum), default=VehicleStatusEnum.active, nullable=False, index=True)
    helmet_required = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # --- 關聯 (Relationships) ---
    # --- (!!! MODIFICATION HERE: 加入 cascade 和 passive_deletes) ---
    documents = relationship("VehicleDocument", back_populates="vehicle", cascade="all, delete-orphan", passive_deletes=True)
    assets = relationship("VehicleAsset", back_populates="vehicle", cascade="all, delete-orphan", passive_deletes=True)
    maintenance_plans = relationship("MaintenancePlan", back_populates="vehicle", cascade="all, delete-orphan", passive_deletes=True)
    work_orders = relationship("WorkOrder", back_populates="vehicle", cascade="all, delete-orphan", passive_deletes=True)
    insurances = relationship("Insurance", back_populates="vehicle", cascade="all, delete-orphan", passive_deletes=True)
    taxes_fees = relationship("TaxFee", back_populates="vehicle", cascade="all, delete-orphan", passive_deletes=True)
    inspections = relationship("Inspection", back_populates="vehicle", cascade="all, delete-orphan", passive_deletes=True)
    violations = relationship("Violation", back_populates="vehicle", cascade="all, delete-orphan", passive_deletes=True)
    reservations = relationship("Reservation", back_populates="vehicle", cascade="all, delete-orphan", passive_deletes=True)
    trips = relationship("Trip", back_populates="vehicle", cascade="all, delete-orphan", passive_deletes=True)
    # -----------------------------------------------------------------

    def __repr__(self):
        return f"<Vehicle(plate_no='{self.plate_no}', type='{self.vehicle_type.name}')>"

# --- 借車申請 ---
class Reservation(Base):
    __tablename__ = "reservations"
    id = Column(Integer, primary_key=True, index=True)
    
    # --- (!!! MODIFICATION HERE: 加入 ondelete="SET NULL") ---
    # 這裡我們假設駕駛被刪除時，預約紀錄的申請人/駕駛可以被設為 NULL
    requester_id = Column(Integer, ForeignKey("employees.id", ondelete="SET NULL"), nullable=True, index=True)
    # -----------------------------------------------------------------
    
    # --- (!!! MODIFICATION HERE: 加入 ondelete="SET NULL") ---
    # 這裡我們假設車輛被刪除時，預約紀錄的車輛可以被設為 NULL (或 "SET DEFAULT", "RESTRICT")
    # 設為 SET NULL，表示保留預約紀錄，但車輛資訊遺失
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True, index=True)
    # -----------------------------------------------------------------
    
    purpose = Column(Enum(ReservationPurposeEnum), nullable=False)
    vehicle_type_pref = Column(Enum(VehicleTypeEnum), nullable=True, comment="偏好車種")
    start_ts = Column(DateTime(timezone=True), nullable=False, index=True, comment="預計開始時間")
    end_ts = Column(DateTime(timezone=True), nullable=False, index=True, comment="預計結束時間")
    status = Column(Enum(ReservationStatusEnum), default=ReservationStatusEnum.pending, nullable=False, index=True)
    destination = Column(String(255), nullable=True, comment="目的地")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # --- 關聯 ---
    requester = relationship("Employee", back_populates="reservations_requested", foreign_keys=[requester_id])
    vehicle = relationship("Vehicle", back_populates="reservations")
    
    # --- (!!! MODIFICATION HERE: 加入 cascade 和 passive_deletes) ---
    trip = relationship("Trip", back_populates="reservation", uselist=False, cascade="all, delete-orphan", passive_deletes=True)
    # -----------------------------------------------------------------

# --- 行程回報 ---
class Trip(Base):
    __tablename__ = "trips"
    id = Column(Integer, primary_key=True, index=True)
    
    # --- (!!! MODIFICATION HERE: 加入 ondelete="CASCADE") ---
    # 如果預約單被刪除，這筆行程回報也應該一起刪除
    reservation_id = Column(Integer, ForeignKey("reservations.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    # -----------------------------------------------------------------

    # --- (!!! MODIFICATION HERE: 加入 ondelete="SET NULL") ---
    # 假設車輛或駕駛被刪除時，行程紀錄可以保留，但關聯設為 NULL
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True, index=True)
    driver_id = Column(Integer, ForeignKey("employees.id", ondelete="SET NULL"), nullable=True, index=True)
    # -----------------------------------------------------------------

    odometer_start = Column(Integer, nullable=True, comment="出發里程數")
    odometer_end = Column(Integer, nullable=True, comment="歸還里程數")
    fuel_liters = Column(Numeric(10, 2), nullable=True, comment="加油公升數")
    charge_kwh = Column(Numeric(10, 2), nullable=True, comment="充電度數")
    evidence_photo_url = Column(String(1024), nullable=True, comment="佐證照片 URL")
    notes = Column(Text, nullable=True, comment="行程備註 (e.g., 車輛有異音)")
    returned_at = Column(DateTime(timezone=True), server_default=func.now())

    # --- 關聯 ---
    reservation = relationship("Reservation", back_populates="trip")
    vehicle = relationship("Vehicle", back_populates="trips")
    driver = relationship("Employee", back_populates="trips_driven")

# --- 車輛文件索引 ---
class VehicleDocument(Base):
    __tablename__ = "vehicle_documents"
    id = Column(Integer, primary_key=True, index=True)
    
    # --- (!!! MODIFICATION HERE: 加入 ondelete="CASCADE") ---
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    # -----------------------------------------------------------------
    
    doc_type = Column(Enum(DocumentTypeEnum), nullable=False, index=True)
    file_url = Column(String(1024), nullable=False)
    sha256 = Column(String(64), nullable=True) 
    issued_on = Column(Date, comment="文件核發日期 (e.g., 保單開始日)")
    expires_on = Column(Date, comment="文件到期日期 (e.g., 保單/行照到期日)")
    tags = Column(String(255), nullable=True, comment="標籤 (e.g., '2024年強制險')")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # --- 關聯 ---
    vehicle = relationship("Vehicle", back_populates="documents")

    def __repr__(self):
        return f"<Document(type='{self.doc_type.name}', vehicle_id={self.vehicle_id})>"


# --- 車輛備品資產 ---
class VehicleAsset(Base):
    __tablename__ = "vehicle_assets"
    id = Column(Integer, primary_key=True, index=True)
    
    # --- (!!! MODIFICATION HERE: 加入 ondelete="SET NULL") ---
    # 備品可以與車輛脫鉤，設為 SET NULL
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True, index=True)
    # -----------------------------------------------------------------
    
    asset_type = Column(Enum(AssetTypeEnum), nullable=False, index=True)
    serial_no = Column(String(100), unique=True, index=True, comment="資產編號/序號")
    expires_on = Column(Date, nullable=True, comment="資產有效期/汰換日期")
    status = Column(Enum(AssetStatusEnum), default=AssetStatusEnum.available, nullable=False)
    notes = Column(Text, nullable=True, comment="備註 (e.g., 尺寸L, 顏色藍)")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # --- 關聯 ---
    vehicle = relationship("Vehicle", back_populates="assets")
    
    def __repr__(self):
        return f"<Asset(type='{self.asset_type.name}', serial='{self.serial_no}')>"
    
# --- 供應商主檔 ---
class Vendor(Base):
    __tablename__ = "vendors"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    category = Column(Enum(VendorCategoryEnum), nullable=False, index=True)
    contact = Column(String(255), nullable=True, comment="聯絡人/電話/Email")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # --- (!!! MODIFICATION HERE: 加入 cascade 和 passive_deletes) ---
    # 如果供應商被刪除，工單/保險/檢驗 上的 vendor_id 應設為 NULL
    work_orders = relationship("WorkOrder", back_populates="vendor", cascade="all, delete-orphan", passive_deletes=True)
    insurances = relationship("Insurance", back_populates="insurer", cascade="all, delete-orphan", passive_deletes=True)
    inspections = relationship("Inspection", back_populates="inspector", cascade="all, delete-orphan", passive_deletes=True)
    # -----------------------------------------------------------------

    def __repr__(self):
        return f"<Vendor(name='{self.name}', category='{self.category.name}')>"

# --- 保養計畫 ---
class MaintenancePlan(Base):
    __tablename__ = "maintenance_plans"
    id = Column(Integer, primary_key=True, index=True)
    
    # --- (!!! MODIFICATION HERE: 加入 ondelete="CASCADE") ---
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    # -----------------------------------------------------------------
    
    policy_name = Column(String(255), comment="計畫名稱 (e.g., 原廠定保, 換機油)")
    interval_km = Column(Integer, nullable=True, comment="間隔公里數 (e.g., 5000)")
    next_due_odometer = Column(Integer, nullable=True, comment="下次到期里程數")
    interval_months = Column(Integer, nullable=True, comment="間隔月數 (e.g., 6)")
    next_due_date = Column(Date, nullable=True, comment="下次到期日期")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    vehicle = relationship("Vehicle", back_populates="maintenance_plans")

    def __repr__(self):
        return f"<MaintenancePlan(vehicle_id={self.vehicle_id}, policy='{self.policy_name}')>"

# --- 維護工單 ---
class WorkOrder(Base):
    __tablename__ = "work_orders"
    id = Column(Integer, primary_key=True, index=True)
    
    # --- (!!! MODIFICATION HERE: 加入 ondelete="CASCADE") ---
    # 這是錯誤 發生的欄位。
    # 刪除車輛時，工單也應一併刪除。
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    # -----------------------------------------------------------------

    type = Column(Enum(WorkOrderTypeEnum), nullable=False, index=True)
    status = Column(Enum(WorkOrderStatusEnum), default=WorkOrderStatusEnum.draft, nullable=False, index=True)
    
    # --- (!!! MODIFICATION HERE: 加入 ondelete="SET NULL") ---
    # 供應商刪除時，工單上的 vendor_id 設為 NULL
    vendor_id = Column(Integer, ForeignKey("vendors.id", ondelete="SET NULL"), nullable=True, index=True)
    invoice_doc_id = Column(Integer, ForeignKey("vehicle_documents.id", ondelete="SET NULL"), nullable=True)
    # -----------------------------------------------------------------

    scheduled_on = Column(Date, nullable=True, comment="預計執行日期")
    completed_on = Column(Date, nullable=True, comment="實際完成日期")
    cost_amount = Column(Numeric(14, 2), nullable=True)
    notes = Column(Text, nullable=True, comment="工單說明 (e.g., 更換煞車來令片)")
    odometer_at_service = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # --- 關聯 ---
    vehicle = relationship("Vehicle", back_populates="work_orders")
    vendor = relationship("Vendor", back_populates="work_orders")
    invoice_document = relationship("VehicleDocument")

    def __repr__(self):
        return f"<WorkOrder(id={self.id}, type='{self.type.name}', status='{self.status.name}')>"
    
# --- 保險紀錄 ---
class Insurance(Base):
    __tablename__ = "insurances"
    id = Column(Integer, primary_key=True, index=True)
    
    # --- (!!! MODIFICATION HERE: 加入 ondelete="CASCADE") ---
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    insurer_id = Column(Integer, ForeignKey("vendors.id", ondelete="SET NULL"), nullable=True)
    # -----------------------------------------------------------------
    
    policy_type = Column(Enum(InsurancePolicyTypeEnum), nullable=False)
    policy_no = Column(String(100), nullable=False, index=True, comment="保單號碼")
    coverage = Column(Text, nullable=True, comment="保額/承保範圍 (e.g., 第三人責任險 500/1000/50)")
    effective_on = Column(Date, nullable=False, comment="保單生效日")
    expires_on = Column(Date, nullable=False, index=True, comment="保單到期日")
    premium = Column(Numeric(14, 2), nullable=True, comment="保費")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    vehicle = relationship("Vehicle", back_populates="insurances")
    insurer = relationship("Vendor", back_populates="insurances")


# --- 稅費紀錄 ---
class TaxFee(Base):
    __tablename__ = "taxes_fees"
    id = Column(Integer, primary_key=True, index=True)

    # --- (!!! MODIFICATION HERE: 加入 ondelete="CASCADE") ---
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    evidence_doc_id = Column(Integer, ForeignKey("vehicle_documents.id", ondelete="SET NULL"), nullable=True)
    # -----------------------------------------------------------------

    fee_type = Column(Enum(FeeTypeEnum), nullable=False, index=True)
    period_start = Column(Date, nullable=False, comment="費用區間 (起)")
    period_end = Column(Date, nullable=False, comment="費用區間 (迄)")
    amount = Column(Numeric(14, 2), nullable=False)
    paid_on = Column(Date, nullable=True, index=True, comment="繳費日期")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    vehicle = relationship("Vehicle", back_populates="taxes_fees")
    evidence_document = relationship("VehicleDocument")


# --- 檢驗紀錄 ---
class Inspection(Base):
    __tablename__ = "inspections"
    id = Column(Integer, primary_key=True, index=True)
    
    # --- (!!! MODIFICATION HERE: 加入 ondelete="CASCADE") ---
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    inspector_id = Column(Integer, ForeignKey("vendors.id", ondelete="SET NULL"), nullable=True)
    cert_doc_id = Column(Integer, ForeignKey("vehicle_documents.id", ondelete="SET NULL"), nullable=True)
    # -----------------------------------------------------------------
    
    inspection_type = Column(Enum(InspectionTypeEnum), nullable=False, index=True)
    result = Column(Enum(InspectionResultEnum), default=InspectionResultEnum.pending)
    inspection_date = Column(Date, nullable=True, comment="實際檢驗日期")
    next_due_date = Column(Date, nullable=True, index=True, comment="下次應檢驗日期")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    vehicle = relationship("Vehicle", back_populates="inspections")
    inspector = relationship("Vendor", back_populates="inspections")
    certificate_document = relationship("VehicleDocument")


# --- 違規紀錄 ---
class Violation(Base):
    __tablename__ = "violations"
    id = Column(Integer, primary_key=True, index=True)
    
    # --- (!!! MODIFICATION HERE: 加入 ondelete="CASCADE" / "SET NULL") ---
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    driver_id = Column(Integer, ForeignKey("employees.id", ondelete="SET NULL"), nullable=True, index=True)
    ticket_doc_id = Column(Integer, ForeignKey("vehicle_documents.id", ondelete="SET NULL"), nullable=True)
    # -----------------------------------------------------------------
    
    law_ref = Column(String(255), nullable=True, comment="違反法條 (e.g., 道路交通管理處罰條例 第56條1項)")
    violation_date = Column(DateTime(timezone=True), nullable=False, comment="違規時間")
    amount = Column(Numeric(14, 2), nullable=False, comment="罰款金額")
    points = Column(Integer, default=0, comment="駕駛積點")
    paid_on = Column(Date, nullable=True, comment="繳費日期")
    status = Column(Enum(ViolationStatusEnum), default=ViolationStatusEnum.open, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    vehicle = relationship("Vehicle", back_populates="violations")
    driver = relationship("Employee", back_populates="violations")
    ticket_document = relationship("VehicleDocument")

# --- 不可竄改稽核軌跡 ---
class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    
    # --- (!!! MODIFICATION HERE: 加入 ondelete="SET NULL") ---
    actor_id = Column(Integer, ForeignKey("employees.id", ondelete="SET NULL"), nullable=True, index=True)
    # -----------------------------------------------------------------
    
    ts = Column(DateTime(timezone=True), server_default=func.now(), index=True, comment="操作時間")
    action = Column(String(50), nullable=False, index=True, comment="動作 (e.g., CREATE, UPDATE, DELETE)")
    entity = Column(String(100), nullable=False, index=True, comment="實體 (e.g., Vehicle, Violation)")
    entity_id = Column(Integer, nullable=False, index=True, comment="實體 ID")
    old_value = Column(JSONB, nullable=True, comment="舊值 (JSON)")
    new_value = Column(JSONB, nullable=True, comment="新值 (JSON)")
    ip_address = Column(String(100), nullable=True)
    user_agent = Column(String(512), nullable=True)

    actor = relationship("Employee")


# --- 敏感資料存取紀錄 ---
class PrivacyAccessLog(Base):
    __tablename__ = "privacy_access_logs"
    id = Column(Integer, primary_key=True, index=True)
    
    # --- (!!! MODIFICATION HERE: 加入 ondelete="SET NULL") ---
    actor_id = Column(Integer, ForeignKey("employees.id", ondelete="SET NULL"), nullable=True, index=True)
    # -----------------------------------------------------------------
    
    ts = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    resource = Column(String(255), nullable=False, index=True, comment="存取的資源 (e.g., Employee.license_class)")
    resource_id = Column(Integer, nullable=False, index=True, comment="資源 ID")
    reason = Column(Text, nullable=True, comment="存取原因 (e.g., 稽核罰單)")
    ip_address = Column(String(100), nullable=True)

    actor = relationship("Employee")