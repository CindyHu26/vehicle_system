// frontend/app/work-orders/page.tsx
'use client';

import { useQuery } from '@tanstack/react-query';
import { apiClient, WorkOrder, Vehicle } from '@/lib/api'; // 匯入 WorkOrder 和 Vehicle 型別
import Link from 'next/link';
import { format } from 'date-fns'; // 用於格式化日期

export default function WorkOrdersPage() {
  // 1. 載入工單列表
  const { data: workOrders, isLoading: isLoadingWorkOrders } = useQuery<WorkOrder[]>({
    queryKey: ['workOrders'], // 使用 'workOrders' 作為 query key
    queryFn: async () => {
      // 預設獲取所有工單，不指定 vehicleId
      const response = await apiClient.getWorkOrders();
      return response.data;
    },
  });

  // 2. 載入車輛列表 (用於顯示車牌)
  const { data: vehicles, isLoading: isLoadingVehicles } = useQuery<Vehicle[]>({
    queryKey: ['vehicles'],
    queryFn: async () => {
      const response = await apiClient.getVehicles();
      return response.data;
    },
  });

  // 輔助函式：根據 vehicle_id 查找車牌
  const getVehiclePlateNo = (vehicleId: number) => {
    if (!vehicles) return `ID: ${vehicleId}`;
    const vehicle = vehicles.find(v => v.id === vehicleId);
    return vehicle ? vehicle.plate_no : `ID: ${vehicleId}`;
  };

  // 輔助函式：狀態徽章顏色
  const statusBadgeColor = (status: string) => {
    switch (status) {
      case 'completed':
      case 'closed':
        return 'bg-green-100 text-green-800';
      case 'in_progress':
        return 'bg-blue-100 text-blue-800';
      case 'pending_approval':
        return 'bg-yellow-100 text-yellow-800';
      case 'draft':
      case 'billed': // 待對帳也用灰色
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  // 組合載入狀態
  const isLoading = isLoadingWorkOrders || isLoadingVehicles;

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">工單管理</h1>
        {/* 新增工單按鈕 (連結暫設為 #) */}
        <Link
          href="/work-orders/new" // 未來的新增頁面路徑
          className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700"
        >
          新增工單
        </Link>
      </div>

      {isLoading ? (
        <div className="text-center p-8 bg-white rounded-lg shadow">載入中...</div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">車輛</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">類型</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">狀態</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">預計日期</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">完成日期</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {workOrders?.map((wo) => (
                  <tr key={wo.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">{wo.id}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {/* 顯示車牌，並連結到車輛詳情頁 */}
                      <Link href={`/vehicles/${wo.vehicle_id}`} className="text-primary-600 hover:text-primary-900">
                        {getVehiclePlateNo(wo.vehicle_id)}
                      </Link>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">{wo.type}</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${statusBadgeColor(wo.status)}`}>
                        {wo.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {wo.scheduled_on ? format(new Date(wo.scheduled_on), 'yyyy-MM-dd') : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {wo.completed_on ? format(new Date(wo.completed_on), 'yyyy-MM-dd') : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      {/* 管理連結 (暫設為 #) */}
                      <Link
                        href={`/work-orders/${wo.id}/edit`} // 未來的編輯頁面路徑
                        className="text-primary-600 hover:text-primary-900"
                      >
                        管理
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {/* 如果沒有工單資料 */}
            {!workOrders || workOrders.length === 0 && (
              <div className="p-6 text-center text-gray-500">
                目前尚無工單資料
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}