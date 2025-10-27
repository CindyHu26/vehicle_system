// frontend/app/vehicles/[id]/edit/page.tsx
'use client';

import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useRouter, useParams } from 'next/navigation';
import { apiClient, Vehicle } from '@/lib/api'; // 從 api.ts 匯入 Vehicle 型別
import { useEffect } from 'react';

// Zod Schema (與新增頁面幾乎相同，但欄位皆為 Optional 或 nullable)
const vehicleSchema = z.object({
  plate_no: z.string().min(1, '車牌號碼為必填'), // 車牌通常不允許編輯
  make: z.string().optional().nullable(), // 改為 nullable
  model: z.string().optional().nullable(),
  year: z.preprocess(
    (val) => (val === "" || val === null ? null : val), // 空字串轉 null
    z.coerce.number({invalid_type_error: '年份必須是數字'})
      .int()
      .min(1900, '年份不正確')
      .max(new Date().getFullYear() + 1, '年份不正確')
      .optional()
      .nullable()
  ),
  displacement_cc: z.preprocess(
    (val) => (val === "" || val === null ? null : val),
    z.coerce.number({invalid_type_error: '排氣量必須是數字'})
      .int()
      .positive('排氣量必須是正整數')
      .optional()
      .nullable()
  ),
  vehicle_type: z.preprocess(
      (val) => (val === "" || val === null ? null : val),
      z.enum(['car', 'motorcycle', 'van', 'truck', 'ev_scooter', 'other'], {
          errorMap: () => ({ message: '請選擇有效的車輛類型' })
      }).optional().nullable()
  ),
  vin: z.string().optional().nullable(),
  powertrain: z.string().optional().nullable(),
  seats: z.preprocess(
      (val) => (val === "" || val === null ? null : val),
      z.coerce.number({invalid_type_error: '座位數必須是數字'})
        .int()
        .optional()
        .nullable()
  ),
  acquired_on: z.string().optional().refine(val => !val || !isNaN(Date.parse(val)), {
      message: "取得日期格式不正確 (YYYY-MM-DD)"
  }).nullable(),
  status: z.enum(['active', 'maintenance', 'idle', 'retired'], {
    errorMap: () => ({ message: '請選擇有效的狀態' })
  }).optional(),
});

type VehicleFormData = z.infer<typeof vehicleSchema>;

export default function EditVehiclePage() {
  const router = useRouter();
  const params = useParams();
  const vehicleId = parseInt(params.id as string);
  const queryClient = useQueryClient();

  // 載入現有車輛資料
  const { data: vehicle, isLoading: isLoadingVehicle, isError } = useQuery({
    queryKey: ['vehicle', vehicleId],
    queryFn: () => apiClient.getVehicle(vehicleId).then(res => res.data),
    enabled: !!vehicleId,
  });

  // 設定 react-hook-form
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<VehicleFormData>({
    resolver: zodResolver(vehicleSchema),
    defaultValues: {}, // 初始為空，稍後用 useEffect 填入
  });

  // 當資料載入後，設定表單預設值
  useEffect(() => {
    if (vehicle) {
      reset({
        ...vehicle,
        // 格式化日期並處理 null/undefined
        acquired_on: vehicle.acquired_on ? vehicle.acquired_on.split('T')[0] : '',
        year: vehicle.year ?? undefined,
        displacement_cc: vehicle.displacement_cc ?? undefined,
        vehicle_type: vehicle.vehicle_type ?? undefined,
        vin: vehicle.vin ?? '',
        powertrain: vehicle.powertrain ?? '',
        seats: vehicle.seats ?? undefined,
        status: vehicle.status ?? undefined,
      });
    }
  }, [vehicle, reset]);

  // 設定 react-query mutation (更新 API)
  const updateMutation = useMutation({
    mutationFn: (data: VehicleFormData) => {
        const { plate_no, ...updateData } = data; // 排除車牌
        const payload = {
            ...updateData,
            acquired_on: updateData.acquired_on || null, // 空字串轉 null
            // 將可能是 undefined 的數值轉為 null
            year: updateData.year ?? null,
            displacement_cc: updateData.displacement_cc ?? null,
            seats: updateData.seats ?? null,
            vehicle_type: updateData.vehicle_type ?? null,
        };
      return apiClient.updateVehicle(vehicleId, payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vehicles'] });
      queryClient.invalidateQueries({ queryKey: ['vehicle', vehicleId] });
      router.push(`/vehicles/${vehicleId}`); // 導回詳情頁
    },
    onError: (error) => {
      console.error("更新車輛失敗:", error);
      alert(`更新失敗: ${error.message}`);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => apiClient.deleteVehicle(vehicleId), // 呼叫刪除 API
    onSuccess: () => {
      // 成功刪除後...
      queryClient.invalidateQueries({ queryKey: ['vehicles'] }); // 讓列表快取失效
      router.push('/vehicles'); // 導回列表頁
    },
    onError: (error: any) => {
      console.error("刪除車輛失敗:", error);
      // 後端返回的 400 錯誤會包含 detail 訊息
      const errorMsg = error.response?.data?.detail || error.message;
      alert(`刪除失敗: ${errorMsg}`);
    },
  });

  const onSubmit = (data: VehicleFormData) => {
    updateMutation.mutate(data);
  };
  const handleDelete = () => {
    // 確保 vehicle 物件存在後才繼續
    if (!vehicle) {
      return; 
    }
    if (window.confirm(`您確定要永久刪除車輛 ${vehicle.plate_no} 嗎？\n此操作無法復原。`)) {
      deleteMutation.mutate();
    }
  };

  const vehicleTypeOptions = [
    { value: 'car', label: '汽車' },
    { value: 'motorcycle', label: '機車' },
    { value: 'van', label: '廂型車' },
    { value: 'truck', label: '卡車' },
    { value: 'ev_scooter', label: '電動機車' },
    { value: 'other', label: '其他' },
  ];
  const vehicleStatusOptions = [ // 狀態選項
    { value: 'active', label: '啟用中' },
    { value: 'maintenance', label: '維護中' },
    { value: 'idle', label: '閒置' },
    { value: 'retired', label: '已報廢' },
  ];


  if (isLoadingVehicle) return <div className="text-center p-8">載入車輛資料中...</div>;
  if (isError || !vehicle) return <div className="text-center p-8 text-red-600">載入車輛資料失敗</div>;

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">編輯車輛 - {vehicle.plate_no}</h1>
        <Link href={`/vehicles/${vehicleId}`} className="text-gray-600 hover:text-gray-900">
          ← 返回詳情
        </Link>
      </div>

      <div className="bg-white rounded-lg shadow p-8">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* 車牌 (唯讀) */}
          <div>
            <label htmlFor="plate_no" className="block text-sm font-medium text-gray-700">車牌號碼 <span className="text-red-600">*</span></label>
            <input type="text" id="plate_no" {...register('plate_no')} readOnly className="mt-1 block w-full rounded-md border-gray-300 shadow-sm bg-gray-100 sm:text-sm"/>
          </div>

          {/* 品牌 & 型號 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
             <div>
                <label htmlFor="make" className="block text-sm font-medium text-gray-700">品牌</label>
                <input type="text" id="make" {...register('make')} className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${errors.make ? 'border-red-500' : ''}`} />
                {errors.make && <p className="mt-1 text-sm text-red-600">{errors.make.message}</p>}
             </div>
             <div>
                <label htmlFor="model" className="block text-sm font-medium text-gray-700">型號</label>
                <input type="text" id="model" {...register('model')} className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${errors.model ? 'border-red-500' : ''}`} />
                {errors.model && <p className="mt-1 text-sm text-red-600">{errors.model.message}</p>}
             </div>
          </div>

          {/* 年份 & 排氣量 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
             <div>
                <label htmlFor="year" className="block text-sm font-medium text-gray-700">年份</label>
                <input type="number" id="year" {...register('year')} className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${errors.year ? 'border-red-500' : ''}`} />
                {errors.year && <p className="mt-1 text-sm text-red-600">{errors.year.message}</p>}
             </div>
             <div>
                <label htmlFor="displacement_cc" className="block text-sm font-medium text-gray-700">排氣量 (cc)</label>
                <input type="number" id="displacement_cc" {...register('displacement_cc')} className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${errors.displacement_cc ? 'border-red-500' : ''}`} />
                {errors.displacement_cc && <p className="mt-1 text-sm text-red-600">{errors.displacement_cc.message}</p>}
             </div>
          </div>

          {/* 車輛類型 */}
          <div>
            <label htmlFor="vehicle_type" className="block text-sm font-medium text-gray-700">車輛類型</label>
            <select id="vehicle_type" {...register('vehicle_type')} className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${errors.vehicle_type ? 'border-red-500' : ''}`}>
              <option value="">-- 請選擇 --</option>
              {vehicleTypeOptions.map(option => ( <option key={option.value} value={option.value}>{option.label}</option> ))}
            </select>
            {errors.vehicle_type && <p className="mt-1 text-sm text-red-600">{errors.vehicle_type.message}</p>}
          </div>

          {/* 狀態 */}
          <div>
            <label htmlFor="status" className="block text-sm font-medium text-gray-700">狀態</label>
            <select id="status" {...register('status')} className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${errors.status ? 'border-red-500' : ''}`}>
              {/* <option value="">-- 請選擇 --</option> */} {/* 狀態通常必選，不給空選項 */}
              {vehicleStatusOptions.map(option => ( <option key={option.value} value={option.value}>{option.label}</option> ))}
            </select>
            {errors.status && <p className="mt-1 text-sm text-red-600">{errors.status.message}</p>}
          </div>

          {/* VIN */}
          <div>
            <label htmlFor="vin" className="block text-sm font-medium text-gray-700">VIN/車身號碼</label>
            <input type="text" id="vin" {...register('vin')} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm" />
          </div>

          {/* 取得日期 */}
          <div>
            <label htmlFor="acquired_on" className="block text-sm font-medium text-gray-700">取得日期</label>
            <input type="date" id="acquired_on" {...register('acquired_on')} className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${errors.acquired_on ? 'border-red-500' : ''}`} />
            {errors.acquired_on && <p className="mt-1 text-sm text-red-600">{errors.acquired_on.message}</p>}
          </div>

          <div className="flex justify-between items-center">
            {/* 刪除按鈕 (靠左) */}
            <button
              type="button" // 必須是 type="button" 才不會觸發 form submit
              onClick={handleDelete}
              disabled={deleteMutation.isPending}
              className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50"
            >
              {deleteMutation.isPending ? '刪除中...' : '刪除此車輛'}
            </button>
            
            {/* 更新按鈕 (靠右) */}
            <button
              type="submit"
              disabled={updateMutation.isPending}
              className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
            >
              {updateMutation.isPending ? '更新中...' : '更新'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}