// frontend/app/work-orders/page.tsx
'use client';

import { useQuery } from '@tanstack/react-query';
import { apiClient, WorkOrder } from '@/lib/api'; // 只匯入 WorkOrder 型別
import Link from 'next/link';
import { format } from 'date-fns'; // 用於格式化日期

// *** 假設您在 lib/api.ts 中定義了 VehicleMinimal interface ***
// 用於 WorkOrder.vehicle 的型別
interface VehicleMinimal {
    id: number;
    plate_no: string;
    // 可能還有 make, model 等，依據後端回傳調整
}

export default function WorkOrdersPage() {
  // 1. 只載入工單列表 (假設後端已包含 vehicle)
  const { data: workOrders, isLoading: isLoadingWorkOrders } = useQuery<WorkOrder[]>({
    queryKey: ['workOrders'], // 使用 'workOrders' 作為 query key
    queryFn: async () => {
      // 呼叫獲取所有工單的 API
      const response = await apiClient.getWorkOrders();
      return response.data;
    },
  });

  // *** 已移除載入 vehicles 的 useQuery ***

  // 輔助函式：直接從 workOrder 物件讀取車輛資訊
  const getVehicleDisplay = (workOrder: WorkOrder) => {
    if (workOrder.vehicle) {
      // 直接使用工單物件中關聯的車輛車牌
      return workOrder.vehicle.plate_no || `ID: ${workOrder.vehicle_id}`;
    }
    return `ID: ${workOrder.vehicle_id}`; // Fallback
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
      case 'billed':
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  // 簡化載入狀態
  const isLoading = isLoadingWorkOrders;

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">工單管理</h1>
        {/* 新增工單按鈕 */}
        <Link
          href="/work-orders/new"
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
                      {/* 直接顯示車牌，並連結到車輛詳情頁 */}
                      <Link href={`/vehicles/${wo.vehicle_id}`} className="text-primary-600 hover:text-primary-900">
                        {getVehicleDisplay(wo)}
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
                      {/* 管理連結 */}
                      <Link
                        href={`/work-orders/${wo.id}/edit`}
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
            {(!workOrders || workOrders.length === 0) && (
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