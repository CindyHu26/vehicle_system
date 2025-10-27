// frontend/app/vehicles/new/page.tsx
'use client';

import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation'; // 從 next/navigation 匯入
import { apiClient } from '@/lib/api';

// 1. 定義 Zod Schema (對應後端的 VehicleCreate)
const vehicleSchema = z.object({
  plate_no: z.string().min(1, '車牌號碼為必填'),
  make: z.string().min(1, '品牌為必填'),
  model: z.string().min(1, '型號為必填'),
  year: z.coerce.number().int().min(1900, '年份不正確').max(new Date().getFullYear() + 1, '年份不正確'), // coerce 將字串轉數字
  displacement_cc: z.coerce.number().int().positive('排氣量必須是正整數'),
  vehicle_type: z.enum(['car', 'motorcycle', 'van', 'truck', 'ev_scooter', 'other'], {
    errorMap: () => ({ message: '請選擇有效的車輛類型' })
  }),
  // 其他選填欄位可以加入 .optional()
  vin: z.string().optional(),
  powertrain: z.string().optional(),
  seats: z.coerce.number().int().optional(),
  acquired_on: z.string().optional().refine(val => !val || !isNaN(Date.parse(val)), { // 檢查是否為有效日期字串
      message: "取得日期格式不正確 (YYYY-MM-DD)"
  }),
});

// 從 Zod Schema 推斷 TypeScript 型別
type VehicleFormData = z.infer<typeof vehicleSchema>;

export default function NewVehiclePage() {
  const router = useRouter();
  const queryClient = useQueryClient(); // 用於快取失效

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
        // 將 acquired_on 轉換為 Date 物件或 null
        const payload = {
            ...data,
            acquired_on: data.acquired_on ? data.acquired_on : null,
        };
        return apiClient.createVehicle(payload);
    },
    onSuccess: () => {
      // 成功後...
      queryClient.invalidateQueries({ queryKey: ['vehicles'] }); // 讓車輛列表快取失效
      router.push('/vehicles'); // 導回列表頁
    },
    onError: (error) => {
      // 顯示錯誤訊息 (簡易版)
      console.error("新增車輛失敗:", error);
      alert(`新增失敗: ${error.message}`);
    },
  });

  // 4. 表單提交處理函式
  const onSubmit = (data: VehicleFormData) => {
    console.log(data); // 可以在開發者工具中看到表單資料
    mutation.mutate(data); // 觸發 mutation (呼叫 API)
  };

  // 車輛類型選項 (來自後端 models.py VehicleTypeEnum)
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
          {/* 表單欄位範例 (車牌) */}
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

          {/* 品牌 & 型號 (放在同一行) */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
                <label htmlFor="make" className="block text-sm font-medium text-gray-700">
                品牌 <span className="text-red-600">*</span>
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
                型號 <span className="text-red-600">*</span>
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
                年份 <span className="text-red-600">*</span>
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
                排氣量 (cc) <span className="text-red-600">*</span>
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
              車輛類型 <span className="text-red-600">*</span>
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
              type="date" // 使用 date input
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
              disabled={mutation.isPending} // 正在提交時禁用按鈕
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