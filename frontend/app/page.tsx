// frontend/app/page.tsx
'use client';

import { useQuery } from '@tanstack/react-query';
// *** 修改這裡：引入 VehicleBasic 和 ComplianceReportResponse ***
import { apiClient, VehicleBasic, ComplianceReportResponse } from '@/lib/api';
import Link from 'next/link';

export default function Home() {
  // *** 修改這裡：使用 getVehiclesBasic 和 VehicleBasic[] ***
  const { data: vehicles, isLoading: isLoadingVehicles } = useQuery<VehicleBasic[]>({
    queryKey: ['vehiclesBasic'], // <-- 使用不同的 query key
    queryFn: async () => {
      const response = await apiClient.getVehiclesBasic(); // <-- 呼叫新的 API 方法
      return response.data;
    },
  });

  // *** 修改這裡：指定 useQuery 的型別為 ComplianceReportResponse ***
  const { data: complianceReport, isLoading: isLoadingCompliance } = useQuery<ComplianceReportResponse>({
    queryKey: ['compliance-report'],
    queryFn: async () => {
      const response = await apiClient.getComplianceReport(30);
      return response.data; // data 現在會被推斷為 ComplianceReportResponse | undefined
    },
  });

  // 組合 isLoading 狀態
  const isLoading = isLoadingVehicles || isLoadingCompliance;

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">儀表板</h1>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500 mb-2">總車輛數</h3>
          <p className="text-3xl font-bold">
            {isLoadingVehicles ? '...' : vehicles?.length ?? 0}
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500 mb-2">合規率</h3>
          <p className="text-3xl font-bold">
            {isLoadingCompliance ? '...' : (complianceReport?.compliance_rate ?? 0)}%
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500 mb-2">合規車輛</h3>
          <p className="text-3xl font-bold">
            {isLoadingCompliance ? '...' : (
              `${complianceReport?.compliant_vehicles ?? 0} / ${complianceReport?.total_vehicles ?? 0}`
            )}
          </p>
        </div>
      </div>

      {/* Vehicles List */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold">車輛列表</h2>
        </div>
        {isLoadingVehicles ? (
          <div className="p-6 text-center">載入車輛列表中...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    車牌
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    品牌/型號
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    車型
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    狀態
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    操作
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {/* *** 使用 vehicles (型別是 VehicleBasic[]) *** */}
                {vehicles?.map((vehicle) => (
                  <tr key={vehicle.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {vehicle.plate_no}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {vehicle.make || '-'} {vehicle.model || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {vehicle.vehicle_type || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          vehicle.status === 'active'
                            ? 'bg-green-100 text-green-800'
                            : vehicle.status === 'maintenance'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {vehicle.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <Link
                        href={`/vehicles/${vehicle.id}`} // 連結到詳情頁不變
                        className="text-primary-600 hover:text-primary-900"
                      >
                        查看詳情
                      </Link>
                    </td>
                  </tr>
                ))}
                {/* 如果沒有車輛資料 */}
                {(!vehicles || vehicles.length === 0) && (
                    <tr>
                        <td colSpan={5} className="px-6 py-4 text-center text-gray-500">尚無車輛資料</td>
                    </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Compliance Issues */}
      {isLoadingCompliance ? (
        <div className="mt-8 p-6 text-center text-gray-500">載入合規報表中...</div>
      ) : (
        complianceReport && complianceReport.items.some(item => item.issues.length > 0) && (
          <div className="mt-8 bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4 text-yellow-800">⚠️ 合規警告 (30 天內到期)</h2>
            <ul className="space-y-2">
              {complianceReport.items
                .filter(item => item.issues.length > 0)
                .map((item) => ( // TypeScript 現在知道 item 是 ComplianceReportItem 型別
                  <li key={item.vehicle_id} className="text-sm text-yellow-700">
                    <Link href={`/vehicles/${item.vehicle_id}`} className="font-medium text-yellow-800 hover:underline">
                      {item.plate_no}
                    </Link>
                    :{' '}
                    {item.issues.join(', ')}
                  </li>
                ))}
            </ul>
          </div>
        )
      )}
    </div>
  );
}