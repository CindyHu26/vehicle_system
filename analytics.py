# 檔案名稱: analytics.py
"""
分析與報表功能
規格書 4.8, 11, 13
"""
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, date
from typing import Dict, List, Any
import models
from decimal import Decimal

def get_vehicle_utilization(
    db: Session, 
    vehicle_id: int, 
    start_date: date, 
    end_date: date
) -> Dict[str, Any]:
    """
    計算車輛使用率
    
    規格書 4.8: 車輛使用率報表
    """
    # 查詢該車輛在指定日期範圍內的所有已完成預約
    reservations = db.query(models.Reservation).filter(
        models.Reservation.vehicle_id == vehicle_id,
        models.Reservation.status == models.ReservationStatusEnum.completed,
        models.Reservation.start_ts >= datetime.combine(start_date, datetime.min.time()),
        models.Reservation.end_ts <= datetime.combine(end_date, datetime.max.time())
    ).all()
    
    total_hours = Decimal('0')
    total_km = Decimal('0')
    trip_count = 0
    
    for reservation in reservations:
        if reservation.trip:
            # 計算使用時數
            duration = reservation.end_ts - reservation.start_ts
            hours = Decimal(str(duration.total_seconds() / 3600))
            total_hours += hours
            
            # 計算里程
            if reservation.trip.odometer_end and reservation.trip.odometer_start:
                km = reservation.trip.odometer_end - reservation.trip.odometer_start
                total_km += Decimal(str(km))
            
            trip_count += 1
    
    # 計算總時數
    total_days = (end_date - start_date).days
    total_available_hours = Decimal(str(total_days * 24))
    
    utilization_rate = (total_hours / total_available_hours * 100) if total_available_hours > 0 else Decimal('0')
    
    return {
        "vehicle_id": vehicle_id,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "total_hours": float(total_hours),
        "total_km": float(total_km),
        "trip_count": trip_count,
        "utilization_rate": float(utilization_rate)
    }


def get_cost_per_km(
    db: Session,
    vehicle_id: int,
    start_date: date,
    end_date: date
) -> Dict[str, Any]:
    """
    計算每公里成本 (TCO)
    
    規格書 4.8: 每公里成本
    """
    # 1. 計算總行駛里程
    trips = db.query(models.Trip).join(models.Reservation).filter(
        models.Trip.vehicle_id == vehicle_id,
        models.Reservation.status == models.ReservationStatusEnum.completed,
        models.Reservation.start_ts >= datetime.combine(start_date, datetime.min.time()),
        models.Reservation.end_ts <= datetime.combine(end_date, datetime.max.time())
    ).all()
    
    total_km = Decimal('0')
    for trip in trips:
        if trip.odometer_end and trip.odometer_start:
            km = trip.odometer_end - trip.odometer_start
            total_km += Decimal(str(km))
    
    # 2. 計算總成本
    # - 維護工單
    work_orders = db.query(models.WorkOrder).filter(
        models.WorkOrder.vehicle_id == vehicle_id,
        models.WorkOrder.status == models.WorkOrderStatusEnum.closed,
        models.WorkOrder.completed_on >= start_date,
        models.WorkOrder.completed_on <= end_date
    ).all()
    
    maintenance_cost = sum(wo.cost_amount or Decimal('0') for wo in work_orders)
    
    # - 罰單
    violations = db.query(models.Violation).filter(
        models.Violation.vehicle_id == vehicle_id,
        models.Violation.paid_on >= start_date,
        models.Violation.paid_on <= end_date
    ).all()
    
    fine_cost = sum(v.amount for v in violations if v.status == models.ViolationStatusEnum.paid)
    
    # - 稅費 (比例分配)
    taxes_fees = db.query(models.TaxFee).filter(
        models.TaxFee.vehicle_id == vehicle_id,
        models.TaxFee.period_start <= end_date,
        models.TaxFee.period_end >= start_date
    ).all()
    
    total_cost = maintenance_cost + fine_cost
    # 稅費按實際使用天數比例計算
    for tf in taxes_fees:
        period_days = (tf.period_end - tf.period_start).days + 1
        actual_days = min(end_date, tf.period_end) - max(start_date, tf.period_start)
        ratio = actual_days.days / period_days if period_days > 0 else 0
        total_cost += tf.amount * Decimal(str(ratio))
    
    # 3. 計算每公里成本
    cost_per_km = total_cost / total_km if total_km > 0 else Decimal('0')
    
    return {
        "vehicle_id": vehicle_id,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "total_km": float(total_km),
        "maintenance_cost": float(maintenance_cost),
        "fine_cost": float(fine_cost),
        "total_cost": float(total_cost),
        "cost_per_km": float(cost_per_km)
    }


def get_compliance_report(
    db: Session,
    days_ahead: int = 30
) -> Dict[str, Any]:
    """
    合規性報表
    
    規格書 4.8, 11: 合規完成率
    """
    today = date.today()
    target_date = today + timedelta(days=days_ahead)
    
    # 查詢所有車輛
    vehicles = db.query(models.Vehicle).filter(
        models.Vehicle.status != models.VehicleStatusEnum.retired
    ).all()
    
    compliance_items = []
    
    for vehicle in vehicles:
        item = {
            "vehicle_id": vehicle.id,
            "plate_no": vehicle.plate_no,
            "vehicle_type": vehicle.vehicle_type.name,
            "status": vehicle.status.name,
            "issues": []
        }
        
        # 檢查強制險
        cali_valid = False
        for ins in vehicle.insurances:
            if ins.policy_type == models.InsurancePolicyTypeEnum.CALI and ins.expires_on >= today:
                if ins.expires_on <= target_date:
                    item["issues"].append(f"強制險將於 {ins.expires_on} 到期")
                cali_valid = True
                break
        
        if not cali_valid:
            item["issues"].append("強制險已過期或不存在")
        
        # 檢查四輪定檢
        if vehicle.vehicle_type in (models.VehicleTypeEnum.car, models.VehicleTypeEnum.van, models.VehicleTypeEnum.truck):
            inspection_valid = False
            for insp in vehicle.inspections:
                if insp.inspection_type == models.InspectionTypeEnum.periodic:
                    if insp.next_due_date and insp.next_due_date >= today:
                        if insp.next_due_date <= target_date:
                            item["issues"].append(f"定檢將於 {insp.next_due_date} 到期")
                        inspection_valid = True
                        break
            
            if not inspection_valid:
                item["issues"].append("定檢已過期或不存在")
        
        # 檢查機車排氣定檢
        elif vehicle.vehicle_type == models.VehicleTypeEnum.motorcycle:
            emission_valid = False
            for insp in vehicle.inspections:
                if insp.inspection_type == models.InspectionTypeEnum.emission:
                    if insp.next_due_date and insp.next_due_date >= today:
                        if insp.next_due_date <= target_date:
                            item["issues"].append(f"排氣定檢將於 {insp.next_due_date} 到期")
                        emission_valid = True
                        break
            
            if not emission_valid:
                item["issues"].append("排氣定檢已過期或不存在")
        
        compliance_items.append(item)
    
    # 計算合規率
    compliant_count = sum(1 for item in compliance_items if len(item["issues"]) == 0)
    total_count = len(compliance_items)
    compliance_rate = (compliant_count / total_count * 100) if total_count > 0 else 0
    
    return {
        "report_date": today.isoformat(),
        "days_ahead": days_ahead,
        "total_vehicles": total_count,
        "compliant_vehicles": compliant_count,
        "compliance_rate": round(compliance_rate, 2),
        "items": compliance_items
    }


def get_violation_stats(
    db: Session,
    start_date: date,
    end_date: date
) -> Dict[str, Any]:
    """
    違規統計
    
    規格書 4.5: 違規統計與積點風險
    """
    violations = db.query(models.Violation).filter(
        models.Violation.violation_date >= datetime.combine(start_date, datetime.min.time()),
        models.Violation.violation_date <= datetime.combine(end_date, datetime.max.time())
    ).all()
    
    # 按車輛統計
    vehicle_stats = {}
    for v in violations:
        if v.vehicle_id not in vehicle_stats:
            vehicle_stats[v.vehicle_id] = {"count": 0, "total_amount": Decimal('0'), "total_points": 0}
        vehicle_stats[v.vehicle_id]["count"] += 1
        vehicle_stats[v.vehicle_id]["total_amount"] += v.amount
        vehicle_stats[v.vehicle_id]["total_points"] += v.points
    
    # 按駕駛統計
    driver_stats = {}
    for v in violations:
        if v.driver_id:
            if v.driver_id not in driver_stats:
                driver_stats[v.driver_id] = {"count": 0, "total_amount": Decimal('0'), "total_points": 0}
            driver_stats[v.driver_id]["count"] += 1
            driver_stats[v.driver_id]["total_amount"] += v.amount
            driver_stats[v.driver_id]["total_points"] += v.points
    
    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "total_violations": len(violations),
        "total_amount": float(sum(v.amount for v in violations)),
        "vehicle_stats": {
            vid: {
                "count": stats["count"],
                "total_amount": float(stats["total_amount"]),
                "total_points": stats["total_points"]
            }
            for vid, stats in vehicle_stats.items()
        },
        "driver_stats": {
            did: {
                "count": stats["count"],
                "total_amount": float(stats["total_amount"]),
                "total_points": stats["total_points"]
            }
            for did, stats in driver_stats.items()
        }
    }


