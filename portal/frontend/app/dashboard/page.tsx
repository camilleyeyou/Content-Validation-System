"use client";

import * as React from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import LinkedInAppSettings from "@/components/LinkedInAppSettings";
import { fetchApproved, runBatch, ApprovedRec, linkedInLoginUrl } from "@/lib/config";

export default function DashboardPage() {
  const [approved, setApproved] = React.useState<ApprovedRec[]>([]);
  const [busy, setBusy] = React.useState(false);

  const load = React.useCallback(async () => {
    const list = await fetchApproved();
    setApproved(list);
  }, []);

  React.useEffect(() => {
    load();
  }, [load]);

  async function onGenerate() {
    setBusy(true);
    try {
      const newItems = await runBatch(3);
      // Append immediately for snappy UX; then refresh to be safe:
      setApproved((prev) => [...newItems, ...prev]);
      await load();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Dashboard</h1>
          <p className="text-sm text-zinc-600">
            Configure LinkedIn, generate sample content, and publish.
          </p>
        </div>
        <a href={linkedInLoginUrl(true, typeof window !== "undefined" ? window.location.href : undefined)}>
          <Button variant="outline">Connect LinkedIn</Button>
        </a>
      </div>

      <LinkedInAppSettings />

      <Card>
        <CardHeader title="Quick Actions" />
        <CardContent className="flex items-center gap-3">
          <Button onClick={onGenerate} disabled={busy}>
            {busy ? "Generating…" : "Generate 3 Demo Posts"}
          </Button>
          <Link href="/approved">
            <Button variant="outline">Go to Approved Queue</Button>
          </Link>
        </CardContent>
      </Card>

      <Card>
        <CardHeader
          title="Recently Approved"
          description="The latest items in your approved queue"
        />
        <CardContent>
          {approved.length === 0 ? (
            <div className="text-sm text-zinc-600">No items yet. Click “Generate 3 Demo Posts”.</div>
          ) : (
            <ul className="space-y-3">
              {approved.slice(0, 5).map((p) => (
                <li key={p.id} className="border rounded-md p-3">
                  <div className="font-medium">{p.content.slice(0, 120)}{p.content.length > 120 ? "…" : ""}</div>
                  <div className="text-xs text-zinc-500 mt-1">
                    {new Date(p.created_at).toLocaleString()} • {p.status}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
