"use client";

import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Check, Send } from "lucide-react";

type ApprovedItem = {
  id: string;
  content: string;
  hashtags: string[];
  created_at: string;
};

type PublishPayload = {
  ids: string[];
  target: "AUTO" | "MEMBER" | "ORG";
  org_id?: string;
  publish_now: boolean;
};

export default function ApprovedPage() {
  const [items, setItems] = useState<ApprovedItem[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [target, setTarget] = useState<"AUTO" | "MEMBER" | "ORG">("AUTO");
  const [publishNow, setPublishNow] = useState(false);
  const [orgId, setOrgId] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [ok, setOk] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    setError(null);
    try {
      const res = await api<ApprovedItem[]>("/api/approved");
      setItems(res ?? []);
    } catch (e: any) {
      setError(e?.message ?? "Failed to load approved");
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  function toggle(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  async function publish() {
    if (!selected.size) return;
    setLoading(true);
    setError(null);
    setOk(null);

    const payload: PublishPayload = {
      ids: Array.from(selected),
      target,
      org_id: target === "ORG" && orgId ? orgId : undefined,
      publish_now: publishNow,
    };

    try {
      const res = await api<{ successful: number; requested: number; results: any[] }>(
        "/api/approved/publish",
        {
          method: "POST",
          body: JSON.stringify(payload),
        }
      );
      setOk(`Published ${res.successful}/${res.requested} selections.`);
      setSelected(new Set());
      await refresh();
    } catch (e: any) {
      setError(e?.message ?? "Failed to publish");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="grid gap-6 py-8">
      <Card>
        <CardHeader className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <CardTitle>Approved Queue</CardTitle>
            <p className="mt-1 text-sm text-neutral-600">Select posts to publish to LinkedIn.</p>
          </div>

          <div className="grid gap-2 md:grid-cols-4">
            <select
              value={target}
              onChange={(e) => setTarget(e.target.value as any)}
              className="h-10 rounded-xl border border-neutral-300 bg-white px-3 text-sm"
            >
              <option value="AUTO">Auto (ORG if configured else MEMBER)</option>
              <option value="MEMBER">Member Profile</option>
              <option value="ORG">Organization Page</option>
            </select>

            <input
              placeholder="Org ID (if target = ORG)"
              className="h-10 rounded-xl border border-neutral-300 bg-white px-3 text-sm"
              value={orgId}
              onChange={(e) => setOrgId(e.target.value)}
              disabled={target !== "ORG"}
            />

            <label className="flex h-10 items-center justify-center gap-2 rounded-xl border border-neutral-300 bg-white px-3 text-sm">
              <input
                type="checkbox"
                checked={publishNow}
                onChange={(e) => setPublishNow(e.target.checked)}
              />
              Publish live (otherwise drafts)
            </label>

            <Button onClick={publish} loading={loading} disabled={!selected.size}>
              <Send className="mr-2 h-4 w-4" />
              Publish Selected ({selected.size})
            </Button>
          </div>
        </CardHeader>

        <CardContent>
          {ok && (
            <div className="mb-4 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900">
              <div className="flex items-center gap-2">
                <Check className="h-4 w-4" />
                <span>{ok}</span>
              </div>
            </div>
          )}
          {error && (
            <div className="mb-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-900">
              {error}
            </div>
          )}

          {!items.length ? (
            <div className="text-sm text-neutral-500">Nothing in the queue yet.</div>
          ) : (
            <ul className="grid gap-4">
              {items.map((it) => (
                <li
                  key={it.id}
                  className="flex gap-4 rounded-xl border border-neutral-200 bg-white p-4"
                >
                  <input
                    type="checkbox"
                    className="mt-1 h-5 w-5"
                    checked={selected.has(it.id)}
                    onChange={() => toggle(it.id)}
                  />
                  <div className="flex-1">
                    <div className="text-sm whitespace-pre-wrap">{it.content}</div>
                    {!!it.hashtags?.length && (
                      <div className="mt-2 flex flex-wrap gap-2">
                        {it.hashtags.map((h, i) => (
                          <span key={i} className="rounded-full bg-neutral-100 px-3 py-1 text-xs">
                            #{h.replace(/^#/, "")}
                          </span>
                        ))}
                      </div>
                    )}
                    <div className="mt-2 text-xs text-neutral-500">
                      Added {new Date(it.created_at).toLocaleString()}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </main>
  );
}
