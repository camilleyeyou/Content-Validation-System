"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";

const API_BASE =
  (process.env.NEXT_PUBLIC_API_BASE || "").replace(/\/+$/, "") ||
  "http://localhost:8001";

export default function HomePage() {
  const loginUrl = `${API_BASE}/auth/linkedin/login?include_org=true`;

  return (
    <main className="min-h-[70vh] grid place-items-center px-6">
      <section className="max-w-4xl text-center space-y-8">
        <div className="inline-flex items-center rounded-full border border-zinc-200 bg-white px-3 py-1 text-xs text-zinc-600">
          LinkedIn Content Portal
        </div>

        <h1 className="text-4xl sm:text-5xl font-semibold leading-tight">
          Validate, approve & publish LinkedIn content with confidence
        </h1>

        <p className="mx-auto max-w-2xl text-zinc-600">
          Connect your LinkedIn account, run your generation/validation pipeline,
          and manually publish to a profile or company page — all in one clean,
          focused UI.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
          <a href={loginUrl}>
            <Button size="lg">Connect LinkedIn</Button>
          </a>
          <a href="/dashboard">
            <Button variant="outline" size="lg">
              Open Dashboard
            </Button>
          </a>
          <a href="/approved">
            <Button variant="ghost" size="lg">
              View Approved Queue
            </Button>
          </a>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-10">
          <Feature
            title="Human-in-the-loop"
            desc="Keep full control: review and publish only what you approve."
          />
          <Feature
            title="Org support"
            desc="Publish as your company page when the right scopes are granted."
          />
          <Feature
            title="Fast & simple"
            desc="Minimal UI, clear actions, and sensible defaults."
          />
        </div>
      </section>
    </main>
  );
}

function Feature({ title, desc }: { title: string; desc: string }) {
  return (
    <div className="rounded-2xl border border-zinc-200 bg-white p-6 text-left">
      <div className="text-sm font-semibold">{title}</div>
      <p className="mt-2 text-sm text-zinc-600">{desc}</p>
    </div>
  );
}
