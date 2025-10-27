// frontend/app/reservations/[id]/edit/page.tsx
'use client';

import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useRouter, useParams } from 'next/navigation';
import { apiClient, Reservation, Vehicle, Employee, Trip } from '@/lib/api';
import { useEffect } from 'react';
import { format } from 'date-fns';

// 1. Zod Schema (對應後端的 ReservationUpdate)
const reservationUpdateSchema = z.object({
  status: z.enum(['pending', 'approved', 'rejected', 'in_progress', 'completed', 'cancelled']),
  vehicle_id: z.preprocess(
    (val) => (val === "" || val === null ? null : Number(val) || null), // 確保轉為數字或 null
    z.coerce.number().int().optional().nullable()
  ),
});

type ReservationUpdateFormData = z.infer<typeof reservationUpdateSchema>;

// 2. Zod Schema for Trip Report (對應後端的 TripCreate)
const tripSchema = z.object({
  // 從 reservation 取得，不需要填寫
  // vehicle_id: z.coerce.number().int().positive(),
  // driver_id: z.coerce.number().int().positive(),
  odometer_start: z.coerce.number().int().nonnegative("必須是大於或等於 0 的數字").optional().nullable(), // 改為 nonnegative
  odometer_end: z.coerce.number().int().nonnegative("必須是大於或等於 0 的數字").optional().nullable(),
  fuel_liters: z.preprocess(
    (val) => (val === "" || val === null ? null : val),
    z.coerce.number().positive("必須是大於 0 的數字").optional().nullable()
  ),
  notes: z.string().optional(),
}).refine(data => { // 結束里程必須 >= 開始里程
    // 只有在兩者都有值時才比較
    if (data.odometer_start !== null && data.odometer_start !== undefined &&
        data.odometer_end !== null && data.odometer_end !== undefined) {
        return data.odometer_end >= data.odometer_start;
    }
    return true; // 如果其中一個是空的，不驗證大小關係
}, {
    message: "結束里程數必須大於或等於開始里程數",
    path: ["odometer_end"],
});

type TripFormData = z.infer<typeof tripSchema>;


export default function EditReservationPage() {
  const router = useRouter();
  const params = useParams();
  const reservationId = parseInt(params.id as string);
  const queryClient = useQueryClient();

  // 載入這筆預約的資料 (包含 trip)
  const { data: reservation, isLoading: isLoadingReservation, refetch: refetchReservation } = useQuery({
    queryKey: ['reservation', reservationId],
    queryFn: () => apiClient.getReservation(reservationId).then(res => res.data),
    enabled: !!reservationId,
  });

  // 載入所有員工 (用於顯示申請人名稱)
  const { data: employees, isLoading: isLoadingEmployees } = useQuery({
    queryKey: ['employees'],
    queryFn: () => apiClient.getEmployees().then(res => res.data),
  });

  // 載入所有 'active' 車輛 (用於指派)
  const { data: vehicles, isLoading: isLoadingVehicles } = useQuery({
    queryKey: ['vehicles'],
    queryFn: () => apiClient.getVehicles().then(res => res.data),
    select: (data) => data?.filter(v => v.status === 'active'), // 加入可選鏈 ?.
  });

  // --- 表單設定 ---
  // (管理預約表單)
  const {
    register: registerUpdate,
    handleSubmit: handleSubmitUpdate,
    formState: { errors: errorsUpdate },
    reset: resetUpdate,
    watch: watchUpdate, // 監聽表單變化
  } = useForm<ReservationUpdateFormData>({
    resolver: zodResolver(reservationUpdateSchema),
  });

  // (行程回報表單)
  const {
    register: registerTrip,
    handleSubmit: handleSubmitTrip,
    formState: { errors: errorsTrip },
    reset: resetTrip, // 加入 resetTrip
  } = useForm<TripFormData>({
    resolver: zodResolver(tripSchema),
  });

  // 當資料載入後，設定表單預設值
  useEffect(() => {
    if (reservation) {
      resetUpdate({
        status: reservation.status as any, // 直接使用 reservation 的 status
        vehicle_id: reservation.vehicle_id ?? undefined, // 使用 ?? 處理 null
      });
      // 如果已有 trip 資料，也設定 trip 表單的預設值
      if (reservation.trip) {
          resetTrip({
              odometer_start: reservation.trip.odometer_start ?? undefined,
              odometer_end: reservation.trip.odometer_end ?? undefined,
              fuel_liters: reservation.trip.fuel_liters ? Number(reservation.trip.fuel_liters) : undefined, // API 回傳 string，轉 number
              notes: reservation.trip.notes ?? '',
          });
      } else {
          // 如果沒有 trip 資料，清空 trip 表單
          resetTrip({
              odometer_start: undefined,
              odometer_end: undefined,
              fuel_liters: undefined,
              notes: '',
          });
      }
    }
  }, [reservation, resetUpdate, resetTrip]); // 加入 resetTrip

  // --- Mutations ---
  // (更新預約狀態/指派車輛)
  const updateMutation = useMutation({
    mutationFn: (data: ReservationUpdateFormData) => {
        // 從 watch 取得目前的 vehicle_id，因為 resetUpdate 可能還沒完全同步
        const currentVehicleId = watchUpdate('vehicle_id');
        const payload = {
            status: data.status,
            // 確保 vehicle_id 是數字或 null
            vehicle_id: currentVehicleId ? Number(currentVehicleId) : null,
        };
        console.log("Updating reservation with payload:", payload); // Debug log
        return apiClient.updateReservation(reservationId, payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reservations'] }); // 更新列表
      queryClient.invalidateQueries({ queryKey: ['reservation', reservationId] }); // 更新自己
      alert('預約更新成功！');
      // 可以選擇導回列表頁或留在原地
      // router.push('/reservations');
    },
    onError: (error: any) => {
      console.error("更新預約失敗:", error);
      const errorMsg = error.response?.data?.detail || error.message;
      alert(`更新預約失敗: ${errorMsg}`);
    },
  });

  // (提交行程回報)
  const tripMutation = useMutation({
      mutationFn: (data: TripFormData) => {
          if (!reservation || !reservation.vehicle_id || !reservation.requester_id) {
              throw new Error("預約資訊不完整，無法提交行程");
          }
          const payload = {
              ...data,
              vehicle_id: reservation.vehicle_id, // 從 reservation 取得
              driver_id: reservation.requester_id, // 預設使用申請人 ID
              // 將可能為 undefined 的值轉為 null
              odometer_start: data.odometer_start ?? null,
              odometer_end: data.odometer_end ?? null,
              fuel_liters: data.fuel_liters ?? null,
              notes: data.notes || null,
          };
          return apiClient.createTrip(reservationId, payload);
      },
      onSuccess: () => {
          queryClient.invalidateQueries({ queryKey: ['reservations'] });
          queryClient.invalidateQueries({ queryKey: ['reservation', reservationId] }); // 重新載入預約資料 (狀態會變 completed, trip 會出現)
          alert('行程回報成功！');
      },
      onError: (error: any) => {
          console.error("行程回報失敗:", error);
          const errorMsg = error.response?.data?.detail || error.message;
          alert(`行程回報失敗: ${errorMsg}`);
      },
  });

  // --- Submit Handlers ---
  const onSubmitUpdate = (data: ReservationUpdateFormData) => {
      console.log("Submitting reservation update:", data); // Debug log
      updateMutation.mutate(data);
  };

  const onSubmitTrip = (data: TripFormData) => {
      tripMutation.mutate(data);
  };

  // --- Helper Functions & Data ---
  const statusOptions = [
    { value: 'pending', label: '待審核' },
    { value: 'approved', label: '已核准' },
    { value: 'in_progress', label: '進行中' }, // (也許需要加入)
    { value: 'completed', label: '已完成' },
    { value: 'rejected', label: '已拒絕' },
    { value: 'cancelled', label: '已取消' }, // 合併使用者/管理員取消
  ];

  const getEmployeeName = (id: number) => {
    return employees?.find(e => e.id === id)?.name || `員工ID: ${id}`;
  };

  const getVehiclePlate = (id: number | null | undefined) => { // 允許 null/undefined
      if (!id) return '未指派';
      // 注意：這裡的 vehicles 只包含 active 的，如果預約是指派非 active 車輛，會找不到
      // 更好的做法是另外載入所有車輛或直接用 reservation 裡回傳的 vehicle plate (如果後端有提供)
      const vehicle = vehicles?.find(v => v.id === id);
      return vehicle ? `${vehicle.plate_no} (${vehicle.make} ${vehicle.model})` : `車輛ID: ${id}`;
  }

  // --- Loading & Error States ---
  if (isLoadingReservation || isLoadingEmployees || isLoadingVehicles) {
    return <div className="text-center p-8">載入資料中...</div>;
  }

  if (!reservation) {
      return <div className="text-center p-8 text-red-600">找不到該預約 (ID: {reservationId})</div>;
  }

  // --- Render Logic ---
  const canManage = ['pending', 'approved'].includes(reservation.status); // 只有 pending 或 approved 才能管理
  const canReportTrip = ['approved', 'in_progress'].includes(reservation.status) && !reservation.trip; // 只有 approved 或 in_progress 且尚未回報才能回報
  const hasTripReported = !!reservation.trip; // 是否已回報

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">管理預約 (ID: {reservation.id})</h1>
        <Link href="/reservations" className="text-gray-600 hover:text-gray-900">
          ← 返回列表
        </Link>
      </div>

      {/* 顯示預約的靜態資訊 */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">預約詳情</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div>
            <p className="text-sm text-gray-500">申請人</p>
            <p className="font-medium">{getEmployeeName(reservation.requester_id)}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">用途</p>
            <p className="font-medium">{reservation.purpose}</p>
          </div>
           <div>
            <p className="text-sm text-gray-500">目的地</p>
            <p className="font-medium">{reservation.destination || '-'}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">開始時間</p>
            <p className="font-medium">{format(new Date(reservation.start_ts), 'yyyy-MM-dd HH:mm')}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">結束時間</p>
            <p className="font-medium">{format(new Date(reservation.end_ts), 'yyyy-MM-dd HH:mm')}</p>
          </div>
           <div>
            <p className="text-sm text-gray-500">目前狀態</p>
            <p className="font-medium">{reservation.status}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">目前指派車輛</p>
            <p className="font-medium">{getVehiclePlate(reservation.vehicle_id)}</p>
          </div>
        </div>
      </div>

      {/* 管理操作表單 (僅在可管理狀態下顯示) */}
      {canManage && (
        <div className="bg-white rounded-lg shadow p-8 mb-6">
          <h2 className="text-xl font-semibold mb-4">管理操作</h2>
          <p className="text-sm text-gray-500 mb-4">
            請更新預約狀態或指派/變更車輛。
            <br />
            - 將狀態改為 'approved' 並指派車輛以核准。
            <br />
            - 將狀態改為 'rejected' 或 'cancelled' 以拒絕或取消。
          </p>
          {/* 使用 handleSubmitUpdate 和 onSubmitUpdate */}
          <form onSubmit={handleSubmitUpdate(onSubmitUpdate)} className="space-y-6">
            {/* 狀態 */}
            <div>
              <label htmlFor="status" className="block text-sm font-medium text-gray-700">
                更新狀態 <span className="text-red-600">*</span>
              </label>
              <select
                id="status"
                {...registerUpdate('status')}
                className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${errorsUpdate.status ? 'border-red-500' : ''}`}
              >
                {/* 可以根據目前狀態篩選可選的下個狀態 */}
                {statusOptions.map(option => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
              {errorsUpdate.status && (
                <p className="mt-1 text-sm text-red-600">{errorsUpdate.status.message}</p>
              )}
            </div>

            {/* 指派車輛 */}
            <div>
              <label htmlFor="vehicle_id" className="block text-sm font-medium text-gray-700">
                指派/變更車輛
              </label>
              <select
                id="vehicle_id"
                {...registerUpdate('vehicle_id')}
                disabled={isLoadingVehicles}
                className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${errorsUpdate.vehicle_id ? 'border-red-500' : ''}`}
              >
                <option value="">-- 不指定/清空指派 --</option>
                {vehicles?.map(v => (
                  <option key={v.id} value={v.id}>{v.plate_no} ({v.make} {v.model})</option>
                ))}
              </select>
              {errorsUpdate.vehicle_id && (
                <p className="mt-1 text-sm text-red-600">{errorsUpdate.vehicle_id.message}</p>
              )}
            </div>

            {/* 提交按鈕 */}
            <div className="flex justify-end">
              <button
                type="submit"
                disabled={updateMutation.isPending}
                className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
              >
                {updateMutation.isPending ? '更新中...' : '更新預約'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* 行程回報表單 (僅在可回報狀態下顯示) */}
      {canReportTrip && (
          <div className="bg-white rounded-lg shadow p-8 mb-6">
              <h2 className="text-xl font-semibold mb-4">行程回報 (還車)</h2>
              {/* 使用 handleSubmitTrip 和 onSubmitTrip */}
              <form onSubmit={handleSubmitTrip(onSubmitTrip)} className="space-y-6">
                  {/* 里程 */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                          <label htmlFor="odometer_start" className="block text-sm font-medium text-gray-700">
                              開始里程數
                          </label>
                          <input
                              type="number"
                              id="odometer_start"
                              {...registerTrip('odometer_start')}
                              className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${errorsTrip.odometer_start ? 'border-red-500' : ''}`}
                          />
                          {errorsTrip.odometer_start && (
                              <p className="mt-1 text-sm text-red-600">{errorsTrip.odometer_start.message}</p>
                          )}
                      </div>
                      <div>
                          <label htmlFor="odometer_end" className="block text-sm font-medium text-gray-700">
                              結束里程數
                          </label>
                          <input
                              type="number"
                              id="odometer_end"
                              {...registerTrip('odometer_end')}
                              className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${errorsTrip.odometer_end ? 'border-red-500' : ''}`}
                          />
                          {errorsTrip.odometer_end && (
                              <p className="mt-1 text-sm text-red-600">{errorsTrip.odometer_end.message}</p>
                          )}
                      </div>
                  </div>
                  {/* 加油量 */}
                  <div>
                      <label htmlFor="fuel_liters" className="block text-sm font-medium text-gray-700">
                          加油量 (公升) (選填)
                      </label>
                      <input
                          type="number"
                          step="0.01" // 允許小數
                          id="fuel_liters"
                          {...registerTrip('fuel_liters')}
                          className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${errorsTrip.fuel_liters ? 'border-red-500' : ''}`}
                      />
                      {errorsTrip.fuel_liters && (
                          <p className="mt-1 text-sm text-red-600">{errorsTrip.fuel_liters.message}</p>
                      )}
                  </div>
                  {/* 備註 */}
                  <div>
                      <label htmlFor="notes" className="block text-sm font-medium text-gray-700">
                          備註 (選填)
                      </label>
                      <textarea
                          id="notes"
                          {...registerTrip('notes')}
                          rows={3}
                          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                      />
                  </div>
                  {/* 提交按鈕 */}
                  <div className="flex justify-end">
                      <button
                          type="submit"
                          disabled={tripMutation.isPending}
                          className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50"
                      >
                          {tripMutation.isPending ? '提交中...' : '提交行程回報'}
                      </button>
                  </div>
              </form>
          </div>
      )}

      {/* 已完成的行程資訊 */}
      {hasTripReported && reservation.trip && (
          <div className="bg-gray-100 rounded-lg shadow p-6 mb-6">
              <h2 className="text-xl font-semibold mb-4 text-gray-700">已回報行程</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                      <p className="text-sm text-gray-500">回報時間</p>
                      <p className="font-medium">{format(new Date(reservation.trip.returned_at), 'yyyy-MM-dd HH:mm')}</p>
                  </div>
                  <div>
                      <p className="text-sm text-gray-500">開始里程</p>
                      <p className="font-medium">{reservation.trip.odometer_start ?? '-'}</p>
                  </div>
                  <div>
                      <p className="text-sm text-gray-500">結束里程</p>
                      <p className="font-medium">{reservation.trip.odometer_end ?? '-'}</p>
                  </div>
                  <div>
                      <p className="text-sm text-gray-500">行駛里程</p>
                      <p className="font-medium">
                          {(reservation.trip.odometer_end && reservation.trip.odometer_start)
                              ? `${reservation.trip.odometer_end - reservation.trip.odometer_start} km`
                              : '-'}
                      </p>
                  </div>
                  <div>
                      <p className="text-sm text-gray-500">加油量</p>
                      <p className="font-medium">{reservation.trip.fuel_liters ? `${reservation.trip.fuel_liters} L` : '-'}</p>
                  </div>
              </div>
               {reservation.trip.notes && (
                   <div className="mt-4">
                      <p className="text-sm text-gray-500">備註</p>
                      <p className="font-medium whitespace-pre-wrap">{reservation.trip.notes}</p>
                  </div>
               )}
          </div>
      )}

    </div>
  );
}