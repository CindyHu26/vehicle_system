# 公務車管理系統 - 前端

這是公務車管理系統的前端應用程式，使用 Next.js 14 + React 18 + TypeScript 建置。

## 功能特色

- 📊 **儀表板** - 查看車輛概覽與合規狀態
- 🚗 **車輛管理** - 查看、管理車輛資訊
- 📝 **借車申請** - 查看借車記錄與狀態
- 👥 **員工管理** - 查看員工資訊
- 📋 **工單管理** - 查看維護工單（開發中）
- 📊 **分析報表** - 查看統計分析（開發中）

## 技術棧

- **Next.js 14** - React 框架
- **TypeScript** - 型別安全
- **Tailwind CSS** - 樣式設計
- **React Query** - 資料獲取與快取
- **Axios** - HTTP 客戶端

## 安裝與執行

### 前置需求

- Node.js 18+
- npm 或 yarn
- 後端 API 伺服器正在執行（`http://localhost:8000`）

### 安裝步驟

1. **安裝依賴**

```bash
cd frontend
npm install
# 或
yarn install
```

2. **設定環境變數**

建立 `.env.local` 檔案：

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

3. **啟動開發伺服器**

```bash
npm run dev
# 或
yarn dev
```

應用程式將在 `http://localhost:3000` 啟動。

## 專案結構

```
frontend/
├── app/                    # Next.js App Router
│   ├── layout.tsx         # 根佈局
│   ├── page.tsx           # 首頁（儀表板）
│   ├── vehicles/          # 車輛管理
│   ├── reservations/       # 借車申請
│   ├── employees/          # 員工管理
│   └── globals.css        # 全域樣式
├── components/             # 共用元件
│   ├── Navbar.tsx         # 導航列
│   └── Sidebar.tsx        # 側邊欄
├── lib/                    # 工具函式
│   ├── api.ts             # API 客戶端
│   └── react-query-provider.tsx
├── package.json           # 專案依賴
├── tailwind.config.js     # Tailwind 設定
└── tsconfig.json          # TypeScript 設定
```

## 功能說明

### 儀表板 (`/`)
- 顯示車輛總數、合規率
- 車輛列表
- 合規警告

### 車輛管理 (`/vehicles`)
- 查看所有車輛
- 查看車輛詳情（保險、違規等）
- 新增車輛（開發中）

### 借車申請 (`/reservations`)
- 查看所有借車申請
- 查看申請狀態

### 員工管理 (`/employees`)
- 查看所有員工
- 查看員工基本資訊

## 開發指南

### 新增頁面

1. 在 `app/` 目錄下建立新的路由資料夾
2. 建立 `page.tsx` 檔案
3. 使用 `useQuery` hook 獲取資料

範例：

```tsx
'use client';

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';

export default function MyPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['my-key'],
    queryFn: async () => {
      const response = await apiClient.someMethod();
      return response.data;
    },
  });

  if (isLoading) return <div>載入中...</div>;

  return <div>{/* 你的內容 */}</div>;
}
```

### 新增 API 方法

在 `lib/api.ts` 中新增 API 方法：

```typescript
export const apiClient = {
  // ... 現有方法
  
  // 新增你的方法
  myMethod: () => api.get('/api/v1/my-endpoint'),
};
```

### 樣式規範

- 使用 Tailwind CSS 類別
- 顏色使用主題色 `primary-*`
- 響應式設計使用 `md:`, `lg:` 等前綴

## 已知問題

1. Sidebar 在移動端尚未隱藏（需要添加響應式設計）
2. 部分頁面功能尚未完全實作（新增、編輯）
3. 錯誤處理需要改進

## 未來改進

- [ ] 新增車輛表單
- [ ] 借車申請表單
- [ ] 編輯功能
- [ ] 權限管理
- [ ] 登入頁面
- [ ] 響應式設計改進
- [ ] 載入狀態優化
- [ ] 錯誤處理改進

## 授權

Copyright © 2025


