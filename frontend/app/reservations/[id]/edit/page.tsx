// frontend/app/reservations/[id]/edit/page.tsx
'use client';

import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useRouter, useParams } from 'next/navigation';
import { apiClient, Reservation, Vehicle, Employee } from '@/lib/api'; // 匯入型別
import { useEffect } from 'react';
import { format } from 'date-fns';

// 1. Zod Schema (對應後端的 ReservationUpdate)
const reservationUpdateSchema = z.object({
  status: z.enum(['pending', 'approved', 'rejected', 'in_progress', 'completed', 'cancelled']),
  vehicle_id: z.preprocess( // 允許空字串轉為 undefined
    (val) => (val === "" || val === null ? null : val),
    z.coerce.number().int().optional().nullable()
  ),
});

type ReservationUpdateFormData = z.infer<typeof reservationUpdateSchema>;

export default function EditReservationPage() {
  const router = useRouter();
  const params = useParams();
  const reservationId = parseInt(params.id as string);
  const queryClient = useQueryClient();

  // 載入這筆預約的資料
  const { data: reservation, isLoading: isLoadingReservation } = useQuery({
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
    select: (data) => data.filter(v => v.status === 'active'),
  });

  // 設定 react-hook-form
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<ReservationUpdateFormData>({
    resolver: zodResolver(reservationUpdateSchema),
  });

  // 當資料載入後，設定表單預設值
  useEffect(() => {
    if (reservation) {
      reset({
        status: reservation.status as any, // 設置當前狀態
        vehicle_id: reservation.vehicle_id ?? undefined, // 設置當前指派的車輛
      });
    }
  }, [reservation, reset]);

  // 設定 mutation (呼叫更新 API)
  const mutation = useMutation({
    mutationFn: (data: ReservationUpdateFormData) => {
        const payload = {
            ...data,
            vehicle_id: data.vehicle_id ? Number(data.vehicle_id) : null,
        };
      return apiClient.updateReservation(reservationId, payload); // 呼叫更新 API
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reservations'] });
      queryClient.invalidateQueries({ queryKey: ['reservation', reservationId] });
      router.push('/reservations'); // 導回列表頁
    },
    onError: (error: any) => {
      console.error("更新預約失敗:", error);
      const errorMsg = error.response?.data?.detail || error.message;
      alert(`更新失敗: ${errorMsg}`); // 顯示後端錯誤 (例如衝突)
    },
  });

  const onSubmit = (data: ReservationUpdateFormData) => {
    mutation.mutate(data);
  };

  // 狀態選項
  const statusOptions = [
    { value: 'pending', label: '待審核' },
    { value: 'approved', label: '已核准' },
    { value: 'in_progress', label: '進行中' },
    { value: 'completed', label: '已完成' },
    { value: 'rejected', label: '已拒絕' },
    { value: 'cancelled', label: '已取消 (使用者/管理員取消)' },
  ];

  const getEmployeeName = (id: number) => {
    return employees?.find(e => e.id === id)?.name || `員工ID: ${id}`;
  };
  
  const getVehiclePlate = (id: number) => {
      return vehicles?.find(v => v.id === id)?.plate_no || `車輛ID: ${id}`;
  }

  if (isLoadingReservation || isLoadingEmployees || isLoadingVehicles) {
    return <div className="text-center p-8">載入資料中...</div>;
  }
  
  if (!reservation) {
      return <div className="text-center p-8 text-red-600">找不到該預約</div>;
  }

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
            <p className="text-sm text-gray-500">目前指派車輛</p>
            <p className="font-medium">{reservation.vehicle_id ? getVehiclePlate(reservation.vehicle_id) : '未指派'}</p>
          </div>
        </div>
      </div>

      {/* 編輯表單 */}
      <div className="bg-white rounded-lg shadow p-8">
        <h2 className="text-xl font-semibold mb-4">管理操作</h2>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">

          {/* 狀態 (編輯/取消) */}
          <div>
            <label htmlFor="status" className="block text-sm font-medium text-gray-700">
              更新狀態 (例如：取消預約) <span className="text-red-600">*</span>
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

          {/* 指派車輛 (編輯) */}
          <div>
            <label htmlFor="vehicle_id" className="block text-sm font-medium text-gray-700">
              指派/變更車輛
            </label>
            <select
              id="vehicle_id"
              {...register('vehicle_id')}
              disabled={isLoadingVehicles}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
            >
              <option value="">-- 不指定/清空指派 --</option>
              {vehicles?.map(v => (
                <option key={v.id} value={v.id}>{v.plate_no} ({v.make} {v.model})</option>
              ))}
            </select>
            {errors.vehicle_id && (
              <p className="mt-1 text-sm text-red-600">{errors.vehicle_id.message}</p>
            )}
          </div>

          {/* 提交按鈕 */}
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={mutation.isPending}
              className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
            >
              {mutation.isPending ? '更新中...' : '更新預約'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}