"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { apiGet, apiPost } from "@/lib/config";
import ConnectLinkedInButton from "@/components/ConnectLinkedInButton";
import LinkedInAppSettings from "@/components/LinkedInAppSettings";

type Me = { sub: string; name: string; email?: string | null; org_preferred?: string | null };
type ApprovedRec = {
  id: string;
  content: string;
  hashtags: string[];
  status: string;
  created_at: string;
  li_post_id?: string | null;
  error_message?: string | null;
};
type OrgsResp = { orgs: { id: string; urn: string }[] } | { error?: string };

export default function DashboardPage() {
  const [me, setMe] = React.useState<Me | null>(null);
  const [orgs, setOrgs] = React.useState<{ id: string; urn: string }[]>([]);
  const [approved, setApproved] = React.useState<ApprovedRec[]>([]);
  const [sel, setSel] = React.useState<Record<string, boolean>>({});
  const [busy, setBusy] = React.useState<{ gen?: boolean; pub?: boolean }>({});
  const [notice, setNotice] = React.useState<string | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  const selectedIds = React.useMemo(
    () => Object.entries(sel).filter(([, v]) => v).map(([k]) => k),
    [sel]
  );

  const fetchAll = React.useCallback(async () => {
    setError(null);
    try {
      const [meResp, approvedResp] = await Promise.all([
        apiGet<Me>("/api/me"),
        apiGet<ApprovedRec[]>("/api/approved"),
      ]);
      setMe(meResp);
      setApproved(approvedResp);
      try {
        const o = await apiGet<OrgsResp>("/api/orgs");
        if ("orgs" in o) setOrgs(o.orgs || []);
      } catch {}
    } catch (e: any) {
      setError(e?.message || "Failed to load");
    }
  }, []);

  React.useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  function clearSelection() {
    setSel({});
  }

  async function onGenerateApproved() {
    setBusy((b) => ({ ...b, gen: true }));
    setNotice(null);
    setError(null);
    try {
      const res = await apiPost<{ approved_count: number; batch_id?: string }>(
        "/api/run-batch",
        {}
      );
      setNotice(`Generated ${res.approved_count} approved post(s).`);
      await fetchAll();
    } catch (e: any) {
      setError(`Generate failed: ${e?.message || e}`);
    } finally {
      setBusy((b) => ({ ...b, gen: false }));
    }
  }

  async function onPublish(target: "MEMBER" | "ORG", publishNow: boolean) {
    if (selectedIds.length === 0) return;
    setBusy((b) => ({ ...b, pub: true }));
    setNotice(null);
    setError(null);
    try {
      const payload: any = { ids: selectedIds, target, publish_now: publishNow };
      if (target === "ORG" && orgs[0]?.id) payload.org_id = orgs[0].id;

      const res = await apiPost<{ successful: number; results: any[] }>(
        "/api/approved/publish",
        payload
      );
      setNotice(`Publish: ${res.successful}/${selectedIds.length} succeeded.`);
      clearSelection();
      await fetchAll();
    } catch (e: any) {
      setError(`Publish failed: ${e?.message || e}`);
    } finally {
      setBusy((b) => ({ ...b, pub: false }));
    }
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Dashboard</h1>
          <p className="text-sm text-zinc-600">Validate, approve, and publish LinkedIn content</p>
        </div>
        <ConnectLinkedInButton />
      </div>

      {notice && <div className="rounded-xl bg-green-50 text-green-800 border border-green-200 px-4 py-3">{notice}</div>}
      {error && <div className="rounded-xl bg-red-50 text-red-800 border border-red-200 px-4 py-3">{error}</div>}

      <Card>
        <CardHeader
          title="Account"
          description="LinkedIn identity and organization context"
          actions={<ConnectLinkedInButton label="Re-connect" variant="secondary" />}
        />
        <CardContent className="grid gap-4 sm:grid-cols-2">
          <div>
            <div className="text-sm text-zinc-500">Signed in as</div>
            <div className="font-medium">{me?.name || "—"}</div>
            {me?.email ? <div className="text-sm text-zinc-600">{me.email}</div> : null}
          </div>
          <div>
            <div className="text-sm text-zinc-500">Preferred Org ID</div>
            <div className="font-medium">{me?.org_preferred || "—"}</div>
          </div>
        </CardContent>
        <CardFooter className="text-sm text-zinc-600">
          {orgs.length > 0 ? (
            <>Organizations you can manage: <span className="font-medium">{orgs.map(o => o.id).join(", ")}</span></>
          ) : (
            <>No organizations found or missing scopes.</>
          )}
        </CardFooter>
      </Card>

      <LinkedInAppSettings />

      <Card>
        <CardHeader
          title="Generate Approved Posts"
          description="Run your validation pipeline and stash approved posts for manual publishing"
          actions={<Button onClick={onGenerateApproved} isLoading={busy.gen}>Generate</Button>}
        />
        <CardContent className="text-sm text-zinc-600">
          Click <span className="font-medium">Generate</span> to run the pipeline. Approved posts will appear below.
        </CardContent>
      </Card>

      <Card>
        <CardHeader
          title="Approved Queue"
          description={approved.length ? `${approved.length} ready` : "No approved posts yet"}
          actions={
            <div className="flex items-center gap-2">
              <Button variant="outline" onClick={() => onPublish("MEMBER", false)} disabled={busy.pub || selectedIds.length === 0} isLoading={busy.pub}>Draft as Member</Button>
              <Button variant="secondary" onClick={() => onPublish("MEMBER", true)} disabled={busy.pub || selectedIds.length === 0} isLoading={busy.pub}>Publish Now (Member)</Button>
              <Button variant="outline" onClick={() => onPublish("ORG", false)} disabled={busy.pub || selectedIds.length === 0 || orgs.length === 0} isLoading={busy.pub}>Draft as Org</Button>
              <Button onClick={() => onPublish("ORG", true)} disabled={busy.pub || selectedIds.length === 0 || orgs.length === 0} isLoading={busy.pub}>Publish Now (Org)</Button>
            </div>
          }
        />
        <CardContent className="p-0">
          {approved.length === 0 ? (
            <div className="px-6 py-8 text-sm text-zinc-600">Nothing here yet.</div>
          ) : (
            <div className="divide-y divide-zinc-100">
              {approved.map((p) => (
                <label key={p.id} className="flex items-start gap-3 px-6 py-4 hover:bg-zinc-50 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={!!sel[p.id]}
                    onChange={(e) => setSel((s) => ({ ...s, [p.id]: e.target.checked }))}
                    className="mt-1 h-4 w-4"
                  />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-3">
                      <div className="font-medium truncate">
                        {p.content.slice(0, 80)}{p.content.length > 80 ? "…" : ""}
                      </div>
                      <div className="text-xs text-zinc-500">
                        {new Date(p.created_at).toLocaleString()}
                      </div>
                    </div>
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
                      Status: <span className="font-medium">{p.status}</span>
                      {p.li_post_id ? <> • LinkedIn ID: <span className="font-mono">{p.li_post_id}</span></> : null}
                      {p.error_message ? <div className="text-red-600 mt-1">{p.error_message}</div> : null}
                    </div>
                  </div>
                </label>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
