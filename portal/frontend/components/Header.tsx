"use client";

import Link from "next/link";

export default function Header() {
  return (
    <header className="sticky top-0 z-30 bg-white/90 backdrop-blur-lg border-b border-gray-200 shadow-sm">
      <div className="mx-auto max-w-7xl px-6 h-16 flex items-center justify-between">
        <div className="flex items-center gap-4">
          {/* Logo */}
          <div 
            className="w-10 h-10 rounded-lg flex items-center justify-center shadow-lg"
            style={{
              background: 'linear-gradient(135deg, #635BFF 0%, #4F46E5 100%)',
            }}
          >
            <span className="text-white text-lg font-semibold">JE</span>
          </div>

          {/* Navigation */}
          <nav className="flex items-center gap-6">
            <Link 
              href="/" 
              className="text-sm font-medium text-gray-700 hover:text-purple-600 transition-colors duration-200"
            >
              Home
            </Link>
            <Link 
              href="/dashboard" 
              className="text-sm font-medium text-gray-700 hover:text-purple-600 transition-colors duration-200"
            >
              Dashboard
            </Link>
            <Link 
              href="/approved" 
              className="text-sm font-medium text-gray-700 hover:text-purple-600 transition-colors duration-200"
            >
              Approved
            </Link>
          </nav>
        </div>

        {/* Right side - can add connect button here if needed */}
        <div className="flex items-center gap-4">
          {/* Placeholder for connect button */}
        </div>
      </div>
    </header>
  );
}