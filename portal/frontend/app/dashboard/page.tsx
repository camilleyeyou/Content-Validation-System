"use client";
import { useEffect, useState } from "react";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE?.replace(/\/$/, "") || "http://localhost:8001";

type PostRow = {
  id: string;
  target_type: "MEMBER" | "ORG";
  lifecycle: string;
  commentary: string;
  hashtags?: string[];
  li_post_id?: string;
  error_message?: string;
  created_at?: string;
};

export default function Dashboard() {
  const [me, setMe] = useState<any>(null);
  const [orgs, setOrgs] = useState<any[]>([]);
  const [commentary, setCommentary] = useState("");
  const [hashtags, setHashtags] = useState("MyBrand, Update");
  const [target, setTarget] = useState<"AUTO" | "MEMBER" | "ORG">("AUTO");
  const [orgId, setOrgId] = useState("");
  const [rows, setRows] = useState<PostRow[]>([]);
  const [msg, setMsg] = useState("");

  async function fetchJSON(url: string, opts: any = {}) {
    const r = await fetch(url, { ...opts });
    const text = await r.text();
    if (!r.ok) throw new Error(text || `${r.status} ${r.statusText}`);
    try {
      return JSON.parse(text);
    } catch {
      return text;
    }
  }

  async function loadMe() {
    try {
      setMe(await fetchJSON(`${API_BASE}/api/me`));
    } catch {}
  }
  async function loadOrgs() {
    try {
      const data = await fetchJSON(`${API_BASE}/api/orgs`);
      setOrgs(data.orgs || []);
    } catch {}
  }
  async function loadPosts() {
    try {
      setRows(await fetchJSON(`${API_BASE}/api/posts`));
    } catch {}
  }

  useEffect(() => {
    loadMe();
    loadOrgs();
    loadPosts();
  }, []);

  async function publish() {
    setMsg("");
    try {
      const payload = {
        commentary,
        hashtags: hashtags.split(",").map((s) => s.trim()).filter(Boolean),
        target,
        org_id: target === "ORG" ? orgId : null,
        publish_now: true, // local publish (no LinkedIn)
      };
      const data = await fetchJSON(`${API_BASE}/api/posts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      setMsg(`Saved locally as ${data.lifecycle}`);
      setCommentary("");
      await loadPosts();
    } catch (e: any) {
      setMsg(e?.message || "Error");
    }
  }

  async function runBatch() {
    setMsg("Running full system…");
    try {
      const data = await fetchJSON(`${API_BASE}/api/run-batch`, { method: "POST" });
      setMsg(`Batch ${data.batch_id || ""}: approved ${data.approved}, added ${data.added}`);
      await loadPosts();
    } catch (e: any) {
      setMsg(e?.message || "Error");
    }
  }

  async function clearAll() {
    setMsg("");
    try {
      const data = await fetchJSON(`${API_BASE}/api/approved/clear`, { method: "POST" });
      setMsg(`Cleared ${data.deleted} items`);
      await loadPosts();
    } catch (e: any) {
      setMsg(e?.message || "Error");
    }
  }

  const subline = me ? (
    <>
      Acting as <b>{me.name || me.sub}</b>
      {orgs.length > 0 ? (
        <span style={{ color: "#666" }}> • Org ready: {orgs.map((o) => o.id).join(", ")}</span>
      ) : null}
    </>
  ) : (
    "Loading…"
  );

  return (
    <main style={{ padding: 24, display: "grid", gap: 16, maxWidth: 900, margin: "0 auto" }}>
      <h1>Dashboard</h1>
      <div style={{ fontSize: 14, color: "#444" }}>{subline}</div>

      <section style={{ display: "grid", gap: 8 }}>
        <h2>Compose</h2>
        <textarea
          value={commentary}
          onChange={(e) => setCommentary(e.target.value)}
          placeholder="Write your post…"
          style={{ width: "100%", height: 140, padding: 12 }}
        />
        <input
          value={hashtags}
          onChange={(e) => setHashtags(e.target.value)}
          placeholder="Hashtags (comma)"
          style={{ padding: 8 }}
        />

        <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
          <label>Target:</label>
          <select value={target} onChange={(e) => setTarget(e.target.value as any)}>
            <option value="AUTO">Auto (Org if configured)</option>
            <option value="MEMBER">Personal</option>
            <option value="ORG">Company</option>
          </select>

          {target === "ORG" && (
            <>
              <select value={orgId} onChange={(e) => setOrgId(e.target.value)}>
                <option value="">-- select org --</option>
                {orgs.map((o: any) => (
                  <option key={o.urn} value={o.id}>
                    {o.id}
                  </option>
                ))}
              </select>
              <span style={{ fontSize: 12, color: "#666" }}>
                (or set LINKEDIN_ORG_ID in backend env)
              </span>
            </>
          )}

          <button
            onClick={publish}
            style={{ padding: "8px 12px", background: "#111", color: "#fff", borderRadius: 8 }}
          >
            Save
          </button>
          <button
            onClick={runBatch}
            style={{ padding: "8px 12px", background: "#0A66C2", color: "#fff", borderRadius: 8 }}
          >
            Generate (run full system)
          </button>
          <button onClick={clearAll} style={{ padding: "8px 12px", borderRadius: 8 }}>
            Clear queue
          </button>
        </div>

        {msg && <div style={{ fontSize: 13 }}>{msg}</div>}
      </section>

      <section>
        <h2>Recent</h2>
        <div style={{ display: "grid", gap: 8 }}>
          {rows.map((r) => {
            const full =
              r.commentary +
              (r.hashtags?.length ? "\n\n" + r.hashtags.map((h) => `#${h}`).join(" ") : "");
            return (
              <div key={r.id} style={{ border: "1px solid #ddd", padding: 12 }}>
                <div style={{ fontSize: 12, color: "#666" }}>
                  {r.target_type} • {r.lifecycle} •{" "}
                  {r.created_at ? new Date(r.created_at).toLocaleString() : ""}
                </div>
                <div style={{ whiteSpace: "pre-wrap", marginTop: 6 }}>{r.commentary}</div>
                {r.hashtags?.length ? (
                  <div style={{ marginTop: 6, display: "flex", gap: 6, flexWrap: "wrap" }}>
                    {r.hashtags.map((h, i) => (
                      <span
                        key={i}
                        style={{
                          fontSize: 12,
                          background: "#f2f2f2",
                          padding: "2px 6px",
                          borderRadius: 999,
                        }}
                      >
                        #{h}
                      </span>
                    ))}
                  </div>
                ) : null}
                {r.li_post_id && (
                  <div style={{ fontSize: 12, color: "#555", marginTop: 6 }}>
                    LinkedIn ID: {r.li_post_id}
                  </div>
                )}
                {r.error_message && (
                  <div style={{ fontSize: 12, color: "#B00020", marginTop: 6 }}>
                    Error: {r.error_message}
                  </div>
                )}
                <div style={{ marginTop: 8 }}>
                  <button
                    onClick={() => navigator.clipboard.writeText(r.commentary)}
                    style={{ padding: "6px 10px", borderRadius: 6, marginRight: 8 }}
                  >
                    Copy text
                  </button>
                  <button
                    onClick={() => navigator.clipboard.writeText(full)}
                    style={{ padding: "6px 10px", borderRadius: 6 }}
                  >
                    Copy post + tags
                  </button>
                </div>

                <div style={{ display: "flex", gap: 16, marginTop: 16 }}>
                  <a href="/prompts" style={{ color: "#0A66C2", fontWeight: 600 }}>
                    📝 Manage Agent Prompts
                  </a>
                </div>
              </div>
            );
          })}
          {rows.length === 0 && <div style={{ color: "#666" }}>Nothing yet. Click Generate.</div>}
        </div>
      </section>
    </main>
  );
}
