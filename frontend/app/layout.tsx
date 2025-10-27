import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import Navbar from '@/components/Navbar';
import Sidebar from '@/components/Sidebar';
import ReactQueryProvider from '@/lib/react-query-provider';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: '公務車管理系統',
  description: '公務車與機車管理系統',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-TW">
      <body className={inter.className}>
        <ReactQueryProvider>
          {/* (!!! 修改外層 div，讓 Navbar 延伸，Sidebar 和 Main 在下方 flex) !!! */}
          <div className="min-h-screen flex flex-col bg-gray-50">
            <Navbar />
            <div className="flex flex-1"> {/* flex-1 讓內容區填滿剩餘高度 */}
              <Sidebar />
              {/* (!!! 修改 main 元素，加入 md:ml-64 !!!) */}
              <main className="flex-1 p-6 md:ml-64"> {/* 在 md 以上螢幕增加左邊距 */}
                {children}
              </main>
            </div>
          </div>
        </ReactQueryProvider>
      </body>
    </html>
  );
}

