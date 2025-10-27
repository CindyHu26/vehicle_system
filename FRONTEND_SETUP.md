# 前端設定指南

## 快速開始

### 1. 安裝依賴

```bash
cd frontend
npm install
```

### 2. 設定環境變數

建立 `frontend/.env.local` 檔案：

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. 啟動前端

```bash
npm run dev
```

前端將在 `http://localhost:3000` 啟動。

### 4. 確保後端正在執行

後端 API 必須在 `http://localhost:8000` 執行。

```bash
# 在專案根目錄
uvicorn main:app --reload
```

## 專案結構

```
frontend/
├── app/                    # Next.js App Router (頁面)
│   ├── layout.tsx         # 根佈局
│   ├── page.tsx           # 首頁（儀表板）
│   ├── vehicles/          # 車輛管理
│   │   ├── page.tsx       # 車輛列表
│   │   └── [id]/          # 車輛詳情
│   ├── reservations/       # 借車申請
│   ├── employees/          # 員工管理
│   ├── work-orders/       # 工單管理
│   └── analytics/          # 分析報表
├── components/             # 共用元件
│   ├── Navbar.tsx         # 導航列
│   └── Sidebar.tsx        # 側邊欄
├── lib/                    # 工具函式
│   ├── api.ts             # API 客戶端
│   └── react-query-provider.tsx
├── package.json
├── tailwind.config.js
└── tsconfig.json
```

## 技術棧

- **Next.js 14** - React 框架，使用 App Router
- **TypeScript** - 型別安全
- **Tailwind CSS** - 樣式設計
- **React Query** - 資料獲取與快取
- **Axios** - HTTP 客戶端

## 主要功能

### 已實作

1. **儀表板** (`/`) - 顯示車輛概覽與合規狀態
2. **車輛管理** (`/vehicles`) - 查看車輛列表
3. **車輛詳情** (`/vehicles/[id]`) - 查看單一車輛詳情
4. **借車申請** (`/reservations`) - 查看借車記錄
5. **員工管理** (`/employees`) - 查看員工資訊
6. **導航系統** - 側邊欄與導航列

### 開發中

1. 新增車輛表單
2. 借車申請表單
3. 工單管理功能
4. 分析報表功能
5. 響應式設計改進

## 開發指南

### 新增頁面

1. 在 `app/` 目錄下建立新的資料夾（例如 `app/my-page/`）
2. 建立 `page.tsx` 檔案
3. 使用 `'use client'` 指令啟用客戶端元件

範例：

```tsx
// app/my-page/page.tsx
'use client';

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';

export default function MyPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['my-data'],
    queryFn: async () => {
      const response = await apiClient.getVehicles();
      return response.data;
    },
  });

  if (isLoading) return <div>載入中...</div>;

  return <div>{/* 你的內容 */}</div>;
}
```

### 新增 API 方法

在 `lib/api.ts` 中新增：

```typescript
export const apiClient = {
  // ... 現有方法
  
  myNewMethod: () => api.get('/api/v1/my-endpoint'),
};
```

### 樣式

使用 Tailwind CSS 類別：

```tsx
<div className="bg-white rounded-lg shadow p-6">
  <h1 className="text-3xl font-bold">標題</h1>
</div>
```

### 資料獲取

使用 React Query：

```tsx
const { data, isLoading, error } = useQuery({
  queryKey: ['unique-key'],
  queryFn: async () => {
    const response = await apiClient.someMethod();
    return response.data;
  },
});
```

## 已知問題

1. 移動端側邊欄未隱藏
2. 部分頁面缺少新增/編輯功能
3. 錯誤處理需要改進
4. 缺少載入骨架（Skeleton）
5. 缺少錯誤邊界

## 下一步

1. 實作新增車輛表單
2. 實作借車申請表單
3. 改進響應式設計
4. 加入錯誤處理
5. 加入載入狀態
6. 加入權限管理
7. 加入登入頁面

## 除錯

### CORS 錯誤

如果遇到 CORS 錯誤，請確認後端的 `main.py` 中已啟用 CORS：

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### API 連線失敗

1. 確認後端正在執行
2. 確認 `.env.local` 中的 `NEXT_PUBLIC_API_URL` 正確
3. 檢查瀏覽器控制台是否有錯誤

### 依賴安裝問題

```bash
# 清除快取
rm -rf node_modules package-lock.json
npm install
```


