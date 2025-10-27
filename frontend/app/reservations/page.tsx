// frontend/app/reservations/page.tsx
'use client';

import { useQuery } from '@tanstack/react-query';
import { apiClient, Employee, Reservation } from '@/lib/api'; // (!!!) 匯入 Employee 和 Reservation 型別
import { format } from 'date-fns';
import Link from 'next/link'; // (!!!) 確保匯入 Link

export default function ReservationsPage() {
  // 1. 載入預約列表
  const { data: reservations, isLoading: isLoadingReservations } = useQuery<Reservation[]>({
    queryKey: ['reservations'],
    queryFn: async () => {
      const response = await apiClient.getReservations();
      return response.data;
    },
  });

  // 2. (!!! 新增) 載入員工列表，用於顯示姓名
  const { data: employees, isLoading: isLoadingEmployees } = useQuery<Employee[]>({
    queryKey: ['employees'],
    queryFn: async () => {
      const response = await apiClient.getEmployees();
      return response.data;
    },
  });

  // 輔助函式：根據 ID 查找員工姓名
  const getEmployeeName = (id: number) => {
    if (!employees) return `ID: ${id}`;
    const employee = employees.find(e => e.id === id);
    return employee ? employee.name : `ID: ${id}`;
  };

  // 輔助函式：狀態徽章顏色
  const statusBadgeColor = (status: string) => {
    switch (status) {
      case 'approved':
        return 'bg-green-100 text-green-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'completed':
        return 'bg-blue-100 text-blue-800';
      case 'rejected':
      case 'cancelled':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const isLoading = isLoadingReservations || isLoadingEmployees;

  if (isLoading) {
    return <div className="text-center p-8">載入中...</div>;
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">借車申請</h1>
        {/* (!!! 新增申請按鈕 !!!) */}
        <Link
          href="/reservations/new"
          className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700"
        >
          新增申請
        </Link>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  申請人 {/* (!!!) 文字更新 */}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  用途
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  開始時間
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  結束時間
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  狀態
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  操作 {/* (!!! 新增欄位 !!!) */}
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {reservations?.map((reservation) => (
                <tr key={reservation.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    {reservation.id}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {/* (!!!) 改為顯示姓名 */}
                    {getEmployeeName(reservation.requester_id)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {reservation.purpose}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {format(new Date(reservation.start_ts), 'yyyy-MM-dd HH:mm')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {format(new Date(reservation.end_ts), 'yyyy-MM-dd HH:mm')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`px-2 py-1 text-xs font-semibold rounded-full ${statusBadgeColor(reservation.status)}`}
                    >
                      {reservation.status}
                    </span>
                  </td>
                  {/* (!!! 新增 <td> !!!) */}
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <Link
                      href={`/reservations/${reservation.id}/edit`}
                      className="text-primary-600 hover:text-primary-900"
                    >
                      管理
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}