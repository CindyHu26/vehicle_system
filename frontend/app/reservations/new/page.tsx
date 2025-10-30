// frontend/app/reservations/new/page.tsx
'use client';

import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { apiClient, Employee, Vehicle } from '@/lib/api'; // 引入 Employee 和 Vehicle

// 1. 修改 Zod Schema
const reservationSchema = z.object({
  requester_id: z.coerce.number().int().positive("必須選擇駕駛"),
  
  // *** 這是關鍵修改：vehicle_id 改為必填 ***
  vehicle_id: z.coerce.number().int().positive("必須選擇車輛"),
  // *** (移除了 Zod 裡的 z.preprocess, optional, nullable) ***

  purpose: z.enum(['business', 'commute', 'errand', 'other'], {
    errorMap: () => ({ message: '必須選擇用途' })
  }),
  destination: z.string().optional(),
  start_ts: z.string().min(1, "必須填寫開始時間"),
  end_ts: z.string().min(1, "必須填寫結束時間"),
})
.refine(data => {
    try {
        return new Date(data.end_ts) > new Date(data.start_ts);
    } catch {
        return false;
    }
}, {
  message: "結束時間必須晚於開始時間",
  path: ["end_ts"],
});

type ReservationFormData = z.infer<typeof reservationSchema>;

export default function NewReservationPage() {
  const router = useRouter();
  const queryClient = useQueryClient();

  // --- 載入下拉選單所需的資料 ---
  const { data: employees, isLoading: isLoadingEmployees } = useQuery<Employee[]>({
    queryKey: ['employees'],
    queryFn: () => apiClient.getEmployees().then(res => res.data),
  });

  const { data: vehicles, isLoading: isLoadingVehicles } = useQuery<Vehicle[]>({
    queryKey: ['vehicles'], // 這裡使用 vehicles (完整) 還是 vehiclesBasic (輕量)
    queryFn: () => apiClient.getVehicles().then(res => res.data), // 暫時先用 getVehicles
    // (篩選出 'active' 的車輛)
    select: (data) => data.filter(v => v.status === 'active'),
  });
  // -----------------------------

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ReservationFormData>({
    resolver: zodResolver(reservationSchema),
  });

  const mutation = useMutation({
    mutationFn: (data: ReservationFormData) => {
        const payload = {
            ...data,
            start_ts: new Date(data.start_ts).toISOString(),
            end_ts: new Date(data.end_ts).toISOString(),
            // *** vehicle_id 現在是必填的 number ***
            vehicle_id: Number(data.vehicle_id), 
        };
        // 後端 create_reservation 收到 vehicle_id 後，會自動將 status 設為 'approved'
        return apiClient.createReservation(payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reservations'] });
      router.push('/reservations');
    },
    onError: (error: any) => {
      console.error("建立派車單失敗:", error);
      const errorMsg = error.response?.data?.detail || error.message;
      alert(`建立派車單失敗: ${errorMsg}`); // 修改提示文字
    },
  });

  const onSubmit = (data: ReservationFormData) => {
    mutation.mutate(data);
  };

  const purposeOptions = [
    { value: 'business', label: '公務 (廠服/會議)' },
    { value: 'commute', label: '通勤 (上下班)' },
    { value: 'errand', label: '跑腿/臨時' },
    { value: 'other', label: '其他' },
  ];

  const isLoading = isLoadingEmployees || isLoadingVehicles;

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        {/* 修改標題 */}
        <h1 className="text-3xl font-bold">新增派車單 (排程)</h1>
        <Link href="/reservations" className="text-gray-600 hover:text-gray-900">
          ← 返回列表
        </Link>
      </div>

      <div className="bg-white rounded-lg shadow p-8">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          
          {/* 駕駛/使用人 (必填) */}
          <div>
            {/* 修改標籤 */}
            <label htmlFor="requester_id" className="block text-sm font-medium text-gray-700">
              駕駛/使用人 <span className="text-red-600">*</span>
            </label>
            <select
              id="requester_id"
              {...register('requester_id')}
              disabled={isLoadingEmployees}
              className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${errors.requester_id ? 'border-red-500' : ''}`}
            >
              <option value="">-- 請選擇員工 --</option>
              {employees?.map(emp => (
                <option key={emp.id} value={emp.id}>{emp.name} ({emp.emp_no})</option>
              ))}
            </select>
            {errors.requester_id && (
              <p className="mt-1 text-sm text-red-600">{errors.requester_id.message}</p>
            )}
          </div>

          {/* 指派車輛 (必填) */}
          <div>
            {/* 修改標籤並設為必填 */}
            <label htmlFor="vehicle_id" className="block text-sm font-medium text-gray-700">
              指派車輛 <span className="text-red-600">*</span>
            </label>
            <select
              id="vehicle_id"
              {...register('vehicle_id')}
              disabled={isLoadingVehicles}
              // 加入錯誤樣式
              className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${errors.vehicle_id ? 'border-red-500' : ''}`}
            >
              {/* 修改預設選項 */}
              <option value="">-- 請選擇車輛 --</option>
              {vehicles?.map(v => (
                <option key={v.id} value={v.id}>{v.plate_no} ({v.make} {v.model})</option>
              ))}
            </select>
            {/* 加入錯誤訊息顯示 */}
            {errors.vehicle_id && (
              <p className="mt-1 text-sm text-red-600">{errors.vehicle_id.message}</p>
            )}
          </div>

          {/* 用途 (必填) */}
          <div>
            <label htmlFor="purpose" className="block text-sm font-medium text-gray-700">
              用途 <span className="text-red-600">*</span>
            </label>
            <select
              id="purpose"
              {...register('purpose')}
              className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${errors.purpose ? 'border-red-500' : ''}`}
            >
              <option value="">-- 請選擇用途 --</option>
              {purposeOptions.map(option => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
            {errors.purpose && (
              <p className="mt-1 text-sm text-red-600">{errors.purpose.message}</p>
            )}
          </div>

          {/* 開始 & 結束時間 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label htmlFor="start_ts" className="block text-sm font-medium text-gray-700">
                開始時間 <span className="text-red-600">*</span>
              </label>
              <input
                type="datetime-local"
                id="start_ts"
                {...register('start_ts')}
                className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${errors.start_ts ? 'border-red-500' : ''}`}
              />
              {errors.start_ts && (
                <p className="mt-1 text-sm text-red-600">{errors.start_ts.message}</p>
              )}
            </div>
            <div>
              <label htmlFor="end_ts" className="block text-sm font-medium text-gray-700">
                結束時間 <span className="text-red-600">*</span>
              </label>
              <input
                type="datetime-local"
                id="end_ts"
                {...register('end_ts')}
                className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${errors.end_ts ? 'border-red-500' : ''}`}
              />
              {errors.end_ts && (
                <p className="mt-1 text-sm text-red-600">{errors.end_ts.message}</p>
              )}
            </div>
          </div>
          
          {/* 目的地 (選填) */}
          <div>
            <label htmlFor="destination" className="block text-sm font-medium text-gray-700">
              目的地 (選填)
            </label>
            <input
              type="text"
              id="destination"
              {...register('destination')}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
            />
          </div>

          {/* 提交按鈕 */}
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={mutation.isPending || isLoading} // 統一使用 isLoading
              className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
            >
              {/* 修改按鈕文字 */}
              {mutation.isPending ? '建立中...' : '建立派車單'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}