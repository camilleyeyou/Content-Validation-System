// portal/frontend/components/Header.tsx
"use client";

import Link from "next/link";
import { linkedInLoginUrl } from "@/lib/config";
import { Button } from "@/components/ui/button";

export default function Header() {
  return (
    <header className="sticky top-0 z-30 bg-white/80 backdrop-blur supports-[backdrop-filter]:bg-white/60 border-b border-zinc-100">
      <div className="mx-auto max-w-5xl px-4 h-14 flex items-center justify-between">
        <nav className="flex items-center gap-6">
          <Link href="/" className="font-semibold hover:opacity-80">Home</Link>
          <Link href="/dashboard" className="hover:opacity-80">Dashboard</Link>
          <Link href="/approved" className="hover:opacity-80">Approved</Link>
        </nav>
        <a href={linkedInLoginUrl(true)}>
          <Button variant="outline">Connect LinkedIn</Button>
        </a>
      </div>
    </header>
  );
}
