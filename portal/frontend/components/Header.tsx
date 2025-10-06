"use client";

import Link from "next/link";
import { linkedInLoginUrl } from "@/lib/api";
import { Button } from "@/components/ui/button";

export default function Header() {
  const loginUrl = linkedInLoginUrl(true);

  return (
    <header className="border-b border-zinc-200">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
        <div className="flex items-center gap-6">
          <Link href="/" className="font-semibold">
            Content Portal
          </Link>
          <nav className="hidden gap-4 sm:flex">
            <Link href="/dashboard" className="text-sm text-zinc-700 hover:underline">
              Dashboard
            </Link>
            <Link href="/approved" className="text-sm text-zinc-700 hover:underline">
              Approved
            </Link>
          </nav>
        </div>

        <div className="flex items-center gap-2">
          <a href={loginUrl} rel="noopener noreferrer">
            <Button variant="outline">Connect LinkedIn</Button>
          </a>
        </div>
      </div>
    </header>
  );
}
