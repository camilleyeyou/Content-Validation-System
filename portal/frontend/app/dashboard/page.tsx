"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { apiGet, apiPost, linkedInLoginUrl, getLoginSid } from "@/lib/config";
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
      } catch {
        // orgs may 403 if scopes missing; ignore
      }
    } catch (e: any) {
      setError(e?.message || "Failed to load");
    }
  }, []);

  React.useEffect(() => { fetchAll(); }, [fetchAll]);

  async function onGenerateApproved() {
    setBusy((b) => ({ ...b, gen: true }));
    setNotice(null);
    setError(null);
    try {
      const res = await apiPost<{ approved_count: number; batch_id?: string }>("/api/run-batch", {});
      setNotice(`Generated ${res.approved_count} approved post(s).`);
      await fetchAll();
    } catch (e: any) {
      setError(`Generate failed: ${e?.message || e}`);
    } finally {
      setBusy((b) => ({ ...b, gen: false }));
    }
  }

  async function onPublish(target: "MEMBER" | "ORG", publishNow: boolean) {
    const ids = Object.entries(sel).filter(([, v]) => v).map(([k]) => k);
    if (ids.length === 0) return;
    setBusy((b) => ({ ...b, pub: true }));
    setNotice(null);
    setError(null);
    try {
      const payload: any = { ids, target, publish_now: publishNow };
      if (target === "ORG" && orgs[0]?.id) payload.org_id = orgs[0].id;

      const res = await apiPost<{ successful: number; results: any[] }>(
        "/api/approved/publish",
        payload
      );
      setNotice(`Publish: ${res.successful}/${ids.length} succeeded.`);
      setSel({});
      await fetchAll();
    } catch (e: any) {
      setError(`Publish failed: ${e?.message || e}`);
    } finally {
      setBusy((b) => ({ ...b, pub: false }));
    }
  }

  const sid = React.useMemo(() => getLoginSid(), []);
  const linkedInHref = linkedInLoginUrl(true, sid);

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Dashboard</h1>
          <p className="text-sm text-zinc-600">Validate, approve, and publish LinkedIn content</p>
        </div>
        <div className="flex items-center gap-2">
          <a href={linkedInHref}><Button variant="outline">Connect LinkedIn</Button></a>
        </div>
      </div>

      <LinkedInAppSettings />

      {notice ? (
        <div className="rounded-xl bg-green-50 text-green-800 border border-green-200 px-4 py-3">{notice}</div>
      ) : null}
      {error ? (
        <div className="rounded-xl bg-red-50 text-red-800 border border-red-200 px-4 py-3">{error}</div>
      ) : null}

      <Card>
        <CardHeader
          title="Account"
          description="LinkedIn identity and organization context"
          actions={<a href={linkedInHref}><Button variant="secondary">Re-connect</Button></a>}
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
        <CardFooter className="flex items-center gap-2">
          {orgs.length > 0 ? (
            <div className="text-sm text-zinc-600">
              Organizations you can manage: <span className="font-medium">{orgs.map((o) => o.id).join(", ")}</span>
            </div>
          ) : (
            <div className="text-sm text-zinc-600">No organizations found or missing scopes.</div>
          )}
        </CardFooter>
      </Card>

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
    </div>
  );
}
