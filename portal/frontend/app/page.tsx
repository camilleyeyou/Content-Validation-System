"use client";

import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen">
      <header className="border-b border-zinc-200 bg-white/70 backdrop-blur sticky top-0 z-10">
        <div className="container flex items-center justify-between py-4">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-xl bg-black text-white grid place-items-center text-sm font-semibold">CV</div>
            <span className="font-semibold">Content Portal</span>
          </div>
          <nav className="flex items-center gap-2">
            <Link href="/dashboard" className="btn-ghost">Dashboard</Link>
            <a href={process.env.NEXT_PUBLIC_API_BASE + "/auth/linkedin/login?include_org=true"} className="btn-primary">
              Connect LinkedIn
            </a>
          </nav>
        </div>
      </header>

      <section className="container py-12">
        <div className="grid gap-6 md:grid-cols-3">
          <div className="card">
            <h3 className="text-lg font-semibold">1. Connect</h3>
            <p className="text-sm text-zinc-600 mt-2">
              Authenticate with LinkedIn (member or organization scopes) to post.
            </p>
          </div>
          <div className="card">
            <h3 className="text-lg font-semibold">2. Generate & Validate</h3>
            <p className="text-sm text-zinc-600 mt-2">
              Run the content pipeline. Approved posts land in a queue.
            </p>
          </div>
          <div className="card">
            <h3 className="text-lg font-semibold">3. Publish</h3>
            <p className="text-sm text-zinc-600 mt-2">
              Manually curate and publish to profile or company page.
            </p>
          </div>
        </div>
      </section>
    </main>
  );
}
