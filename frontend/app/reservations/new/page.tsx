// frontend/app/reservations/new/page.tsx
'use client';

import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api';

// 1. 定義 Zod Schema (對應後端的 ReservationCreate)
const reservationSchema = z.object({
  requester_id: z.coerce.number().int().positive("必須選擇申請人"),
  vehicle_id: z.preprocess( // 允許空字串轉為 undefined
    (val) => (val === "" ? undefined : val),
    z.coerce.number().int().optional().nullable()
  ),
  purpose: z.enum(['business', 'commute', 'errand', 'other'], {
    errorMap: () => ({ message: '必須選擇用途' })
  }),
  destination: z.string().optional(),
  start_ts: z.string().min(1, "必須填寫開始時間"), // datetime-local input 回傳的是字串
  end_ts: z.string().min(1, "必須填寫結束時間"),
})
.refine(data => { // 驗證：結束時間必須晚於開始時間
    try {
        return new Date(data.end_ts) > new Date(data.start_ts);
    } catch {
        return false;
    }
}, {
  message: "結束時間必須晚於開始時間",
  path: ["end_ts"], // 錯誤訊息顯示在 'end_ts' 欄位
});

type ReservationFormData = z.infer<typeof reservationSchema>;

export default function NewReservationPage() {
  const router = useRouter();
  const queryClient = useQueryClient();

  // --- 載入下拉選單所需的資料 ---
  // 載入員工
  const { data: employees, isLoading: isLoadingEmployees } = useQuery({
    queryKey: ['employees'],
    queryFn: () => apiClient.getEmployees().then(res => res.data),
  });

  // 載入車輛 (只選 'active' 狀態的)
  const { data: vehicles, isLoading: isLoadingVehicles } = useQuery({
    queryKey: ['vehicles'],
    queryFn: () => apiClient.getVehicles().then(res => res.data),
    // (篩選出 'active' 的車輛)
    select: (data) => data.filter(v => v.status === 'active'),
  });
  // -----------------------------

  // 2. 設定 react-hook-form
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ReservationFormData>({
    resolver: zodResolver(reservationSchema),
  });

  // 3. 設定 mutation (呼叫 API)
  const mutation = useMutation({
    mutationFn: (data: ReservationFormData) => {
        // 將時間字串轉為 ISO 8601 (API 需要含時區的格式)
        const payload = {
            ...data,
            start_ts: new Date(data.start_ts).toISOString(),
            end_ts: new Date(data.end_ts).toISOString(),
            // 確保 vehicle_id 是數字或 null
            vehicle_id: data.vehicle_id ? Number(data.vehicle_id) : null,
        };
        return apiClient.createReservation(payload); // 呼叫 API
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reservations'] }); // 讓預約列表快取失效
      router.push('/reservations'); // 導回列表頁
    },
    onError: (error: any) => {
      console.error("新增預約失敗:", error);
      // 顯示後端傳來的錯誤 (例如：衝突、合規失敗)
      const errorMsg = error.response?.data?.detail || error.message;
      alert(`新增預約失敗: ${errorMsg}`);
    },
  });

  // 4. 表單提交
  const onSubmit = (data: ReservationFormData) => {
    mutation.mutate(data);
  };

  // 用途選項
  const purposeOptions = [
    { value: 'business', label: '公務 (廠服/會議)' },
    { value: 'commute', label: '通勤 (上下班)' },
    { value: 'errand', label: '跑腿/臨時' },
    { value: 'other', label: '其他' },
  ];

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">新增借車申請</h1>
        <Link href="/reservations" className="text-gray-600 hover:text-gray-900">
          ← 返回列表
        </Link>
      </div>

      <div className="bg-white rounded-lg shadow p-8">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          
          {/* 申請人 (必填) */}
          <div>
            <label htmlFor="requester_id" className="block text-sm font-medium text-gray-700">
              申請人 <span className="text-red-600">*</span>
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

          {/* 指定車輛 (選填) */}
          <div>
            <label htmlFor="vehicle_id" className="block text-sm font-medium text-gray-700">
              指定車輛 (若不指定，將由調度員指派)
            </label>
            <select
              id="vehicle_id"
              {...register('vehicle_id')}
              disabled={isLoadingVehicles}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
            >
              <option value="">-- 不指定車輛 --</option>
              {vehicles?.map(v => (
                <option key={v.id} value={v.id}>{v.plate_no} ({v.make} {v.model})</option>
              ))}
            </select>
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
                type="datetime-local" // 時間日期選擇器
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
              目的地
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
              disabled={mutation.isPending || isLoadingEmployees || isLoadingVehicles}
              className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
            >
              {mutation.isPending ? '提交中...' : '提交申請'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}