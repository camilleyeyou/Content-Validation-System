"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";

function apiBase() {
  const raw = (process.env.NEXT_PUBLIC_API_BASE || "").replace(/\/+$/, "");
  return raw || "http://localhost:8001";
}

export default function Home() {
  const loginUrl = `${apiBase()}/auth/linkedin/login?include_org=true`;

  return (
    <main className="min-h-[70vh] flex flex-col items-center justify-center gap-6 p-8">
      <h1 className="text-3xl font-semibold text-center">LinkedIn Content Portal</h1>
      <p className="max-w-prose text-center text-zinc-600">
        Validate, approve and publish LinkedIn content to your profile or company page.
      </p>
      <div className="flex items-center gap-3">
        <a href={loginUrl}>
          <Button>Connect LinkedIn</Button>
        </a>
        <Link href="/dashboard">
          <Button variant="outline">Go to Dashboard</Button>
        </Link>
      </div>
    </main>
  );
}
