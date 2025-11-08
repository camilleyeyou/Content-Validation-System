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
        className="bg-black text-white min-h-screen flex flex-col"
        style={{ background: 'linear-gradient(to bottom, #000000 0%, #0a0a0a 50%, #000000 100%)' }}
      >
        {/* Subtle grain texture overlay */}
        <div 
          className="fixed inset-0 opacity-[0.015] pointer-events-none" 
          style={{
            backgroundImage: 'url("data:image/svg+xml,%3Csvg viewBox=\'0 0 400 400\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cfilter id=\'noiseFilter\'%3E%3CfeTurbulence type=\'fractalNoise\' baseFrequency=\'0.9\' numOctaves=\'4\' stitchTiles=\'stitch\'/%3E%3C/filter%3E%3Crect width=\'100%25\' height=\'100%25\' filter=\'url(%23noiseFilter)\'/%3E%3C/svg%3E")',
          }}
        />

        {/* Header Navigation */}
        <header className="relative bg-black/40 backdrop-blur-sm border-b border-[#d4af37]/20 shadow-2xl">
          <nav className="max-w-[1400px] mx-auto px-6 md:px-8 py-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex flex-col md:flex-row md:items-center gap-6 md:gap-10">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 bg-gradient-to-br from-[#d4af37] via-[#f4e4c1] to-[#d4af37] rounded-sm flex items-center justify-center shadow-lg">
                  <span className="text-black text-lg font-serif font-bold">JE</span>
                </div>
                <h1 className="text-xl md:text-2xl font-serif font-light tracking-wide">
                  Content Manager
                </h1>
              </div>
              <div className="flex gap-6 md:gap-8">
                <Link
                  href="/"
                  className="text-gray-300 hover:text-[#d4af37] transition-colors duration-300 text-sm font-light uppercase tracking-wider flex items-center gap-2"
                >
                  <span>📝</span>
                  <span>Dashboard</span>
                </Link>
                <Link
                  href="/prompts"
                  className="text-gray-300 hover:text-[#d4af37] transition-colors duration-300 text-sm font-light uppercase tracking-wider flex items-center gap-2"
                >
                  <span>🤖</span>
                  <span>Agent Prompts</span>
                </Link>
              </div>
            </div>
            <div className="text-xs text-gray-500 font-light uppercase tracking-widest">
              Content Portal
            </div>
          </nav>
        </header>

        {/* Main Content */}
        <main className="relative flex-1">{children}</main>

        {/* Footer */}
        <footer className="relative bg-black/40 backdrop-blur-sm border-t border-[#d4af37]/20 py-6">
          <div className="max-w-[1400px] mx-auto px-6 md:px-8">
            <div className="flex flex-col md:flex-row items-center justify-between gap-4">
              <div className="text-xs text-gray-500 font-light">
                Jesse A. Eisenbalm Content Portal
              </div>
              <div className="flex items-center gap-3 text-xs text-gray-600 font-light">
                <span>Powered by</span>
                <span className="text-[#d4af37]">Gemini</span>
                <span className="text-gray-700">•</span>
                <span className="text-[#d4af37]">OpenAI</span>
              </div>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}