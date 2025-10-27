'use client';

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import Link from 'next/link';

export default function VehiclesPage() {
  const { data: vehicles, isLoading } = useQuery({
    queryKey: ['vehicles'],
    queryFn: async () => {
      const response = await apiClient.getVehicles();
      return response.data;
    },
  });

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">車輛管理</h1>
        <Link
          href="/vehicles/new"
          className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700"
        >
          新增車輛
        </Link>
      </div>

      {isLoading ? (
        <div className="text-center p-8">載入中...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {vehicles?.map((vehicle) => (
            <div key={vehicle.id} className="bg-white rounded-lg shadow p-6">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-xl font-semibold">{vehicle.plate_no}</h3>
                  <p className="text-gray-600">{vehicle.make} {vehicle.model}</p>
                </div>
                <span
                  className={`px-2 py-1 text-xs font-semibold rounded-full ${
                    vehicle.status === 'active'
                      ? 'bg-green-100 text-green-800'
                      : vehicle.status === 'maintenance'
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {vehicle.status}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
                <div>
                  <p className="text-gray-500">車型</p>
                  <p className="font-medium">{vehicle.vehicle_type}</p>
                </div>
                <div>
                  <p className="text-gray-500">年份</p>
                  <p className="font-medium">{vehicle.year}</p>
                </div>
              </div>
              <div className="flex space-x-2">
                <Link
                  href={`/vehicles/${vehicle.id}`}
                  className="flex-1 bg-primary-600 text-white px-4 py-2 rounded-lg text-center hover:bg-primary-700"
                >
                  查看詳情
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}


