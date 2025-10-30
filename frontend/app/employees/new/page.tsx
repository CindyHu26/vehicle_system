// frontend/app/employees/new/page.tsx
'use client';

import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api';

// 定義駕照選項
const licenseOptions = [
  '普通小型車',
  '普通重型機車',
  '大型重型機車',
  '職業小型車',
  '職業大貨車',
  '職業大客車',
];

// 1. 定義 Zod Schema
const employeeSchema = z.object({
  emp_no: z.string().min(1, '員工編號為必填'),
  name: z.string().min(1, '姓名稱為必填'),
  dept_name: z.string().optional().nullable(),
  // --- (!!! 修改此行 !!!) ---
  license_class: z.array(z.string()).optional(), // 改為 string 陣列
  // --------------------------
  status: z.enum(['active', 'inactive'], {
    errorMap: () => ({ message: '請選擇有效狀態' })
  }),
});

type EmployeeFormData = z.infer<typeof employeeSchema>;

export default function NewEmployeePage() {
  const router = useRouter();
  const queryClient = useQueryClient();

  // 2. 設定 react-hook-form
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<EmployeeFormData>({
    resolver: zodResolver(employeeSchema),
    defaultValues: {
      status: 'active',
      license_class: [], // 預設為空陣列
    },
  });

  // 3. 設定 react-query mutation
  const mutation = useMutation({
    mutationFn: (data: EmployeeFormData) => {
        const payload = {
            ...data,
            dept_name: data.dept_name || null,
            // license_class 現在直接是陣列，後端 JSONB 可以接收
            license_class: data.license_class && data.license_class.length > 0 ? data.license_class : null,
        };
        return apiClient.createEmployee(payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['employees'] });
      router.push('/employees');
    },
    onError: (error: any) => {
      console.error("新增員工失敗:", error);
      const errorMsg = error.response?.data?.detail || error.message;
      alert(`新增失敗: ${errorMsg}`);
    },
  });

  const onSubmit = (data: EmployeeFormData) => {
    mutation.mutate(data);
  };

  const statusOptions = [
    { value: 'active', label: '在職' },
    { value: 'inactive', label: '離職' },
  ];

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">新增員工</h1>
        <Link href="/employees" className="text-gray-600 hover:text-gray-900">
          ← 返回列表
        </Link>
      </div>

      <div className="bg-white rounded-lg shadow p-8">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          
          {/* 員工編號 (必填) */}
          <div>
            <label htmlFor="emp_no" className="block text-sm font-medium text-gray-700">
              員工編號 <span className="text-red-600">*</span>
            </label>
            <input
              type="text"
              id="emp_no"
              {...register('emp_no')}
              className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${errors.emp_no ? 'border-red-500' : ''}`}
            />
            {errors.emp_no && (
              <p className="mt-1 text-sm text-red-600">{errors.emp_no.message}</p>
            )}
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
                    {...register('license_class')} // react-hook-form 會自動處理陣列
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

          {/* 提交按鈕 */}
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={mutation.isPending}
              className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
            >
              {mutation.isPending ? '儲存中...' : '儲存'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}