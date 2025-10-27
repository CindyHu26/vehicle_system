'use client';

import { useQuery } from '@tanstack/react-query';
import { useParams } from 'next/navigation';
import { apiClient } from '@/lib/api';
import Link from 'next/link';

export default function VehicleDetailPage() {
  const params = useParams();
  const vehicleId = parseInt(params.id as string);

  const { data: vehicle, isLoading } = useQuery({
    queryKey: ['vehicle', vehicleId],
    queryFn: async () => {
      const response = await apiClient.getVehicle(vehicleId);
      return response.data;
    },
  });

  if (isLoading) {
    return <div className="text-center p-8">載入中...</div>;
  }

  if (!vehicle) {
    return <div className="text-center p-8">找不到該車輛</div>;
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">{vehicle.plate_no}</h1>
          <p className="text-gray-600">{vehicle.make} {vehicle.model} ({vehicle.year})</p>
        </div>
        <Link
          href="/vehicles"
          className="text-gray-600 hover:text-gray-900"
        >
          ← 返回列表
        </Link>
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
            <p className="font-medium">{vehicle.vehicle_type}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">狀態</p>
            <p className="font-medium">{vehicle.status}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">排氣量</p>
            <p className="font-medium">{vehicle.displacement_cc} cc</p>
          </div>
        </div>
      </div>

      {/* Insurance */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">保險</h2>
        {vehicle.insurances.length === 0 ? (
          <p className="text-gray-500">尚無保險紀錄</p>
        ) : (
          <div className="space-y-2">
            {vehicle.insurances.map((insurance) => (
              <div key={insurance.id} className="border-b pb-2">
                <p className="font-medium">{insurance.policy_type}</p>
                <p className="text-sm text-gray-600">保單號碼: {insurance.policy_no}</p>
                <p className="text-sm text-gray-600">
                  有效期: {insurance.effective_on} ~ {insurance.expires_on}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Violations */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">違規紀錄</h2>
        {vehicle.violations.length === 0 ? (
          <p className="text-gray-500">尚無違規紀錄</p>
        ) : (
          <div className="space-y-2">
            {vehicle.violations.map((violation) => (
              <div key={violation.id} className="border-b pb-2">
                <p className="font-medium text-red-600">罰款: {violation.amount} 元</p>
                <p className="text-sm text-gray-600">日期: {violation.violation_date}</p>
                <p className="text-sm text-gray-600">積點: {violation.points}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}


