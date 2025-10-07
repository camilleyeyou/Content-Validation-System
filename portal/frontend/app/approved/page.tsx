"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import {
  apiGet,
  apiPost,
  linkedInLoginUrl,
  fetchApproved,
  ApprovedRec,
  normalizeApprovedResponse,
} from "@/lib/config";

type OrgsResp =
  | { orgs: { id: string; urn: string }[]; ok?: boolean }
  | { error?: string };

export default function ApprovedPage() {
  const [approved, setApproved] = React.useState<ApprovedRec[]>([]);
  const [orgs, setOrgs] = React.useState<{ id: string; urn: string }[]>([]);
  const [sel, setSel] = React.useState<Record<string, boolean>>({});
  const [busy, setBusy] = React.useState<{ publishing?: boolean; clearing?: boolean }>({});
  const [notice, setNotice] = React.useState<string | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  const selectedIds = React.useMemo(
    () => Object.entries(sel).filter(([, v]) => v).map(([k]) => k),
    [sel]
  );

  const loginUrl = linkedInLoginUrl(true);

  const load = React.useCallback(async () => {
    setError(null);
    try {
      // tolerate both old and new shapes
      const list = await fetchApproved();
      setApproved(list);

      // orgs require auth; tolerate 401/403
      try {
        const o = await apiGet<OrgsResp>("/api/orgs");
        if ("orgs" in o && Array.isArray(o.orgs)) setOrgs(o.orgs || []);
      } catch {
        // ignore; user might not be connected or lack org permissions
      }
    } catch (e: any) {
      setError(e?.message || "Failed to load");
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

  async function onPublish(target: "MEMBER" | "ORG", publishNow: boolean) {
    if (selectedIds.length === 0) return;
    setBusy((b) => ({ ...b, publishing: true }));
    setNotice(null);
    setError(null);
    try {
      const payload: any = {
        ids: selectedIds,
        target,
        publish_now: publishNow,
      };
      if (target === "ORG" && orgs[0]?.id) payload.org_id = orgs[0].id;

      const res = await apiPost<{ successful: number; results: any[] }>(
        "/api/approved/publish",
        payload
      );
      setNotice(`Publish: ${res.successful}/${selectedIds.length} succeeded.`);
      setSel({});
      await load();
    } catch (e: any) {
      setError(e?.message || "Publish failed");
    } finally {
      setBusy((b) => ({ ...b, publishing: false }));
    }
  }

  async function onClear() {
    setBusy((b) => ({ ...b, clearing: true }));
    setNotice(null);
    setError(null);
    try {
      await apiPost<{ deleted: number }>("/api/approved/clear", {});
      setNotice(`Cleared selection.`);
      setSel({});
      await load();
    } catch (e: any) {
      setError(e?.message || "Clear failed");
    } finally {
      setBusy((b) => ({ ...b, clearing: false }));
    }
  }

  const unauthorized = error?.startsWith("401");

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Approved Queue</h1>
          <p className="text-sm text-zinc-600">
            Select items and publish as member or organization.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <a href={loginUrl}>
            <Button variant="outline">Connect LinkedIn</Button>
          </a>
          <Button variant="ghost" onClick={load}>Refresh</Button>
        </div>
      </div>

      {notice ? (
        <div className="rounded-xl bg-green-50 text-green-800 border border-green-200 px-4 py-3">
          {notice}
        </div>
      ) : null}
      {error && !unauthorized ? (
        <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-red-800">
          {error}
        </div>
      ) : null}

      {unauthorized ? (
        <Card>
          <CardHeader
            title="You're not signed in"
            description="Connect LinkedIn to view and publish approved content."
            actions={
              <a href={loginUrl}>
                <Button>Connect LinkedIn</Button>
              </a>
            }
          />
          <CardContent>
            <p className="text-sm text-zinc-600">
              After connecting, you’ll be redirected back here automatically.
            </p>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader
            title={
              approved.length
                ? `${approved.length} item${approved.length > 1 ? "s" : ""}`
                : "No approved posts yet"
            }
            description="These items passed your pipeline and are ready to publish."
            actions={
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  onClick={() => onPublish("MEMBER", false)}
                  disabled={busy.publishing || selectedIds.length === 0}
                >
                  Draft as Member
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => onPublish("MEMBER", true)}
                  disabled={busy.publishing || selectedIds.length === 0}
                >
                  Publish Now (Member)
                </Button>
                <Button
                  variant="outline"
                  onClick={() => onPublish("ORG", false)}
                  disabled={busy.publishing || selectedIds.length === 0 || orgs.length === 0}
                >
                  Draft as Org
                </Button>
                <Button
                  onClick={() => onPublish("ORG", true)}
                  disabled={busy.publishing || selectedIds.length === 0 || orgs.length === 0}
                >
                  Publish Now (Org)
                </Button>
              </div>
            }
          />
          <CardContent className="p-0">
            {approved.length === 0 ? (
              <div className="px-6 py-8 text-sm text-zinc-600">Nothing here yet.</div>
            ) : (
              <div className="divide-y divide-zinc-100">
                <div className="flex items-center justify-between px-6 py-3 text-sm">
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      className="h-4 w-4"
                      checked={approved.length > 0 && approved.every((p) => sel[p.id])}
                      onChange={(e) => toggleAll(e.target.checked)}
                    />
                    <span>Select all</span>
                  </label>
                  <div className="text-zinc-500">
                    Org access:{" "}
                    <span className="font-medium">
                      {orgs.length > 0 ? "available" : "none"}
                    </span>
                  </div>
                </div>
                {approved.map((p) => (
                  <label
                    key={p.id}
                    className="flex items-start gap-3 px-6 py-4 hover:bg-zinc-50 cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      className="mt-1 h-4 w-4"
                      checked={!!sel[p.id]}
                      onChange={(e) =>
                        setSel((s) => ({ ...s, [p.id]: e.target.checked }))
                      }
                    />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between gap-3">
                        <div className="font-medium truncate">
                          {p.content.slice(0, 90)}
                          {p.content.length > 90 ? "…" : ""}
                        </div>
                        <div className="text-xs text-zinc-500">
                          {new Date(p.created_at).toLocaleString()}
                        </div>
                      </div>
                      {p.hashtags?.length ? (
                        <div className="mt-2 flex flex-wrap gap-1.5">
                          {p.hashtags.map((h, i) => (
                            <span
                              key={i}
                              className="inline-flex items-center rounded-full bg-zinc-100 px-2.5 py-1 text-xs font-medium text-zinc-700"
                            >
                              #{h.replace(/^#/, "")}
                            </span>
                          ))}
                        </div>
                      ) : null}
                      <div className="mt-2 text-xs text-zinc-600">
                        Status: <span className="font-medium">{p.status}</span>
                        {p.li_post_id ? (
                          <>
                            {" "}
                            • LinkedIn ID:{" "}
                            <span className="font-mono">{p.li_post_id}</span>
                          </>
                        ) : null}
                        {p.error_message ? (
                          <div className="text-red-600 mt-1">{p.error_message}</div>
                        ) : null}
                      </div>
                    </div>
                  </label>
                ))}
              </div>
            )}
          </CardContent>
          {approved.length > 0 ? (
            <CardFooter className="flex items-center justify-between">
              <div className="text-sm text-zinc-600">
                Selected: <span className="font-semibold">{selectedIds.length}</span>
              </div>
              <div className="flex items-center gap-2">
                <Button variant="ghost" onClick={() => setSel({})} disabled={!selectedIds.length}>
                  Clear selection
                </Button>
                <Button variant="outline" onClick={onClear} disabled={busy.clearing}>
                  Clear queue
                </Button>
              </div>
            </CardFooter>
          ) : null}
        </Card>
      )}
    </div>
  );
}
