'use client';

import Link from 'next/link';

export default function NewVehiclePage() {
  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">新增車輛</h1>
        <Link
          href="/vehicles"
          className="text-gray-600 hover:text-gray-900"
        >
          ← 返回列表
        </Link>
      </div>
      <div className="bg-white rounded-lg shadow p-8 text-center">
        <p className="text-gray-600">新增車輛功能開發中...</p>
      </div>
    </div>
  );
}


