"use client";

import Link from "next/link";
import ConnectButton from "@/components/ConnectButton";

export default function Header() {
  return (
    <header className="border-b border-zinc-200 bg-white">
      <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 p-4">
        <Link href="/" className="text-lg font-semibold">
          Content Portal
        </Link>

        <nav className="flex items-center gap-4">
          <Link href="/dashboard" className="text-sm text-zinc-700 hover:text-black">
            Dashboard
          </Link>
          <Link href="/approved" className="text-sm text-zinc-700 hover:text-black">
            Approved
          </Link>
          {/* Top-right connect uses the same working component */}
          <ConnectButton />
        </nav>
      </div>
    </header>
  );
}
