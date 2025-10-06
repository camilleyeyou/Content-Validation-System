"use client";

import Link from "next/link";

function apiBase() {
  const raw = (process.env.NEXT_PUBLIC_API_BASE || "").replace(/\/+$/, "");
  return raw || "http://localhost:8001";
}

export default function Header() {
  const loginUrl = `${apiBase()}/auth/linkedin/login?include_org=true`;

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
          <a
            href={loginUrl}
            className="inline-flex items-center rounded-lg bg-black px-3 py-2 text-sm text-white hover:bg-zinc-800"
          >
            Connect LinkedIn
          </a>
        </nav>
      </div>
    </header>
  );
}
