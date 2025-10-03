"use client";

import { useEffect, useState } from "react";

type Me = { name?: string; email?: string; sub?: string; org_preferred?: string | null };
type Org = { urn: string; id: string };
type Approved = { id: string; content: string; hashtags?: string[]; status: string };

const API = process.env.NEXT_PUBLIC_API_BASE!;

export default function Dashboard() {
  const [me, setMe] = useState<Me | null>(null);
  const [orgs, setOrgs] = useState<Org[]>([]);
  const [approved, setApproved] = useState<Approved[]>([]);
  const [commentary, setCommentary] = useState("");
  const [hashtags, setHashtags] = useState("");

  useEffect(() => {
    fetch(`${API}/api/me`, { credentials: "include" }).then(async (r) => {
      if (r.ok) setMe(await r.json());
    });
    fetch(`${API}/api/orgs`, { credentials: "include" }).then(async (r) => {
      if (r.ok) {
        const data = await r.json();
        setOrgs(data.orgs || []);
      }
    });
    fetch(`${API}/api/approved`, { credentials: "include" }).then(async (r) => {
      if (r.ok) setApproved(await r.json());
    });
  }, []);

  async function runBatch() {
    await fetch(`${API}/api/run-batch`, { method: "POST", credentials: "include" });
    const res = await fetch(`${API}/api/approved`, { credentials: "include" });
    if (res.ok) setApproved(await res.json());
  }

  async function publishSelected(ids: string[], target: "MEMBER" | "ORG") {
    await fetch(`${API}/api/approved/publish`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ids,
        target,
        publish_now: true,
        org_id: target === "ORG" ? me?.org_preferred : undefined,
      }),
    });
  }

  async function createPost(target: "MEMBER" | "ORG") {
    await fetch(`${API}/api/posts`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        commentary,
        hashtags: hashtags
          .split(",")
          .map((t) => t.trim())
          .filter(Boolean),
        target,
        publish_now: true,
      }),
    });
    setCommentary("");
    setHashtags("");
  }

  return (
    <main className="container py-10 space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Dashboard</h1>
          <p className="text-zinc-600 text-sm">
            {me ? `Signed in as ${me.name || me.email}` : "Not signed in. Click Connect on the homepage."}
          </p>
        </div>
        <a
          className="btn-primary"
          href={process.env.NEXT_PUBLIC_API_BASE + "/auth/linkedin/login?include_org=true"}
        >
          {me ? "Re-connect LinkedIn" : "Connect LinkedIn"}
        </a>
      </div>

      <section className="grid gap-6 md:grid-cols-3">
        <div className="card md:col-span-2">
          <h2 className="font-semibold">Quick Post</h2>
          <div className="mt-4 space-y-3">
            <textarea
              value={commentary}
              onChange={(e) => setCommentary(e.target.value)}
              className="input h-32 resize-none"
              placeholder="Write something human and premium…"
            />
            <input
              value={hashtags}
              onChange={(e) => setHashtags(e.target.value)}
              className="input"
              placeholder="Comma-separated hashtags e.g. HumanFirst, LinkedInLife"
            />
            <div className="flex gap-2">
              <button className="btn-ghost" onClick={() => createPost("MEMBER")}>Post to Profile</button>
              <button className="btn-primary" onClick={() => createPost("ORG")}>Post to Company Page</button>
            </div>
          </div>
        </div>

        <div className="card">
          <h2 className="font-semibold">Your Pages</h2>
          <div className="mt-3 space-y-2">
            {orgs.length === 0 && <p className="text-sm text-zinc-600">None detected (or missing org scopes).</p>}
            {orgs.map((o) => (
              <div key={o.id} className="flex items-center justify-between rounded-xl border border-zinc-200 p-3">
                <div className="text-sm">
                  <div className="font-medium">Org ID: {o.id}</div>
                  <div className="text-zinc-600">{o.urn}</div>
                </div>
                <span className="tag">ADMIN</span>
              </div>
            ))}
          </div>
          <button className="btn-ghost w-full mt-4" onClick={runBatch}>
            Generate Approved Posts
          </button>
        </div>
      </section>

      <section className="card">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold">Approved Queue</h2>
          <div className="space-x-2">
            <button
              className="btn-ghost"
              onClick={() => publishSelected(approved.map((a) => a.id), "MEMBER")}
            >
              Publish All → Profile
            </button>
            <button
              className="btn-primary"
              onClick={() => publishSelected(approved.map((a) => a.id), "ORG")}
            >
              Publish All → Company
            </button>
          </div>
        </div>

        <div className="mt-4 grid gap-4">
          {approved.length === 0 && <p className="text-sm text-zinc-600">No approved posts yet.</p>}
          {approved.map((a) => (
            <div key={a.id} className="rounded-2xl border border-zinc-200 p-4">
              <div className="flex items-center justify-between">
                <div className="text-xs text-zinc-600">{a.id}</div>
                <span className="tag">{a.status}</span>
              </div>
              <p className="mt-3 whitespace-pre-wrap">{a.content}</p>
              {a.hashtags?.length ? (
                <div className="mt-3 flex flex-wrap gap-2">
                  {a.hashtags.map((t) => (
                    <span key={t} className="tag">#{t}</span>
                  ))}
                </div>
              ) : null}
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
