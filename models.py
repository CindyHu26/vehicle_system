# 檔案名稱: models.py
import enum
from sqlalchemy import (
    Column, Integer, String, Date, Enum, Boolean,
    ForeignKey, Numeric, DateTime, func, Text
)
from sqlalchemy.orm import relationship

from database import Base

# --- 列舉 (Enum) 定義 ---
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
    def __repr__(self):
        return f"<Employee(emp_no='{self.emp_no}', name='{self.name}')>"


class Vehicle(Base):
    __tablename__ = "vehicles"
    id = Column(Integer, primary_key=True, index=True)
    plate_no = Column(String(20), unique=True, nullable=False, index=True)
    vin = Column(String(50), unique=True, nullable=True, index=True)
    make = Column(String(50), comment="品牌 (e.g., Toyota, Kymco)")
    model = Column(String(100), comment="型號 (e.g., Camry, GP125)")
    year = Column(Integer, comment="出廠年份")
    powertrain = Column(String(50))
    displacement_cc = Column(Integer)
    seats = Column(Integer, default=4)
    vehicle_type = Column(Enum(VehicleTypeEnum), nullable=False, index=True)
    owned_or_leased = Column(String(20), default="owned", comment="自有或租賃")
    acquired_on = Column(Date, comment="取得日期")
    status = Column(Enum(VehicleStatusEnum), default=VehicleStatusEnum.active, nullable=False, index=True)
    helmet_required = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # --- 關聯 (Relationships) ---
    # 'documents' 屬性: 讓 Python 可以透過 vehicle.documents 存取這台車的所有文件
    documents = relationship("VehicleDocument", back_populates="vehicle")
    
    # 'assets' 屬性: 讓 Python 可以透過 vehicle.assets 存取這台車的所有備品
    assets = relationship("VehicleAsset", back_populates="vehicle")

    # --- 維護相關關聯 ---
    maintenance_plans = relationship("MaintenancePlan", back_populates="vehicle")
    work_orders = relationship("WorkOrder", back_populates="vehicle")

    def __repr__(self):
        return f"<Vehicle(plate_no='{self.plate_no}', type='{self.vehicle_type.name}')>"

# --- 車輛文件索引 ---
class VehicleDocument(Base):
    """
    5.1 車輛文件索引 (vehicle_documents)
    """
    __tablename__ = "vehicle_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 關聯回 Vehicle 表的 id
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False, index=True)
    
    doc_type = Column(Enum(DocumentTypeEnum), nullable=False, index=True)
    
    # file_url 存放檔案路徑或 S3 URL
    # 規格書 4.4 提到目前尚未上雲，我們暫時可存放 Windows 網路芳鄰路徑 (e.g., \\server\share\file.pdf)
    file_url = Column(String(1024), nullable=False)
    
    # 規格書 3.3 要求的雜湊值，用於驗證檔案完整性
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
    """
    5.1 備品資產 (vehicle_assets)
    """
    __tablename__ = "vehicle_assets"

    id = Column(Integer, primary_key=True, index=True)
    
    # 關聯回 Vehicle 表的 id (表示這個備品 "屬於" 哪台車)
    # 設為 nullable=True，允許安全帽等備品不綁定特定車輛 (共用庫)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True, index=True)
    
    asset_type = Column(Enum(AssetTypeEnum), nullable=False, index=True)
    
    # 規格書 4.1 提到的編碼
    serial_no = Column(String(100), unique=True, index=True, comment="資產編號/序號")
    
    # 規格書 4.1 提到的有效期 (e.g., 安全帽建議 3 年更換)
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
    """
    5.1 供應商 (vendors)
    """
    __tablename__ = "vendors"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    category = Column(Enum(VendorCategoryEnum), nullable=False, index=True)
    contact = Column(String(255), nullable=True, comment="聯絡人/電話/Email")
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # --- 關聯 ---
    work_orders = relationship("WorkOrder", back_populates="vendor")

    def __repr__(self):
        return f"<Vendor(name='{self.name}', category='{self.category.name}')>"


# --- 保養計畫 ---
class MaintenancePlan(Base):
    """
    5.3 保養計畫 (maintenance_plans)
    """
    __tablename__ = "maintenance_plans"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False, index=True)
    
    # 規格書 4.3 範例: '每 10,000 km 或 6 個月'
    # 我們將其拆分為可計算的欄位
    
    policy_name = Column(String(255), comment="計畫名稱 (e.g., 原廠定保, 換機油)")
    
    # 依里程
    interval_km = Column(Integer, nullable=True, comment="間隔公里數 (e.g., 5000)")
    next_due_odometer = Column(Integer, nullable=True, comment="下次到期里程數")
    
    # 依時間
    interval_months = Column(Integer, nullable=True, comment="間隔月數 (e.g., 6)")
    next_due_date = Column(Date, nullable=True, comment="下次到期日期")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # --- 關聯 ---
    vehicle = relationship("Vehicle", back_populates="maintenance_plans")

    def __repr__(self):
        return f"<MaintenancePlan(vehicle_id={self.vehicle_id}, policy='{self.policy_name}')>"


# --- 維護工單 ---
class WorkOrder(Base):
    """
    5.3 工單 (work_orders)
    """
    __tablename__ = "work_orders"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False, index=True)
    
    type = Column(Enum(WorkOrderTypeEnum), nullable=False, index=True)
    status = Column(Enum(WorkOrderStatusEnum), default=WorkOrderStatusEnum.draft, nullable=False, index=True)
    
    # 關聯供應商
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=True, index=True)
    
    scheduled_on = Column(Date, nullable=True, comment="預計執行日期")
    completed_on = Column(Date, nullable=True, comment="實際完成日期")
    
    # 規格書 15. 金額用 numeric(14,2)
    cost_amount = Column(Numeric(14, 2), nullable=True)
    
    # 關聯發票 (規格書 5.3)
    invoice_doc_id = Column(Integer, ForeignKey("vehicle_documents.id"), nullable=True)
    
    notes = Column(Text, nullable=True, comment="工單說明 (e.g., 更換煞車來令片)")
    
    # 紀錄當時的里程數
    odometer_at_service = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # --- 關聯 ---
    vehicle = relationship("Vehicle", back_populates="work_orders")
    vendor = relationship("Vendor", back_populates="work_orders")
    
    # 讓工單可以反查發票文件
    invoice_document = relationship("VehicleDocument")

    def __repr__(self):
        return f"<WorkOrder(id={self.id}, type='{self.type.name}', status='{self.status.name}')>"