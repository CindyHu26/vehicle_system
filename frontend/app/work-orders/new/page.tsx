// frontend/app/work-orders/new/page.tsx
'use client';

import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { apiClient, Vehicle, Vendor } from '@/lib/api'; // 引入 Vehicle 和 Vendor 型別

// 1. 定義 Zod Schema (對應後端的 WorkOrderCreate)
const workOrderSchema = z.object({
  vehicle_id: z.coerce.number().int().positive("必須選擇車輛"),
  type: z.enum([ // 對應 models.py 的 WorkOrderTypeEnum
    'maintenance', 'repair', 'recall', 'cleaning',
    'emission_check', 'inspection', 'purification', 'other'
  ], {
    errorMap: () => ({ message: '必須選擇工單類型' })
  }),
  status: z.enum([ // 對應 models.py 的 WorkOrderStatusEnum
    'draft', 'pending_approval', 'in_progress', 'completed', 'billed', 'closed'
  ]).optional(), // 狀態在建立時通常是可選的，後端可能有預設值
  vendor_id: z.preprocess(
    (val) => (val === "" ? undefined : val),
    z.coerce.number().int().optional().nullable()
  ),
  scheduled_on: z.string().optional().refine(val => !val || !isNaN(Date.parse(val)), {
      message: "預計日期格式不正確 (YYYY-MM-DD)"
  }).nullable(),
  notes: z.string().optional(),
  odometer_at_service: z.preprocess(
    (val) => (val === "" ? undefined : val),
    z.coerce.number({invalid_type_error: '里程必須是數字'})
      .int()
      .nonnegative('里程必須大於或等於 0')
      .optional()
      .nullable()
  ),
  cost_amount: z.preprocess(
      (val) => (val === "" ? undefined : val),
      z.coerce.number({invalid_type_error: '費用必須是數字'})
        .positive('費用必須大於 0')
        .optional()
        .nullable()
  ),
});

type WorkOrderFormData = z.infer<typeof workOrderSchema>;

export default function NewWorkOrderPage() {
  const router = useRouter();
  const queryClient = useQueryClient();

  // 2. 載入下拉選單資料
  const { data: vehicles, isLoading: isLoadingVehicles } = useQuery<Vehicle[]>({
    queryKey: ['vehicles'], // Reuse existing query if possible
    queryFn: () => apiClient.getVehicles().then(res => res.data),
    // 只選擇 active 的車輛來建立工單可能是合理的
    // select: (data) => data.filter(v => v.status === 'active'),
  });

  const { data: vendors, isLoading: isLoadingVendors } = useQuery<Vendor[]>({
    queryKey: ['vendors'],
    queryFn: () => apiClient.getVendors().then(res => res.data), // 假設 apiClient 有 getVendors 方法
  });

  // 3. 設定 react-hook-form
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<WorkOrderFormData>({
    resolver: zodResolver(workOrderSchema),
    defaultValues: {
        status: 'pending_approval', // 預設狀態
    }
  });

  // 4. 設定 mutation (呼叫 API)
  const mutation = useMutation({
    mutationFn: (data: WorkOrderFormData) => {
        const payload = {
            ...data,
            // 確保 optional 數字欄位送出 null 而不是 undefined
            vendor_id: data.vendor_id ?? null,
            scheduled_on: data.scheduled_on || null,
            odometer_at_service: data.odometer_at_service ?? null,
            cost_amount: data.cost_amount ? String(data.cost_amount) : null, // 金額轉字串給後端
            status: data.status || 'draft', // 如果沒選，預設 draft
        };
        return apiClient.createWorkOrder(payload); // 呼叫 API
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workOrders'] }); // 讓工單列表快取失效
      router.push('/work-orders'); // 導回列表頁
    },
    onError: (error: any) => {
      console.error("新增工單失敗:", error);
      const errorMsg = error.response?.data?.detail || error.message;
      alert(`新增工單失敗: ${errorMsg}`);
    },
  });

  // 5. 表單提交
  const onSubmit = (data: WorkOrderFormData) => {
    mutation.mutate(data);
  };

  // 6. 下拉選單選項
  const workOrderTypeOptions = [
    { value: 'maintenance', label: '定期保養' },
    { value: 'repair', label: '故障維修' },
    { value: 'recall', label: '召回' },
    { value: 'cleaning', label: '清潔' },
    { value: 'emission_check', label: '排氣定檢 (機車)' },
    { value: 'inspection', label: '定期檢驗 (四輪)' },
    { value: 'purification', label: '淨車' },
    { value: 'other', label: '其他' },
  ];

  const workOrderStatusOptions = [
    { value: 'draft', label: '草稿' },
    { value: 'pending_approval', label: '待核准' },
    { value: 'in_progress', label: '進行中' },
    { value: 'completed', label: '完成' },
    { value: 'billed', label: '待對帳' },
    { value: 'closed', label: '結案' },
  ];

  const isLoading = isLoadingVehicles || isLoadingVendors;

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">新增工單</h1>
        <Link href="/work-orders" className="text-gray-600 hover:text-gray-900">
          ← 返回列表
        </Link>
      </div>

      <div className="bg-white rounded-lg shadow p-8">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">

          {/* 車輛 (必填) */}
          <div>
            <label htmlFor="vehicle_id" className="block text-sm font-medium text-gray-700">
              車輛 <span className="text-red-600">*</span>
            </label>
            <select
              id="vehicle_id"
              {...register('vehicle_id')}
              disabled={isLoadingVehicles}
              className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${errors.vehicle_id ? 'border-red-500' : ''}`}
            >
              <option value="">-- 請選擇車輛 --</option>
              {vehicles?.map(v => (
                <option key={v.id} value={v.id}>{v.plate_no} ({v.make} {v.model})</option>
              ))}
            </select>
            {errors.vehicle_id && (
              <p className="mt-1 text-sm text-red-600">{errors.vehicle_id.message}</p>
            )}
          </div>

          {/* 工單類型 (必填) */}
          <div>
            <label htmlFor="type" className="block text-sm font-medium text-gray-700">
              工單類型 <span className="text-red-600">*</span>
            </label>
            <select
              id="type"
              {...register('type')}
              className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${errors.type ? 'border-red-500' : ''}`}
            >
              <option value="">-- 請選擇類型 --</option>
              {workOrderTypeOptions.map(option => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
            {errors.type && (
              <p className="mt-1 text-sm text-red-600">{errors.type.message}</p>
            )}
          </div>

          {/* 狀態 (選填，有預設值) */}
          <div>
            <label htmlFor="status" className="block text-sm font-medium text-gray-700">
              狀態
            </label>
            <select
              id="status"
              {...register('status')}
              className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${errors.status ? 'border-red-500' : ''}`}
            >
              {workOrderStatusOptions.map(option => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
            {errors.status && (
              <p className="mt-1 text-sm text-red-600">{errors.status.message}</p>
            )}
          </div>

          {/* 供應商 (選填) */}
          <div>
            <label htmlFor="vendor_id" className="block text-sm font-medium text-gray-700">
              供應商 (選填)
            </label>
            <select
              id="vendor_id"
              {...register('vendor_id')}
              disabled={isLoadingVendors}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
            >
              <option value="">-- 請選擇供應商 --</option>
              {vendors?.map(v => (
                <option key={v.id} value={v.id}>{v.name} ({v.category})</option>
              ))}
            </select>
            {errors.vendor_id && (
              <p className="mt-1 text-sm text-red-600">{errors.vendor_id.message}</p>
            )}
          </div>

          {/* 預計日期 (選填) */}
          <div>
            <label htmlFor="scheduled_on" className="block text-sm font-medium text-gray-700">
              預計日期 (選填)
            </label>
            <input
              type="date"
              id="scheduled_on"
              {...register('scheduled_on')}
              className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${errors.scheduled_on ? 'border-red-500' : ''}`}
            />
             {errors.scheduled_on && (
              <p className="mt-1 text-sm text-red-600">{errors.scheduled_on.message}</p>
            )}
          </div>

           {/* 服務時里程 (選填) */}
           <div>
            <label htmlFor="odometer_at_service" className="block text-sm font-medium text-gray-700">
              服務時里程 (選填)
            </label>
            <input
              type="number"
              id="odometer_at_service"
              {...register('odometer_at_service')}
              className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${errors.odometer_at_service ? 'border-red-500' : ''}`}
            />
             {errors.odometer_at_service && (
              <p className="mt-1 text-sm text-red-600">{errors.odometer_at_service.message}</p>
            )}
          </div>

          {/* 費用 (選填) */}
          <div>
            <label htmlFor="cost_amount" className="block text-sm font-medium text-gray-700">
              費用 (選填)
            </label>
            <input
              type="number"
              step="0.01"
              id="cost_amount"
              {...register('cost_amount')}
              className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${errors.cost_amount ? 'border-red-500' : ''}`}
            />
            {errors.cost_amount && (
              <p className="mt-1 text-sm text-red-600">{errors.cost_amount.message}</p>
            )}
          </div>

          {/* 備註 (選填) */}
          <div>
            <label htmlFor="notes" className="block text-sm font-medium text-gray-700">
              備註 (選填)
            </label>
            <textarea
              id="notes"
              {...register('notes')}
              rows={4}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
            />
          </div>

          {/* 提交按鈕 */}
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={mutation.isPending || isLoading}
              className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
            >
              {mutation.isPending ? '建立中...' : '建立工單'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}