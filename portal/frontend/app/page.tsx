// portal/frontend/app/page.tsx
// import { redirect } from "next/navigation";
// 
// export default function Home() {
//   redirect("/dashboard");
// }
// portal/frontend/app/page.tsx
"use client";

import * as React from "react";
import { API_BASE, apiGet, apiPost, fetchApproved, ApprovedRec } from "@/lib/config";

export default function Home() {
  const [approved, setApproved] = React.useState<ApprovedRec[]>([]);
  const [topic, setTopic] = React.useState("");
  const [count, setCount] = React.useState(3);
  const [busy, setBusy] = React.useState(false);
  const [notice, setNotice] = React.useState<string | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  const load = React.useCallback(async () => {
    setError(null);
    try {
      const list = await fetchApproved();
      setApproved(list);
    } catch (e: any) {
      setError(e?.message || "Failed to load");
    }
  }, []);

  React.useEffect(() => {
    load();
  }, [load]);

  async function onGenerate() {
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      await apiPost("/api/run-batch", { topic: topic || undefined, count });
      setNotice("Generated new posts.");
      await load();
    } catch (e: any) {
      setError(e?.message || "Generate failed");
    } finally {
      setBusy(false);
    }
  }

  async function onClear() {
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      await apiPost("/api/approved/clear", {});
      setNotice("Cleared queue.");
      setApproved([]);
    } catch (e: any) {
      setError(e?.message || "Clear failed");
    } finally {
      setBusy(false);
    }
  }

  function copy(text: string) {
    navigator.clipboard.writeText(text).catch(() => {});
  }

  function formatPost(p: ApprovedRec) {
    const tags = p.hashtags?.length ? " " + p.hashtags.map(h => `#${h.replace(/^#/, "")}`).join(" ") : "";
    return `${p.content}${tags}`;
  }

  async function onExportTxt() {
    const blob = new Blob(
      approved.map(p => formatPost(p)).join("\n\n---\n\n").split("\n").join("\r\n") ? 
      [approved.map(p => formatPost(p)).join("\n\n---\n\n")] : [""],
      { type: "text/plain;charset=utf-8" }
    );
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.download = "posts.txt";
    a.href = url;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Publishing Dashboard</h1>
          <p className="text-sm text-zinc-600">Generate posts and copy/paste to LinkedIn.</p>
        </div>
        <a
          className="text-xs text-zinc-500"
          href={`${API_BASE}/api/health`}
          target="_blank"
          rel="noreferrer"
        >
          API health →
        </a>
      </header>

      {notice && (
        <div className="rounded-xl bg-green-50 text-green-800 border border-green-200 px-4 py-3">
          {notice}
        </div>
      )}
      {error && (
        <div className="rounded-xl bg-red-50 text-red-800 border border-red-200 px-4 py-3">
          {error}
        </div>
      )}

      {/* Generator */}
      <div className="rounded-2xl border p-4 space-y-3">
        <div className="font-semibold">Generate Posts</div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <div className="md:col-span-3">
            <label className="block text-sm mb-1">Topic (optional)</label>
            <input
              className="w-full px-3 py-2 border rounded-md text-sm"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="e.g., content workflow, launch announcement, hiring..."
            />
          </div>
          <div>
            <label className="block text-sm mb-1">Count</label>
            <input
              type="number"
              min={1}
              max={20}
              className="w-full px-3 py-2 border rounded-md text-sm"
              value={count}
              onChange={(e) => setCount(Math.max(1, Math.min(20, Number(e.target.value) || 1)))}
            />
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={onGenerate}
            disabled={busy}
            className="px-4 py-2 rounded-md bg-black text-white disabled:opacity-60"
          >
            {busy ? "Working…" : "Generate"}
          </button>
          <button
            onClick={onExportTxt}
            disabled={!approved.length}
            className="px-3 py-2 rounded-md border"
          >
            Export .txt
          </button>
          <button
            onClick={onClear}
            disabled={busy || !approved.length}
            className="px-3 py-2 rounded-md border"
          >
            Clear queue
          </button>
        </div>
        <p className="text-xs text-zinc-500">
          Backend tries <span className="font-mono">GEN_API_URL</span> → OpenAI (<span className="font-mono">OPENAI_API_KEY</span>) → fallback samples.
        </p>
      </div>

      {/* Queue */}
      <div className="rounded-2xl border overflow-hidden">
        <div className="px-4 py-3 border-b flex items-center justify-between">
          <div className="font-semibold">Global Queue</div>
          <div className="text-sm text-zinc-600">{approved.length} item{approved.length === 1 ? "" : "s"}</div>
        </div>

        {approved.length === 0 ? (
          <div className="p-6 text-sm text-zinc-600">Nothing yet. Generate a few posts above.</div>
        ) : (
          <div className="divide-y">
            {approved.map((p) => {
              const merged = formatPost(p);
              return (
                <div key={p.id} className="p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0 flex-1">
                      <div className="font-medium mb-2">{new Date(p.created_at).toLocaleString()}</div>
                      <p className="whitespace-pre-wrap">{p.content}</p>
                      {p.hashtags?.length > 0 && (
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
                      )}
                    </div>
                    <div className="shrink-0 flex flex-col gap-2">
                      <button
                        className="px-3 py-1.5 text-sm rounded-md border"
                        onClick={() => copy(p.content)}
                      >
                        Copy text
                      </button>
                      <button
                        className="px-3 py-1.5 text-sm rounded-md border"
                        onClick={() => copy(merged)}
                      >
                        Copy post + tags
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
