// frontend/app/vehicles/[id]/page.tsx
'use client';

import { useQuery } from '@tanstack/react-query';
import { useParams } from 'next/navigation';
// *** 1. 修改 import：同時引入 api (default) 和 apiClient (named) ***
import api, { apiClient, Vehicle, Employee } from '@/lib/api';
import Link from 'next/link';
import { format } from 'date-fns';

export default function VehicleDetailPage() {
  const params = useParams();
  const vehicleId = parseInt(params.id as string);

  // 查詢車輛完整資料
  const { data: vehicle, isLoading: isLoadingVehicle } = useQuery<Vehicle>({
    queryKey: ['vehicle', vehicleId],
    queryFn: async () => {
      const response = await apiClient.getVehicle(vehicleId);
      return response.data;
    },
    enabled: !!vehicleId,
  });

  // 載入員工列表 (用於顯示排程的駕駛姓名)
  const { data: employees, isLoading: isLoadingEmployees } = useQuery<Employee[]>({
    queryKey: ['employees'],
    queryFn: () => apiClient.getEmployees().then(res => res.data),
  });

  // 輔助函式：根據 ID 查找員工姓名
  const getEmployeeName = (id: number) => {
    if (!employees) return `ID: ${id}`;
    const employee = employees.find(e => e.id === id);
    return employee ? employee.name : `ID: ${id}`;
  };
  
  // 組合載入狀態
  const isLoading = isLoadingVehicle || isLoadingEmployees;

  if (isLoading) {
    return <div className="text-center p-8">載入中...</div>;
  }

  if (!vehicle) {
    return <div className="text-center p-8">找不到該車輛</div>;
  }
  
  // *** 2. 修改 getFileUrl 函式 ***
  const getFileUrl = (fileUrl: string) => {
      // *** 修正：使用 'api' (Axios instance) 而不是 'apiClient' ***
      const baseUrl = api.defaults.baseURL || ''; 
      
      // fileUrl 可能是 'uploads/filename.pdf'
      // API 路由是 '/files/'
      // 我們需要移除 'uploads/' 前綴
      const relativePath = fileUrl.replace(/^uploads\//i, '');
      
      // 完整的 URL 應該是 http://localhost:8000/files/filename.pdf
      return `${baseUrl}/files/${relativePath}`;
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">{vehicle.plate_no}</h1>
          {/* 修正：使用 ?? 處理可能的 null/undefined */}
          <p className="text-gray-600">{vehicle.make || ''} {vehicle.model || ''} ({vehicle.year ?? 'N/A'})</p>
        </div>
        <div className="flex space-x-4">
            <Link
                href={`/vehicles/${vehicleId}/edit`}
                className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700"
            >
                編輯
            </Link>
            <Link href="/vehicles" className="text-gray-600 hover:text-gray-900 flex items-center">
                ← 返回列表
            </Link>
        </div>
      </div>

      {/* Basic Info */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">基本資訊</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-500">車牌號碼</p>
            <p className="font-medium">{vehicle.plate_no}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">車型</p>
            <p className="font-medium">{vehicle.vehicle_type || '-'}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">狀態</p>
            <p className="font-medium">{vehicle.status}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">排氣量</p>
            <p className="font-medium">{vehicle.displacement_cc ?? '-'} cc</p>
          </div>
        </div>
      </div>
      
      {/* 排程紀錄 (Reservations) */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">排程紀錄 (派車單)</h2>
        {vehicle.reservations.length === 0 ? (
          <p className="text-gray-500">尚無排程紀錄</p>
        ) : (
          <div className="divide-y divide-gray-200">
            {vehicle.reservations
              .sort((a, b) => new Date(b.start_ts).getTime() - new Date(a.start_ts).getTime())
              .map((res) => (
              <div key={res.id} className="py-3">
                <div className="flex justify-between items-center">
                    <p className="font-medium">
                        {getEmployeeName(res.requester_id)}
                        <span className={`ml-2 px-2 py-0.5 text-xs rounded-full ${
                            res.status === 'completed' ? 'bg-blue-100 text-blue-800' : 
                            res.status === 'approved' ? 'bg-green-100 text-green-800' :
                            res.status === 'in_progress' ? 'bg-yellow-100 text-yellow-800' :
                            res.status === 'cancelled' ? 'bg-gray-100 text-gray-800' :
                            'bg-red-100 text-red-800' // pending, rejected
                        }`}>
                            {res.status}
                        </span>
                    </p>
                    <Link href={`/reservations/${res.id}/edit`} className="text-sm text-primary-600 hover:underline">
                        管理
                    </Link>
                </div>
                <p className="text-sm text-gray-600">
                  {format(new Date(res.start_ts), 'yyyy-MM-dd HH:mm')} - {format(new Date(res.end_ts), 'yyyy-MM-dd HH:mm')}
                </p>
                <p className="text-sm text-gray-500">用途: {res.purpose} {res.destination ? `(${res.destination})` : ''}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 工單紀錄 (Work Orders) */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">工單紀錄 (維修/保養)</h2>
        {vehicle.work_orders.length === 0 ? (
          <p className="text-gray-500">尚無工單紀錄</p>
        ) : (
          <div className="divide-y divide-gray-200">
            {vehicle.work_orders
              .sort((a, b) => {
                  const dateA = a.completed_on || a.scheduled_on || a.created_at;
                  const dateB = b.completed_on || b.scheduled_on || b.created_at;
                  return new Date(dateB).getTime() - new Date(dateA).getTime();
              })
              .map((wo) => (
              <div key={wo.id} className="py-3">
                 <div className="flex justify-between items-center">
                    <p className="font-medium">
                        {wo.type}
                        <span className={`ml-2 px-2 py-0.5 text-xs rounded-full ${
                            wo.status === 'closed' || wo.status === 'completed' ? 'bg-green-100 text-green-800' : 
                            wo.status === 'in_progress' ? 'bg-blue-100 text-blue-800' :
                            'bg-gray-100 text-gray-800' // draft, pending_approval, billed
                        }`}>
                            {wo.status}
                        </span>
                    </p>
                     <Link href={`/work-orders/${wo.id}/edit`} className="text-sm text-primary-600 hover:underline">
                        管理
                    </Link>
                 </div>
                <p className="text-sm text-gray-600">
                  日期: {wo.completed_on ? format(new Date(wo.completed_on), 'yyyy-MM-dd') : (wo.scheduled_on ? `預計 ${format(new Date(wo.scheduled_on), 'yyyy-MM-dd')}` : '未排程')}
                </p>
                <p className="text-sm text-gray-500">費用: {wo.cost_amount ? `${wo.cost_amount} 元` : '-'}</p>
                {wo.notes && <p className="text-sm text-gray-500 mt-1">備註: {wo.notes}</p>}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Insurance */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">保險</h2>
        {vehicle.insurances.length === 0 ? (
          <p className="text-gray-500">尚無保險紀錄</p>
        ) : (
          <div className="divide-y divide-gray-200">
            {vehicle.insurances.map((insurance) => (
              <div key={insurance.id} className="py-3">
                <p className="font-medium">{insurance.policy_type}</p>
                <p className="text-sm text-gray-600">保單號碼: {insurance.policy_no}</p>
                <p className="text-sm text-gray-600">
                  有效期: {format(new Date(insurance.effective_on), 'yyyy-MM-dd')} ~ {format(new Date(insurance.expires_on), 'yyyy-MM-dd')}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 檢驗紀錄 (Inspections) */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">檢驗紀錄</h2>
        {vehicle.inspections.length === 0 ? (
          <p className="text-gray-500">尚無檢驗紀錄</p>
        ) : (
          <div className="divide-y divide-gray-200">
            {vehicle.inspections.map((insp) => (
              <div key={insp.id} className="py-3">
                <p className="font-medium">
                    {insp.inspection_type}
                    <span className={`ml-2 px-2 py-0.5 text-xs rounded-full ${
                        insp.result === 'passed' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                    }`}>
                        {insp.result}
                    </span>
                </p>
                <p className="text-sm text-gray-600">
                  檢驗日期: {insp.inspection_date ? format(new Date(insp.inspection_date), 'yyyy-MM-dd') : '-'}
                </p>
                <p className="text-sm text-gray-600">
                  下次應檢日: {insp.next_due_date ? format(new Date(insp.next_due_date), 'yyyy-MM-dd') : '-'}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
      
      {/* Violations */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">違規紀錄</h2>
        {vehicle.violations.length === 0 ? (
          <p className="text-gray-500">尚無違規紀錄</p>
        ) : (
          <div className="divide-y divide-gray-200">
            {vehicle.violations.map((violation) => (
              <div key={violation.id} className="py-3">
                <p className="font-medium text-red-600">罰款: {violation.amount} 元 (狀態: {violation.status})</p>
                <p className="text-sm text-gray-600">日期: {format(new Date(violation.violation_date), 'yyyy-MM-dd')}</p>
                <p className="text-sm text-gray-600">積點: {violation.points}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 文件列表 (Documents) */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">相關文件</h2>
        {vehicle.documents.length === 0 ? (
          <p className="text-gray-500">尚無文件</p>
        ) : (
          <div className="divide-y divide-gray-200">
            {vehicle.documents.map((doc) => (
              <div key={doc.id} className="py-3 flex justify-between items-center">
                <div>
                    <p className="font-medium">{doc.doc_type}</p>
                    {doc.tags && <p className="text-xs text-gray-500">{doc.tags}</p>}
                    <p className="text-sm text-gray-500">到期日: {doc.expires_on ? format(new Date(doc.expires_on), 'yyyy-MM-dd') : '-'}</p>
                </div>
                <a 
                  href={getFileUrl(doc.file_url)} 
                  target="_blank" 
                  rel="noopener noreferrer" 
                  className="text-sm text-primary-600 hover:underline"
                >
                  下載/查看
                </a>
              </div>
            ))}
          </div>
        )}
      </div>

    </div>
  );
}