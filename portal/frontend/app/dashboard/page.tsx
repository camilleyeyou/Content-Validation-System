// portal/frontend/app/dashboard/page.tsx
"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { apiGet, apiPost } from "@/lib/config";

type ApprovedRec = {
  id: string;
  content: string;
  hashtags: string[];
  status: string;
  created_at: string;
  li_post_id?: string | null;
  error_message?: string | null;
};

export default function DashboardPage() {
  const [approved, setApproved] = React.useState<ApprovedRec[]>([]);
  const [sel, setSel] = React.useState<Record<string, boolean>>({});
  const [busy, setBusy] = React.useState(false);
  const [notice, setNotice] = React.useState<string | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(true);

  const selectedIds = React.useMemo(
    () => Object.entries(sel).filter(([, v]) => v).map(([k]) => k),
    [sel]
  );

  const load = React.useCallback(async () => {
    setError(null);
    setLoading(true);
    try {
      const list = await apiGet<ApprovedRec[]>("/api/approved");
      setApproved(Array.isArray(list) ? list : []);
    } catch (e: any) {
      setError(e?.message || "Failed to load queue");
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    load();
  }, [load]);

  function toggleAll(checked: boolean) {
    const next: Record<string, boolean> = {};
    for (const p of approved) next[p.id] = checked;
    setSel(next);
  }

  async function onPublish(publishNow: boolean) {
    if (selectedIds.length === 0) {
      setError("Select at least one post");
      return;
    }
    setBusy(true);
    setNotice(null);
    setError(null);
    try {
      const res = await apiPost<{ successful: number; results: any[]; errors?: any[] }>(
        "/api/approved/publish",
        { ids: selectedIds, target: "MEMBER", publish_now: publishNow }
      );
      if (res.errors?.length) {
        setError(`Some items failed (${res.successful}/${selectedIds.length}).`);
      } else {
        setNotice(`${publishNow ? "Published" : "Drafted"}: ${res.successful}/${selectedIds.length}`);
      }
      setSel({});
      await load();
    } catch (e: any) {
      setError(e?.message || "Publish failed");
    } finally {
      setBusy(false);
    }
  }

  async function onClear() {
    setBusy(true);
    setNotice(null);
    setError(null);
    try {
      const res = await apiPost<{ deleted: number }>("/api/approved/clear", {});
      setNotice(`Cleared ${res.deleted} item(s).`);
      setSel({});
      await load();
    } catch (e: any) {
      setError(e?.message || "Clear failed");
    } finally {
      setBusy(false);
    }
  }

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold">Publishing Dashboard</h1>
        </div>
        <div className="flex items-center justify-center py-12">
          <div className="text-zinc-600">Loading…</div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Publishing Dashboard</h1>
          <p className="text-sm text-zinc-600">Global queue — publish/draft/clear.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={load}>Refresh</Button>
        </div>
      </div>

      {/* Status */}
      {notice && <div className="rounded-xl bg-green-50 text-green-800 border border-green-200 px-4 py-3">{notice}</div>}
      {error && <div className="rounded-xl bg-red-50 text-red-800 border border-red-200 px-4 py-3">{error}</div>}

      {/* Queue */}
      <Card className="p-0">
        <div className="px-4 py-3 border-b">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-semibold">Approved Queue</div>
              <div className="text-sm text-zinc-600">
                {approved.length ? `${approved.length} post${approved.length === 1 ? "" : "s"} ready` : "No approved posts"}
              </div>
            </div>
            {approved.length > 0 && (
              <div className="text-sm">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    onChange={(e) => toggleAll(e.target.checked)}
                    checked={approved.length > 0 && approved.every((p) => sel[p.id])}
                  />
                  Select all
                </label>
              </div>
            )}
          </div>
        </div>

        <div className="divide-y divide-zinc-100">
          {approved.length === 0 ? (
            <div className="px-6 py-8 text-sm text-zinc-600 text-center">
              Nothing to publish. Push items to <code>/api/approved/add</code> from your generator.
            </div>
          ) : (
            approved.map((p) => (
              <label key={p.id} className="flex items-start gap-3 px-6 py-4 hover:bg-zinc-50 cursor-pointer">
                <input
                  type="checkbox"
                  checked={!!sel[p.id]}
                  onChange={(e) => setSel((s) => ({ ...s, [p.id]: e.target.checked }))}
                  className="mt-1 h-4 w-4"
                />
                <div className="min-w-0 flex-1">
                  <div className="font-medium">{p.content || "No content"}</div>
                  {p.hashtags?.length ? (
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {p.hashtags.map((h, i) => (
                        <span key={i} className="inline-flex items-center rounded-full bg-zinc-100 px-2.5 py-1 text-xs font-medium text-zinc-700">
                          #{h.replace(/^#/, "")}
                        </span>
                      ))}
                    </div>
                  ) : null}
                  <div className="mt-2 text-xs text-zinc-600">
                    Status: <span className="font-medium">{p.status || "approved"}</span>
                    {p.li_post_id && (
                      <span className="ml-2">Local ID: <span className="font-mono">{p.li_post_id}</span></span>
                    )}
                    {p.error_message && <div className="text-red-600 mt-1">{p.error_message}</div>}
                  </div>
                </div>
                <div className="text-xs text-zinc-500 shrink-0">
                  {p.created_at ? new Date(p.created_at).toLocaleDateString() : "Now"}
                </div>
              </label>
            ))
          )}
        </div>

        {approved.length > 0 && (
          <div className="flex items-center justify-between px-6 py-3 border-t">
            <div className="text-sm text-zinc-600">
              Selected: <span className="font-semibold">{selectedIds.length}</span> of {approved.length}
            </div>
            <div className="flex flex-wrap gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => onPublish(false)}
                disabled={busy || selectedIds.length === 0}
              >
                Save as Draft
              </Button>
              <Button
                size="sm"
                onClick={() => onPublish(true)}
                disabled={busy || selectedIds.length === 0}
              >
                Publish Now
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={onClear}
                disabled={busy}
              >
                Clear Queue
              </Button>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
