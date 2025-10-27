# 檔案名稱: import_data.py
"""
資料匯入功能
規格書 10: 整備與資料導入
"""
import csv
from sqlalchemy.orm import Session
from datetime import datetime
from decimal import Decimal
import models
import crud
import schemas
from models import (
    VehicleTypeEnum, VehicleStatusEnum, EmployeeStatusEnum,
    DocumentTypeEnum, AssetTypeEnum, AssetStatusEnum,
    VendorCategoryEnum, WorkOrderTypeEnum, WorkOrderStatusEnum,
    InsurancePolicyTypeEnum, FeeTypeEnum, InspectionTypeEnum,
    InspectionResultEnum, ViolationStatusEnum,
    ReservationPurposeEnum, ReservationStatusEnum
)


def import_employees_from_csv(db: Session, file_path: str) -> tuple[int, list[str]]:
    """
    從 CSV 匯入員工資料
    
    CSV 格式：
    emp_no, name, dept_name, license_class
    """
    errors = []
    success_count = 0
    
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                employee = schemas.EmployeeCreate(
                    emp_no=row['emp_no'],
                    name=row['name'],
                    dept_name=row.get('dept_name'),
                    license_class=row.get('license_class'),
                    status=EmployeeStatusEnum.active
                )
                crud.create_employee(db, employee)
                success_count += 1
            except Exception as e:
                errors.append(f"員工 {row.get('emp_no')}: {e}")
    
    return success_count, errors


def import_vehicles_from_csv(db: Session, file_path: str) -> tuple[int, list[str]]:
    """
    從 CSV 匯入車輛資料
    
    CSV 格式：
    plate_no, vin, make, model, year, powertrain, displacement_cc, seats, 
    vehicle_type, acquired_on, status
    """
    errors = []
    success_count = 0
    
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                vehicle = schemas.VehicleCreate(
                    plate_no=row['plate_no'],
                    vin=row.get('vin'),
                    make=row['make'],
                    model=row['model'],
                    year=int(row['year']),
                    powertrain=row.get('powertrain'),
                    displacement_cc=int(row.get('displacement_cc', 0)),
                    seats=int(row.get('seats', 4)),
                    vehicle_type=VehicleTypeEnum(row['vehicle_type']),
                    acquired_on=datetime.strptime(row['acquired_on'], '%Y-%m-%d').date() if row.get('acquired_on') else None,
                    status=VehicleStatusEnum(row.get('status', 'active')),
                    helmet_required=VehicleTypeEnum(row['vehicle_type']) in (VehicleTypeEnum.motorcycle, VehicleTypeEnum.ev_scooter)
                )
                crud.create_vehicle(db, vehicle)
                success_count += 1
            except Exception as e:
                errors.append(f"車輛 {row.get('plate_no')}: {e}")
    
    return success_count, errors


def import_vendors_from_csv(db: Session, file_path: str) -> tuple[int, list[str]]:
    """
    從 CSV 匯入供應商資料
    
    CSV 格式：
    name, category, contact, notes
    """
    errors = []
    success_count = 0
    
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                vendor = schemas.VendorCreate(
                    name=row['name'],
                    category=VendorCategoryEnum(row['category']),
                    contact=row.get('contact'),
                    notes=row.get('notes')
                )
                crud.create_vendor(db, vendor)
                success_count += 1
            except Exception as e:
                errors.append(f"供應商 {row.get('name')}: {e}")
    
    return success_count, errors


def import_insurances_from_csv(db: Session, file_path: str) -> tuple[int, list[str]]:
    """
    從 CSV 匯入保險資料
    
    CSV 格式：
    vehicle_id, policy_type, policy_no, insurer_id, coverage, 
    effective_on, expires_on, premium
    """
    errors = []
    success_count = 0
    
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                insurance = schemas.InsuranceCreate(
                    vehicle_id=int(row['vehicle_id']),
                    policy_type=InsurancePolicyTypeEnum(row['policy_type']),
                    policy_no=row['policy_no'],
                    insurer_id=int(row['insurer_id']) if row.get('insurer_id') else None,
                    coverage=row.get('coverage'),
                    effective_on=datetime.strptime(row['effective_on'], '%Y-%m-%d').date(),
                    expires_on=datetime.strptime(row['expires_on'], '%Y-%m-%d').date(),
                    premium=Decimal(row['premium']) if row.get('premium') else None
                )
                crud.create_insurance(db, insurance)
                success_count += 1
            except Exception as e:
                errors.append(f"保險 {row.get('policy_no')}: {e}")
    
    return success_count, errors


def import_tax_fees_from_csv(db: Session, file_path: str) -> tuple[int, list[str]]:
    """
    從 CSV 匯入稅費資料
    
    CSV 格式：
    vehicle_id, fee_type, period_start, period_end, amount, paid_on
    """
    errors = []
    success_count = 0
    
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                tax_fee = schemas.TaxFeeCreate(
                    vehicle_id=int(row['vehicle_id']),
                    fee_type=FeeTypeEnum(row['fee_type']),
                    period_start=datetime.strptime(row['period_start'], '%Y-%m-%d').date(),
                    period_end=datetime.strptime(row['period_end'], '%Y-%m-%d').date(),
                    amount=Decimal(row['amount']),
                    paid_on=datetime.strptime(row['paid_on'], '%Y-%m-%d').date() if row.get('paid_on') else None
                )
                crud.create_tax_fee(db, tax_fee)
                success_count += 1
            except Exception as e:
                errors.append(f"稅費: {e}")
    
    return success_count, errors


def import_inspections_from_csv(db: Session, file_path: str) -> tuple[int, list[str]]:
    """
    從 CSV 匯入檢驗資料
    
    CSV 格式：
    vehicle_id, inspection_type, result, inspection_date, next_due_date, inspector_id
    """
    errors = []
    success_count = 0
    
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                inspection = schemas.InspectionCreate(
                    vehicle_id=int(row['vehicle_id']),
                    inspection_type=InspectionTypeEnum(row['inspection_type']),
                    result=InspectionResultEnum(row.get('result', 'pending')),
                    inspection_date=datetime.strptime(row['inspection_date'], '%Y-%m-%d').date() if row.get('inspection_date') else None,
                    next_due_date=datetime.strptime(row['next_due_date'], '%Y-%m-%d').date() if row.get('next_due_date') else None,
                    inspector_id=int(row['inspector_id']) if row.get('inspector_id') else None
                )
                crud.create_inspection(db, inspection)
                success_count += 1
            except Exception as e:
                errors.append(f"檢驗: {e}")
    
    return success_count, errors


