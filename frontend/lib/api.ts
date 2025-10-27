/**
 * API 客戶端
 * 封裝對後端 API 的呼叫
 */
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // 可以在這裡加入認證 token
    // const token = localStorage.getItem('token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // 處理錯誤
    if (error.response?.status === 401) {
      // 處理未授權
    }
    return Promise.reject(error);
  }
);

export interface Trip {
  id: number;
  reservation_id: number;
  vehicle_id: number;
  driver_id: number;
  odometer_start?: number | null; // 允許 null
  odometer_end?: number | null;
  fuel_liters?: string | null; // 後端 Decimal 回傳 string，允許 null
  charge_kwh?: string | null; // 新增
  evidence_photo_url?: string | null; // 新增
  notes?: string | null;
  returned_at: string;
}

export interface TaxFee {
  id: number;
  vehicle_id: number;
  fee_type: string;
  period_start: string;
  period_end: string;
  amount: string; // Decimal 會被轉為 string
  paid_on?: string;
}

export interface MaintenancePlan {
  id: number;
  vehicle_id: number;
  policy_name: string;
  interval_km?: number;
  next_due_odometer?: number;
  interval_months?: number;
  next_due_date?: string;
}

// Types
export interface Employee {
  id: number;
  emp_no: string;
  name: string;
  dept_name?: string;
  license_class?: string;
  status: 'active' | 'inactive';
  created_at: string;
}

export interface VehicleMinimal { // 可以放在 Vehicle interface 前面或後面
  id: number;
  plate_no: string;
  make?: string | null; // 可以選擇性加入 make/model
  model?: string | null;
}

export interface Vehicle {
  id: number;
  plate_no: string;
  vin?: string;
  make: string;
  model: string;
  year: number;
  powertrain?: string;
  displacement_cc: number;
  seats: number;
  vehicle_type: 'car' | 'motorcycle' | 'van' | 'truck' | 'ev_scooter' | 'other';
  status: 'active' | 'maintenance' | 'idle' | 'retired';
  created_at: string;

  updated_at?: string;
  acquired_on?: string; 
  helmet_required: boolean;

  // 關聯欄位
  documents: VehicleDocument[];
  assets: VehicleAsset[];
  insurances: Insurance[];
  inspections: Inspection[];
  violations: Violation[];
  maintenance_plans: MaintenancePlan[];
  work_orders: WorkOrder[];
  taxes_fees: TaxFee[];
  reservations: Reservation[];
  trips: Trip[];
  // --------------------------------
}

export interface VehicleDocument {
  id: number;
  vehicle_id: number;
  doc_type: string;
  file_url: string;
  sha256?: string;
  issued_on?: string;
  expires_on?: string;
  tags?: string;
}

export interface VehicleAsset {
  id: number;
  vehicle_id?: number;
  asset_type: string;
  serial_no: string;
  status: string;
  expires_on?: string;
  notes?: string;
}

export interface Vendor { // 加入 Vendor interface
  id: number;
  name: string;
  category: string;
  contact?: string | null;
  notes?: string | null;
  created_at: string;
}

export interface Insurance {
  id: number;
  vehicle_id: number;
  policy_type: string;
  policy_no: string;
  insurer_id?: number;
  coverage?: string;
  effective_on: string;
  expires_on: string;
  premium?: string;
}

export interface Inspection {
  id: number;
  vehicle_id: number;
  inspection_type: string;
  result: string;
  inspection_date?: string;
  next_due_date?: string;
}

export interface Violation {
  id: number;
  vehicle_id: number;
  driver_id?: number;
  law_ref?: string;
  violation_date: string;
  amount: string;
  points: number;
  paid_on?: string;
  status: string;
}

export interface Reservation {
  id: number;
  requester_id: number;
  vehicle_id?: number | null; // 允許 null
  purpose: string;
  vehicle_type_pref?: string;
  start_ts: string;
  end_ts: string;
  status: string;
  destination?: string | null; // 允許 null
  created_at: string;
  trip?: Trip | null; // <--- 新增 trip 欄位，允許 null
}

export interface WorkOrder {
  id: number;
  vehicle_id: number;
  type: string;
  status: string;
  vendor_id?: number | null; // 允許 null
  scheduled_on?: string | null; // 允許 null
  completed_on?: string | null; // 允許 null
  cost_amount?: string | null; // 允許 null
  invoice_doc_id?: number | null; // 根據 schema.py 加入
  notes?: string | null; // 允許 null
  odometer_at_service?: number | null;
  created_at: string;
  updated_at?: string | null;
  vendor?: Vendor | null;
  vehicle?: VehicleMinimal | null;
}

export interface TripCreatePayload { // 定義 TripCreate 的型別
    vehicle_id: number;
    driver_id: number;
    odometer_start?: number | null;
    odometer_end?: number | null;
    fuel_liters?: number | string | null; // 允許前端送數字或字串 (zod 會處理)
    charge_kwh?: number | string | null;
    evidence_photo_url?: string | null;
    notes?: string | null;
}

// API functions
export const apiClient = {
  // Employees
  getEmployees: () => api.get<Employee[]>('/api/v1/employees/'),
  getEmployee: (id: number) => api.get<Employee>(`/api/v1/employees/${id}`),
  createEmployee: (data: any) => api.post<Employee>('/api/v1/employees/', data),

  // Vehicles
  getVehicles: () => api.get<Vehicle[]>('/api/v1/vehicles/'),
  getVehicle: (id: number) => api.get<Vehicle>(`/api/v1/vehicles/${id}`),
  getVehicleByPlate: (plateNo: string) => api.get<Vehicle>(`/api/v1/vehicles/plate/${plateNo}`),
  createVehicle: (data: any) => api.post<Vehicle>('/api/v1/vehicles/', data),
  updateVehicle: (id: number, data: any) => api.put<Vehicle>(`/api/v1/vehicles/${id}`, data),
  deleteVehicle: (id: number) => api.delete<Vehicle>(`/api/v1/vehicles/${id}`),

  // Reservations
  getReservations: () => api.get<Reservation[]>('/api/v1/reservations/'),
  getReservation: (id: number) => api.get<Reservation>(`/api/v1/reservations/${id}`),
  createReservation: (data: any) => api.post<Reservation>('/api/v1/reservations/', data),
  updateReservation: (id: number, data: any) => api.patch<Reservation>(`/api/v1/reservations/${id}/`, data),

  // Work Orders
  getWorkOrder: (id: number) => api.get<WorkOrder>(`/api/v1/work-orders/${id}`),
  getWorkOrders: (vehicleId?: number) => 
    vehicleId 
      ? api.get<WorkOrder[]>(`/api/v1/vehicles/${vehicleId}/work-orders/`)
      : api.get<WorkOrder[]>('/api/v1/work-orders/'),
  createWorkOrder: (data: any) => api.post<WorkOrder>('/api/v1/work-orders/', data),
  updateWorkOrder: (id: number, data: any) => api.put<WorkOrder>(`/api/v1/work-orders/${id}`, data),
  deleteWorkOrder: (id: number) => api.delete(`/api/v1/work-orders/${id}`),
  
  // Insurances
  getInsurances: (vehicleId: number) => api.get<Insurance[]>(`/api/v1/vehicles/${vehicleId}/insurances/`),
  createInsurance: (data: any) => api.post<Insurance>('/api/v1/insurances/', data),

  // Inspections
  getInspections: (vehicleId: number) => api.get<Inspection[]>(`/api/v1/vehicles/${vehicleId}/inspections/`),
  createInspection: (data: any) => api.post<Inspection>('/api/v1/inspections/', data),

  // Violations
  createViolation: (data: any) => api.post<Violation>('/api/v1/violations/', data),

  // Analytics
  getVehicleUtilization: (vehicleId: number, startDate: string, endDate: string) =>
    api.get(`/api/v1/analytics/vehicle-utilization/${vehicleId}`, {
      params: { start_date: startDate, end_date: endDate },
    }),
  getComplianceReport: (daysAhead: number = 30) =>
    api.get('/api/v1/analytics/compliance-report', { params: { days_ahead: daysAhead } }),

  // Trips
  createTrip: (reservationId: number, data: any) => 
    api.post<Trip>(`/api/v1/reservations/${reservationId}/trip/`, data),
  // Vendors
  getVendors: () => api.get<Vendor[]>('/api/v1/vendors/'),
};

export default api;


