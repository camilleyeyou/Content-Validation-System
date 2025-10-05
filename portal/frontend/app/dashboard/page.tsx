"use client";

import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Check, Rocket, AlertTriangle } from "lucide-react";

type Me = { sub: string; name: string; email?: string | null; org_preferred?: string | null };
type Org = { id: string; urn: string };
type Approved = { id: string; content: string; hashtags: string[]; created_at: string }[];

export default function Dashboard() {
  const [me, setMe] = useState<Me | null>(null);
  const [orgs, setOrgs] = useState<Org[]>([]);
  const [approved, setApproved] = useState<Approved>([]);
  const [loadingBatch, setLoadingBatch] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ok, setOk] = useState<string | null>(null);

  async function refreshAll() {
    setError(null);
    try {
      const [meRes, orgsRes, apprRes] = await Promise.all([
        api<Me>("/api/me"),
        api<{ orgs: Org[] }>("/api/orgs"),
        api<Approved>("/api/approved"),
      ]);
      setMe(meRes);
      setOrgs(orgsRes.orgs ?? []);
      setApproved(apprRes ?? []);
    } catch (err: any) {
      setError(err?.message ?? "Failed to load data");
    }
  }

  useEffect(() => {
    refreshAll();
  }, []);

  async function runBatch() {
    setLoadingBatch(true);
    setError(null);
    setOk(null);
    try {
      const res = await api<{ approved_count: number; batch_id?: string }>("/api/run-batch", {
        method: "POST",
      });
      setOk(`Generated ${res.approved_count} approved posts${res.batch_id ? ` (batch ${res.batch_id.slice(0,8)})` : ""}.`);
      await refreshAll();
    } catch (err: any) {
      setError(err?.message ?? "Failed to run batch");
    } finally {
      setLoadingBatch(false);
    }
  }

  return (
    <main className="grid gap-6 py-8 md:grid-cols-2">
      <Card className="md:col-span-2">
        <CardHeader className="flex items-center justify-between md:flex-row md:items-center">
          <CardTitle>Dashboard</CardTitle>
          <div className="flex items-center gap-2">
            <Button onClick={runBatch} loading={loadingBatch} className="min-w-48">
              <Rocket className="mr-2 h-4 w-4" /> Generate Approved Posts
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {!me && (
            <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4" />
                <span>You’re not connected. Click “Connect LinkedIn” in the header, then return here.</span>
              </div>
            </div>
          )}

          {me && (
            <div className="grid gap-4 md:grid-cols-3">
              <div className="rounded-xl border border-neutral-200 bg-white p-4">
                <div className="text-xs text-neutral-500">Signed in as</div>
                <div className="mt-1 text-sm font-medium">{me.name}</div>
                <div className="text-xs text-neutral-500">{me.email ?? ""}</div>
              </div>

              <div className="rounded-xl border border-neutral-200 bg-white p-4">
                <div className="text-xs text-neutral-500">Organizations</div>
                <div className="mt-1 text-sm">
                  {orgs.length ? (
                    <div className="flex flex-wrap gap-2">
                      {orgs.map((o) => (
                        <span
                          key={o.id}
                          className="inline-flex items-center rounded-full bg-neutral-100 px-3 py-1 text-xs"
                          title={o.urn}
                        >
                          {o.id}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <span className="text-neutral-500">None detected or missing scopes</span>
                  )}
                </div>
              </div>

              <div className="rounded-xl border border-neutral-200 bg-white p-4">
                <div className="text-xs text-neutral-500">Approved queue</div>
                <div className="mt-1 text-2xl font-semibold">{approved.length}</div>
                <div className="text-xs text-neutral-500">ready to publish</div>
              </div>
            </div>
          )}

          {ok && (
            <div className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900">
              <div className="flex items-center gap-2">
                <Check className="h-4 w-4" />
                <span>{ok}</span>
              </div>
            </div>
          )}

          {error && (
            <div className="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-900">
              {error}
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="md:col-span-2">
        <CardHeader>
          <CardTitle>Latest Approved</CardTitle>
        </CardHeader>
        <CardContent>
          {!approved.length && (
            <div className="text-sm text-neutral-500">No approved posts yet. Click “Generate Approved Posts”.</div>
          )}
          <ul className="grid gap-4">
            {approved.slice(0, 6).map((p) => (
              <li key={p.id} className="rounded-xl border border-neutral-200 bg-white p-4">
                <div className="text-sm whitespace-pre-wrap">{p.content}</div>
                {!!p.hashtags?.length && (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {p.hashtags.map((h, i) => (
                      <span key={i} className="rounded-full bg-neutral-100 px-3 py-1 text-xs">
                        #{h.replace(/^#/, "")}
                      </span>
                    ))}
                  </div>
                )}
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </main>
  );
}
