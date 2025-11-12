// portal/frontend/app/layout.tsx
import "./globals.css";
import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Jesse A. Eisenbalm - Content Portal",
  description: "Generate posts and copy/paste to LinkedIn",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body 
        className="text-gray-900 min-h-screen flex flex-col"
        style={{ background: 'linear-gradient(180deg, #f6f9fc 0%, #ffffff 100%)' }}
      >
        {/* Header Navigation */}
        <header className="relative bg-white shadow-sm border-b border-gray-200">
          <nav className="max-w-7xl mx-auto px-6 md:px-8 py-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex flex-col md:flex-row md:items-center gap-6 md:gap-10">
              <div className="flex items-center gap-4">
                <div 
                  className="w-10 h-10 rounded-lg flex items-center justify-center shadow-lg"
                  style={{
                    background: 'linear-gradient(135deg, #635BFF 0%, #4F46E5 100%)',
                  }}
                >
                  <span className="text-white text-lg font-semibold">JE</span>
                </div>
                <h1 className="text-xl md:text-2xl font-semibold">
                  Content Manager
                </h1>
              </div>
              <div className="flex gap-6 md:gap-8">
                <Link
                  href="/"
                  className="text-gray-600 hover:text-purple-600 transition-colors duration-300 text-sm font-medium uppercase tracking-wider flex items-center gap-2"
                >
                  <span>📝</span>
                  <span>Dashboard</span>
                </Link>
                
              </div>
            </div>
            <div className="text-xs text-gray-500 font-medium uppercase tracking-widest">
              Content Portal
            </div>
          </nav>
        </header>

        {/* Main Content */}
        <main className="relative flex-1">{children}</main>

        {/* Footer */}
        <footer className="relative bg-white shadow-sm border-t border-gray-200 py-6">
          <div className="max-w-7xl mx-auto px-6 md:px-8">
            <div className="flex flex-col md:flex-row items-center justify-between gap-4">
              <div className="text-xs text-gray-500 font-medium">
                Jesse A. Eisenbalm Content Portal
              </div>
              <div className="flex items-center gap-3 text-xs text-gray-600 font-medium">
                <span>Powered by</span>
                <span className="text-purple-600">Gemini</span>
                <span className="text-gray-300">•</span>
                <span className="text-purple-600">OpenAI</span>
              </div>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}