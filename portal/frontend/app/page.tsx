// portal/frontend/app/page.tsx
"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

export default function HomePage() {
  return (
    <div className="max-w-4xl mx-auto py-12 space-y-8">
      <div className="space-y-2">
        <h1 className="text-3xl font-semibold">Content Validation System</h1>
        <p className="text-zinc-600">
          Generate, approve, and publish LinkedIn content. Configure your LinkedIn app and connect your account from the dashboard.
        </p>
      </div>

      <Card className="p-6">
        <div className="flex items-center justify-between gap-4">
          <div className="text-sm text-zinc-700">
            Ready to set up LinkedIn and start generating content?
          </div>
          <Link href="/dashboard">
            <Button>Go to Dashboard →</Button>
          </Link>
        </div>
      </Card>

      <div className="text-xs text-zinc-500">
        Tip: make sure your Railway and Vercel domains are configured in CORS and that cookies are allowed so your session persists.
      </div>
    </div>
  );
}
