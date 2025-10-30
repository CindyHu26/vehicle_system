// frontend/app/employees/page.tsx
'use client';

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import Link from 'next/link'; // *** 1. 匯入 Link 元件 ***

export default function EmployeesPage() {
  const { data: employees, isLoading } = useQuery({
    queryKey: ['employees'],
    queryFn: async () => {
      const response = await apiClient.getEmployees();
      return response.data;
    },
  });

  if (isLoading) {
    return <div className="text-center p-8">載入中...</div>;
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">員工管理</h1>
        {/* *** 2. 加入新增員工按鈕 *** */}
        <Link
          href="/employees/new"
          className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700"
        >
          新增員工
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {employees?.map((employee) => (
          <div key={employee.id} className="bg-white rounded-lg shadow p-6 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-xl font-semibold">{employee.name}</h3>
                  <p className="text-gray-600">編號: {employee.emp_no}</p>
                </div>
                <span
                  className={`px-2 py-1 text-xs font-semibold rounded-full ${
                    employee.status === 'active'
                      ? 'bg-green-100 text-green-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {employee.status}
                </span>
              </div>
              <div className="text-sm space-y-2">
                <div>
                  <p className="text-gray-500">部門</p>
                  <p className="font-medium">{employee.dept_name || '-'}</p>
                </div>
                <div>
                  <p className="text-gray-500">駕照等級</p>
                  <p className="font-medium">{employee.license_class || '-'}</p>
                </div>
              </div>
            </div>
            
            {/* *** 3. 加入管理按鈕 *** */}
            <div className="mt-6 text-right">
              <Link
                href={`/employees/${employee.id}/edit`} // 連結到未來的編輯頁面
                className="text-sm font-medium text-primary-600 hover:text-primary-800"
              >
                管理 / 編輯
              </Link>
            </div>

          </div>
        ))}
      </div>
    </div>
  );
}