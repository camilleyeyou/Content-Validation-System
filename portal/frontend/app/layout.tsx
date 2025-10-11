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
      <body className="bg-zinc-50 text-zinc-900 min-h-screen flex flex-col">
        {/* Header Navigation */}
        <header className="bg-zinc-900 text-white shadow-lg">
          <nav className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-8">
              <h1 className="text-xl font-bold">Jesse A. Eisenbalm</h1>
              <div className="flex gap-6">
                <Link
                  href="/"
                  className="text-white hover:text-zinc-300 transition-colors text-sm font-medium"
                >
                  📝 Dashboard
                </Link>
                <Link
                  href="/prompts"
                  className="text-white hover:text-zinc-300 transition-colors text-sm font-medium"
                >
                  🤖 Agent Prompts
                </Link>
              </div>
            </div>
            <div className="text-xs text-zinc-400">Content Portal</div>
          </nav>
        </header>

        {/* Main Content */}
        <main className="flex-1">{children}</main>

        {/* Footer */}
        <footer className="bg-zinc-100 border-t border-zinc-200 py-4 text-center text-xs text-zinc-600">
          <div className="max-w-7xl mx-auto px-6">
            Jesse A. Eisenbalm Content Portal • Powered by Claude & OpenAI
          </div>
        </footer>
      </body>
    </html>
  );
}