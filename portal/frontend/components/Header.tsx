// portal/frontend/components/Header.tsx
"use client";

import Link from "next/link";
import ConnectLinkedInButton from "@/components/ConnectLinkedInButton";

export default function Header() {
  return (
    <header className="sticky top-0 z-30 bg-white/80 backdrop-blur supports-[backdrop-filter]:bg-white/60 border-b border-zinc-100">
      <div className="mx-auto max-w-5xl px-4 h-14 flex items-center justify-between">
        <nav className="flex items-center gap-6">
          <Link href="/" className="text-sm font-medium hover:text-zinc-900 text-zinc-700">
            Home
          </Link>
          <Link href="/dashboard" className="text-sm font-medium hover:text-zinc-900 text-zinc-700">
            Dashboard
          </Link>
          <Link href="/approved" className="text-sm font-medium hover:text-zinc-900 text-zinc-700">
            Approved
          </Link>
        </nav>

        {/* One canonical connect button in the header */}
        <ConnectLinkedInButton includeOrg className="shrink-0" />
      </div>
    </header>
  );
}
