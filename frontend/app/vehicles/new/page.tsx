// frontend/app/vehicles/new/page.tsx
'use client';

import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api';

// 1. 定義 Zod Schema (再次修改，加入 preprocess)
const vehicleSchema = z.object({
  plate_no: z.string().min(1, '車牌號碼為必填'),

  make: z.string().optional(),
  model: z.string().optional(),

  // --- 修改數字欄位 ---
  year: z.preprocess(
    (val) => (val === "" ? undefined : val), // 如果是空字串，轉為 undefined
    z.coerce.number({invalid_type_error: '年份必須是數字'})
      .int()
      .min(1900, '年份不正確')
      .max(new Date().getFullYear() + 1, '年份不正確')
      .optional()
      .nullable()
  ),
  displacement_cc: z.preprocess(
    (val) => (val === "" ? undefined : val), // 如果是空字串，轉為 undefined
    z.coerce.number({invalid_type_error: '排氣量必須是數字'})
      .int()
      .positive('排氣量必須是正整數')
      .optional()
      .nullable()
  ),
  // --------------------

  // --- 修改枚舉欄位 ---
  vehicle_type: z.preprocess(
      (val) => (val === "" ? undefined : val), // 如果是空字串，轉為 undefined
      z.enum(['car', 'motorcycle', 'van', 'truck', 'ev_scooter', 'other'], {
          errorMap: () => ({ message: '請選擇有效的車輛類型' })
      }).optional().nullable()
  ),
  // --------------------

  vin: z.string().optional(),
  powertrain: z.string().optional(),

  // --- 修改 seats (也是數字) ---
  seats: z.preprocess(
      (val) => (val === "" ? undefined : val), // 如果是空字串，轉為 undefined
      z.coerce.number({invalid_type_error: '座位數必須是數字'})
        .int()
        .optional()
        .nullable()
  ),
  // -------------------------

  acquired_on: z.string().optional().refine(val => !val || !isNaN(Date.parse(val)), {
      message: "取得日期格式不正確 (YYYY-MM-DD)"
  }).nullable(),
});

type VehicleFormData = z.infer<typeof vehicleSchema>;

export default function NewVehiclePage() {
  const router = useRouter();
  const queryClient = useQueryClient();

  // 2. 設定 react-hook-form
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<VehicleFormData>({
    resolver: zodResolver(vehicleSchema), // 使用 Zod 進行驗證
  });

  // 3. 設定 react-query mutation (處理 API 呼叫)
  const mutation = useMutation({
    mutationFn: (data: VehicleFormData) => {
        const payload = {
            ...data,
            acquired_on: data.acquired_on ? data.acquired_on : null,
        };
        return apiClient.createVehicle(payload); // 呼叫 API
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vehicles'] }); // 讓列表快取失效
      router.push('/vehicles'); // 導回列表頁
    },
    onError: (error) => {
      console.error("新增車輛失敗:", error);
      alert(`新增失敗: ${error.message}`);
    },
  });

  // 4. 表單提交處理函式
  const onSubmit = (data: VehicleFormData) => {
    mutation.mutate(data);
  };

  // 車輛類型選項
  const vehicleTypeOptions = [
    { value: 'car', label: '汽車' },
    { value: 'motorcycle', label: '機車' },
    { value: 'van', label: '廂型車' },
    { value: 'truck', label: '卡車' },
    { value: 'ev_scooter', label: '電動機車' },
    { value: 'other', label: '其他' },
  ];

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">新增車輛</h1>
        <Link href="/vehicles" className="text-gray-600 hover:text-gray-900">
          ← 返回列表
        </Link>
      </div>

      {/* 5. 建立表單 */}
      <div className="bg-white rounded-lg shadow p-8">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* 車牌 */}
          <div>
            <label htmlFor="plate_no" className="block text-sm font-medium text-gray-700">
              車牌號碼 <span className="text-red-600">*</span>
            </label>
            <input
              type="text"
              id="plate_no"
              {...register('plate_no')}
              className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${errors.plate_no ? 'border-red-500' : ''}`}
            />
            {errors.plate_no && (
              <p className="mt-1 text-sm text-red-600">{errors.plate_no.message}</p>
            )}
          </div>

          {/* 品牌 & 型號 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
                <label htmlFor="make" className="block text-sm font-medium text-gray-700">
                品牌
                </label>
                <input
                type="text"
                id="make"
                {...register('make')}
                className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${errors.make ? 'border-red-500' : ''}`}
                />
                {errors.make && (
                <p className="mt-1 text-sm text-red-600">{errors.make.message}</p>
                )}
            </div>
            <div>
                <label htmlFor="model" className="block text-sm font-medium text-gray-700">
                型號
                </label>
                <input
                type="text"
                id="model"
                {...register('model')}
                className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${errors.model ? 'border-red-500' : ''}`}
                />
                {errors.model && (
                <p className="mt-1 text-sm text-red-600">{errors.model.message}</p>
                )}
            </div>
          </div>

          {/* 年份 & 排氣量 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
                <label htmlFor="year" className="block text-sm font-medium text-gray-700">
                年份
                </label>
                <input
                type="number"
                id="year"
                {...register('year')}
                className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${errors.year ? 'border-red-500' : ''}`}
                />
                {errors.year && (
                <p className="mt-1 text-sm text-red-600">{errors.year.message}</p>
                )}
            </div>
             <div>
                <label htmlFor="displacement_cc" className="block text-sm font-medium text-gray-700">
                排氣量 (cc)
                </label>
                <input
                type="number"
                id="displacement_cc"
                {...register('displacement_cc')}
                className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${errors.displacement_cc ? 'border-red-500' : ''}`}
                />
                {errors.displacement_cc && (
                <p className="mt-1 text-sm text-red-600">{errors.displacement_cc.message}</p>
                )}
            </div>
          </div>

          {/* 車輛類型 */}
          <div>
            <label htmlFor="vehicle_type" className="block text-sm font-medium text-gray-700">
              車輛類型
            </label>
            <select
              id="vehicle_type"
              {...register('vehicle_type')}
              className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${errors.vehicle_type ? 'border-red-500' : ''}`}
            >
              <option value="">-- 請選擇 --</option>
              {vehicleTypeOptions.map(option => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
            {errors.vehicle_type && (
              <p className="mt-1 text-sm text-red-600">{errors.vehicle_type.message}</p>
            )}
          </div>

          {/* --- 選填欄位 --- */}
          <div>
            <label htmlFor="vin" className="block text-sm font-medium text-gray-700">
              VIN/車身號碼
            </label>
            <input
              type="text"
              id="vin"
              {...register('vin')}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
            />
          </div>
          <div>
            <label htmlFor="acquired_on" className="block text-sm font-medium text-gray-700">
              取得日期
            </label>
            <input
              type="date"
              id="acquired_on"
              {...register('acquired_on')}
              className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${errors.acquired_on ? 'border-red-500' : ''}`}
            />
            {errors.acquired_on && (
                <p className="mt-1 text-sm text-red-600">{errors.acquired_on.message}</p>
            )}
          </div>
          {/* --- 提交按鈕 --- */}
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