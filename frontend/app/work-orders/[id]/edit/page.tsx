// frontend/app/work-orders/[id]/edit/page.tsx
'use client';

import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useRouter, useParams } from 'next/navigation';
import { apiClient, WorkOrder, Vehicle, Vendor } from '@/lib/api';
import { useEffect } from 'react';
import { format } from 'date-fns';

// 1. Zod Schema for Update (欄位多為 Optional)
const workOrderUpdateSchema = z.object({
  // vehicle_id 通常不變更，設為唯讀
  type: z.enum([
    'maintenance', 'repair', 'recall', 'cleaning',
    'emission_check', 'inspection', 'purification', 'other'
  ]), // 類型通常也不變更，但這裡保留以供參考
  status: z.enum([
    'draft', 'pending_approval', 'in_progress', 'completed', 'billed', 'closed'
  ], {
     errorMap: () => ({ message: '必須選擇有效的狀態' })
  }), // 狀態是主要可編輯欄位
  vendor_id: z.preprocess(
    (val) => (val === "" ? undefined : val),
    z.coerce.number().int().optional().nullable()
  ),
  scheduled_on: z.string().optional().refine(val => !val || !isNaN(Date.parse(val)), {
      message: "預計日期格式不正確 (YYYY-MM-DD)"
  }).nullable(),
  completed_on: z.string().optional().refine(val => !val || !isNaN(Date.parse(val)), {
      message: "完成日期格式不正確 (YYYY-MM-DD)"
  }).nullable(),
  notes: z.string().optional().nullable(), // 允許 null
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

type WorkOrderUpdateFormData = z.infer<typeof workOrderUpdateSchema>;

export default function EditWorkOrderPage() {
  const router = useRouter();
  const params = useParams();
  const workOrderId = parseInt(params.id as string);
  const queryClient = useQueryClient();

  // 2. 載入工單資料
  const { data: workOrder, isLoading: isLoadingWorkOrder, isError } = useQuery<WorkOrder>({
    queryKey: ['workOrder', workOrderId], // 特定工單的 query key
    queryFn: () => apiClient.getWorkOrder(workOrderId).then(res => res.data), // 假設 apiClient 有 getWorkOrder
    enabled: !!workOrderId, // 只有在 workOrderId 有效時才執行
  });

  // 載入車輛和供應商列表 (與 new page 相同)
   const { data: vehicles, isLoading: isLoadingVehicles } = useQuery<Vehicle[]>({
    queryKey: ['vehicles'],
    queryFn: () => apiClient.getVehicles().then(res => res.data),
  });
  const { data: vendors, isLoading: isLoadingVendors } = useQuery<Vendor[]>({
    queryKey: ['vendors'],
    queryFn: () => apiClient.getVendors().then(res => res.data),
  });

  // 3. 設定 react-hook-form
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<WorkOrderUpdateFormData>({
    resolver: zodResolver(workOrderUpdateSchema),
    defaultValues: {}, // 初始為空，稍後用 useEffect 填入
  });

  // 4. 當資料載入後，設定表單預設值
  useEffect(() => {
    if (workOrder) {
        reset({
        // *** 保持明確賦值 ***
        type: workOrder.type as any, // 假設 type 通常不變
        status: workOrder.status as any,
        vendor_id: workOrder.vendor_id ?? undefined,
        scheduled_on: workOrder.scheduled_on ? format(new Date(workOrder.scheduled_on), 'yyyy-MM-dd') : '',
        completed_on: workOrder.completed_on ? format(new Date(workOrder.completed_on), 'yyyy-MM-dd') : '',
        notes: workOrder.notes ?? '',
        odometer_at_service: workOrder.odometer_at_service ?? undefined,
        cost_amount: workOrder.cost_amount ? Number(workOrder.cost_amount) : undefined,
      });
    }
  }, [workOrder, reset]);

  // 5. 設定更新 Mutation
  const updateMutation = useMutation({
    mutationFn: (data: WorkOrderUpdateFormData) => {
        // *** 修改 Payload 準備 ***
        // 只包含 WorkOrderUpdate schema 中定義的欄位
        const payload: Partial<WorkOrderUpdateFormData> = { // 使用 Partial 確保只包含部分欄位
            status: data.status,
            vendor_id: data.vendor_id ?? null,
            scheduled_on: data.scheduled_on || null,
            completed_on: data.completed_on || null,
            cost_amount: data.cost_amount ?? null, // *** 改為直接傳遞數字或 null ***
            notes: data.notes || null,
            odometer_at_service: data.odometer_at_service ?? null,
            // invoice_doc_id: data.invoice_doc_id ?? null, // 如果未來加入此欄位
        };

        // 過濾掉值為 undefined 的鍵，雖然傳 null 通常也可以
        const filteredPayload = Object.fromEntries(
          Object.entries(payload).filter(([_, v]) => v !== undefined)
        );

        console.log("Sending update payload:", filteredPayload); // Debug: 查看送出的資料

        // *** 確保 apiClient.updateWorkOrder 存在 ***
        return apiClient.updateWorkOrder(workOrderId, filteredPayload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workOrders'] });
      queryClient.invalidateQueries({ queryKey: ['workOrder', workOrderId] });
      router.push('/work-orders');
      alert('工單更新成功！');
    },
    // *** 修改 onError ***
    onError: (error: any) => {
      console.error("更新工單失敗:", error.response?.data || error); // Log a more detailed error
      let errorMsg = "更新失敗，請檢查輸入或稍後再試。"; // Default message
      if (error.response?.data?.detail) {
        // Try to parse FastAPI validation errors (usually in error.response.data.detail)
        try {
          if (Array.isArray(error.response.data.detail)) {
            // Format validation errors nicely
            errorMsg = error.response.data.detail
              .map((err: any) => `${err.loc.slice(1).join('.')} (${err.input}): ${err.msg}`) // Show field name, input value, and message
              .join('\n');
          } else if (typeof error.response.data.detail === 'string') {
            // Handle simple string errors from backend (like ValueError)
            errorMsg = error.response.data.detail;
          } else {
             // Handle cases where detail might be an object but not an array of errors
             errorMsg = JSON.stringify(error.response.data.detail);
          }
        } catch (parseError) {
           console.error("Error parsing error detail:", parseError);
           // Fallback if parsing fails
           errorMsg = error.response?.data?.detail || "發生未知錯誤。";
        }

      } else if (error.message) {
        errorMsg = error.message; // Use generic message if no detail found
      }
      alert(`更新失敗:\n${errorMsg}`); // Display the more detailed error message
    },
  });

  // 6. (可選) 設定刪除 Mutation
  const deleteMutation = useMutation({
    mutationFn: () => {
        // *** 假設 apiClient 有 deleteWorkOrder 方法 ***
        return apiClient.deleteWorkOrder(workOrderId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workOrders'] });
      router.push('/work-orders');
      alert('工單已刪除');
    },
    onError: (error: any) => {
      console.error("刪除工單失敗:", error);
      const errorMsg = error.response?.data?.detail || error.message;
      alert(`刪除失敗: ${errorMsg}`);
    },
  });


  // 7. 表單提交處理
  const onSubmit = (data: WorkOrderUpdateFormData) => {
    updateMutation.mutate(data);
  };

  const handleDelete = () => {
      if (window.confirm(`您確定要刪除工單 #${workOrderId} 嗎？此操作無法復原。`)) {
          deleteMutation.mutate();
      }
  };

  // 選項 (與 new page 相同)
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

  // 輔助函式 (與 list page 相同)
  const getVehiclePlateNo = (vehicleId: number | undefined) => {
    if (!vehicleId || !vehicles) return 'N/A';
    const vehicle = vehicles.find(v => v.id === vehicleId);
    return vehicle ? `${vehicle.plate_no} (${vehicle.make} ${vehicle.model})` : `ID: ${vehicleId}`;
  };

  const isLoading = isLoadingWorkOrder || isLoadingVehicles || isLoadingVendors;

  if (isLoading) return <div className="text-center p-8">載入工單資料中...</div>;
  if (isError || !workOrder) return <div className="text-center p-8 text-red-600">載入工單資料失敗</div>;

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">編輯工單 #{workOrder.id}</h1>
        <Link href="/work-orders" className="text-gray-600 hover:text-gray-900">
          ← 返回列表
        </Link>
      </div>

       {/* 顯示唯讀資訊 */}
       <div className="bg-gray-100 rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4 text-gray-700">基本資訊</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
             <div>
                <p className="text-sm text-gray-500">車輛</p>
                <p className="font-medium">{getVehiclePlateNo(workOrder.vehicle_id)}</p>
            </div>
             <div>
                <p className="text-sm text-gray-500">工單類型</p>
                <p className="font-medium">{workOrder.type}</p>
            </div>
             <div>
                <p className="text-sm text-gray-500">建立時間</p>
                <p className="font-medium">{format(new Date(workOrder.created_at), 'yyyy-MM-dd HH:mm')}</p>
            </div>
        </div>
      </div>

      {/* 編輯表單 */}
      <div className="bg-white rounded-lg shadow p-8">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">

          {/* 狀態 (可編輯) */}
          <div>
            <label htmlFor="status" className="block text-sm font-medium text-gray-700">
              狀態 <span className="text-red-600">*</span>
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

          {/* 供應商 (可編輯) */}
          <div>
            <label htmlFor="vendor_id" className="block text-sm font-medium text-gray-700">
              供應商
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

          {/* 日期 (可編輯) */}
           <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                    <label htmlFor="scheduled_on" className="block text-sm font-medium text-gray-700">
                    預計日期
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
                 <div>
                    <label htmlFor="completed_on" className="block text-sm font-medium text-gray-700">
                    完成日期
                    </label>
                    <input
                    type="date"
                    id="completed_on"
                    {...register('completed_on')}
                    className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${errors.completed_on ? 'border-red-500' : ''}`}
                    />
                    {errors.completed_on && (
                    <p className="mt-1 text-sm text-red-600">{errors.completed_on.message}</p>
                    )}
                </div>
           </div>


          {/* 服務時里程 & 費用 (可編輯) */}
           <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                 <div>
                    <label htmlFor="odometer_at_service" className="block text-sm font-medium text-gray-700">
                    服務時里程
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
                 <div>
                    <label htmlFor="cost_amount" className="block text-sm font-medium text-gray-700">
                    費用
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
           </div>


          {/* 備註 (可編輯) */}
          <div>
            <label htmlFor="notes" className="block text-sm font-medium text-gray-700">
              備註
            </label>
            <textarea
              id="notes"
              {...register('notes')}
              rows={4}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
            />
          </div>

          {/* 操作按鈕 */}
          <div className="flex justify-between items-center pt-4">
             {/* 刪除按鈕 */}
             <button
              type="button"
              onClick={handleDelete}
              disabled={deleteMutation.isPending}
              className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50"
            >
              {deleteMutation.isPending ? '刪除中...' : '刪除工單'}
            </button>
             {/* 更新按鈕 */}
            <button
              type="submit"
              disabled={updateMutation.isPending || isLoading}
              className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
            >
              {updateMutation.isPending ? '更新中...' : '儲存變更'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}