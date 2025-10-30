// frontend/app/employees/[id]/edit/page.tsx
'use client';

import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useRouter, useParams } from 'next/navigation';
import { apiClient, Employee } from '@/lib/api';
import { useEffect } from 'react';

// 定義駕照選項 (與 new/page.tsx 相同)
const licenseOptions = [
  '普通小型車',
  '普通重型機車',
  '大型重型機車',
  '職業小型車',
  '職業大貨車',
  '職業大客車',
];

// 1. Zod Schema
const employeeUpdateSchema = z.object({
  emp_no: z.string(), // 員工編號 (唯讀)
  name: z.string().min(1, '姓名稱為必填'),
  dept_name: z.string().optional().nullable(),
  license_class: z.array(z.string()).optional(), // *** 修改為 array ***
  status: z.enum(['active', 'inactive']),
});

type EmployeeUpdateFormData = z.infer<typeof employeeUpdateSchema>;

export default function EditEmployeePage() {
  const router = useRouter();
  const params = useParams();
  const employeeId = parseInt(params.id as string);
  const queryClient = useQueryClient();

  // 2. 載入現有員工資料
  const { data: employee, isLoading: isLoadingEmployee, isError } = useQuery<Employee>({
    queryKey: ['employee', employeeId],
    queryFn: () => apiClient.getEmployee(employeeId).then(res => res.data),
    enabled: !!employeeId,
  });

  // 3. 設定 react-hook-form
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<EmployeeUpdateFormData>({
    resolver: zodResolver(employeeUpdateSchema),
    defaultValues: {
        license_class: [], // 預設空陣列
    },
  });

  // 4. 當資料載入後，設定表單預設值
  useEffect(() => {
    if (employee) {
      reset({
        emp_no: employee.emp_no,
        name: employee.name,
        dept_name: employee.dept_name ?? '',
        // *** 修改：後端傳來的是陣列或 null ***
        license_class: employee.license_class ?? [],
        status: employee.status,
      });
    }
  }, [employee, reset]);

  // 5. 設定更新 Mutation
  const updateMutation = useMutation({
    mutationFn: (data: EmployeeUpdateFormData) => {
        const { emp_no, ...updateData } = data;
        const payload = {
            ...updateData,
            dept_name: updateData.dept_name || null,
            // *** 修改：傳送陣列或 null ***
            license_class: updateData.license_class && updateData.license_class.length > 0 ? updateData.license_class : null,
        };
        return apiClient.updateEmployee(employeeId, payload); 
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['employees'] });
      queryClient.invalidateQueries({ queryKey: ['employee', employeeId] });
      router.push('/employees');
      alert('員工資料更新成功！');
    },
    onError: (error: any) => {
      console.error("更新員工失敗:", error);
      const errorMsg = error.response?.data?.detail || error.message;
      alert(`更新失敗: ${errorMsg}`);
    },
  });

  // 6. 設定刪除 Mutation
  const deleteMutation = useMutation({
    mutationFn: () => apiClient.deleteEmployee(employeeId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['employees'] });
      router.push('/employees');
      alert('員工已刪除');
    },
    onError: (error: any) => {
      console.error("刪除員工失敗:", error);
      const errorMsg = error.response?.data?.detail || error.message;
      alert(`刪除失敗: ${errorMsg}`);
    },
  });

  const onSubmit = (data: EmployeeUpdateFormData) => {
    updateMutation.mutate(data);
  };

  const handleDelete = () => {
    if (window.confirm(`您確定要刪除員工 ${employee?.name} (編號: ${employee?.emp_no}) 嗎？\n此操作無法復原。`)) {
      deleteMutation.mutate();
    }
  };

  const statusOptions = [
    { value: 'active', label: '在職' },
    { value: 'inactive', label: '離職' },
  ];

  if (isLoadingEmployee) return <div className="text-center p-8">載入員工資料中...</div>;
  if (isError || !employee) return <div className="text-center p-8 text-red-600">載入員工資料失敗</div>;

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">編輯員工 - {employee.name}</h1>
        <Link href="/employees" className="text-gray-600 hover:text-gray-900">
          ← 返回列表
        </Link>
      </div>

      <div className="bg-white rounded-lg shadow p-8">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          
          {/* 員工編號 (唯讀) */}
          <div>
            <label htmlFor="emp_no" className="block text-sm font-medium text-gray-700">
              員工編號 (不可修改)
            </label>
            <input
              type="text"
              id="emp_no"
              {...register('emp_no')}
              readOnly
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm bg-gray-100 sm:text-sm"
            />
          </div>

          {/* 姓名 (必填) */}
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700">
              姓名 <span className="text-red-600">*</span>
            </label>
            <input
              type="text"
              id="name"
              {...register('name')}
              className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${errors.name ? 'border-red-500' : ''}`}
            />
            {errors.name && (
              <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
            )}
          </div>

          {/* 部門 (選填) */}
          <div>
            <label htmlFor="dept_name" className="block text-sm font-medium text-gray-700">
              部門 (選填)
            </label>
            <input
              type="text"
              id="dept_name"
              {...register('dept_name')}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
            />
          </div>

          {/* --- (!!! 修改駕照等級為 Checkbox !!!) --- */}
          <div>
            <label className="block text-sm font-medium text-gray-700">
              駕照等級 (可複選)
            </label>
            <div className="mt-2 grid grid-cols-2 md:grid-cols-3 gap-2">
              {licenseOptions.map((license) => (
                <label key={license} className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    value={license}
                    {...register('license_class')}
                    className="rounded border-gray-300 text-primary-600 shadow-sm focus:ring-primary-500"
                  />
                  <span className="text-sm">{license}</span>
                </label>
              ))}
            </div>
          </div>
          {/* ------------------------------------- */}

          {/* 狀態 (必填) */}
          <div>
            <label htmlFor="status" className="block text-sm font-medium text-gray-700">
              狀態 <span className="text-red-600">*</span>
            </label>
            <select
              id="status"
              {...register('status')}
              className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${errors.status ? 'border-red-500' : ''}`}
            >
              {statusOptions.map(option => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
            {errors.status && (
              <p className="mt-1 text-sm text-red-600">{errors.status.message}</p>
            )}
          </div>

          {/* 操作按鈕 */}
          <div className="flex justify-between items-center pt-4">
             <button
              type="button"
              onClick={handleDelete}
              disabled={deleteMutation.isPending}
              className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50"
            >
              {deleteMutation.isPending ? '刪除中...' : '刪除員工'}
            </button>
             
            <button
              type="submit"
              disabled={updateMutation.isPending}
              className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
            >
              {updateMutation.isPending ? '更新中...' : '更新資料'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}