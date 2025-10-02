"use client";
import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8001";

type PostRow = {
  id: string;
  target_type: "MEMBER" | "ORG";
  lifecycle: string;
  commentary: string;
  li_post_id?: string;
  error_message?: string;
};

async function fetchJSON(url: string, opts: any = {}) {
  const r = await fetch(url, { credentials: "include", ...opts });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export default function Dashboard() {
  const [me, setMe] = useState<any>(null);
  const [orgs, setOrgs] = useState<any[]>([]);
  const [commentary, setCommentary] = useState("");
  const [hashtags, setHashtags] = useState("MyBrand, Update");
  const [target, setTarget] = useState<"AUTO" | "MEMBER" | "ORG">("AUTO");
  const [orgId, setOrgId] = useState("");
  const [rows, setRows] = useState<PostRow[]>([]);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    (async () => {
      try { setMe(await fetchJSON(`${API}/api/me`)); } catch {}
      try { const d = await fetchJSON(`${API}/api/orgs`); setOrgs(d.orgs || []); } catch {}
      try { setRows(await fetchJSON(`${API}/api/posts`)); } catch {}
    })();
  }, []);

  async function publish() {
    setMsg("");
    try {
      const payload = {
        commentary,
        hashtags: hashtags.split(",").map(s => s.trim()).filter(Boolean),
        target,
        org_id: target === "ORG" ? orgId : null,
        publish_now: true
      };
      const data = await fetchJSON(`${API}/api/posts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      setMsg(`Published: ${data.lifecycle}${data.li_post_id ? ` (ID ${data.li_post_id})` : ""}`);
      setCommentary("");
      setRows(await fetchJSON(`${API}/api/posts`));
    } catch (e: any) {
      setMsg(e?.message || "Error");
    }
  }

  async function runBatch() {
    setMsg("Running batch…");
    try {
      const data = await fetchJSON(`${API}/api/run-batch`, { method: "POST" });
      setMsg(`Batch ${data.batch_id || ""}: approved ${data.approved}, published ${data.published}`);
      setRows(await fetchJSON(`${API}/api/posts`));
    } catch (e: any) {
      setMsg(e?.message || "Error");
    }
  }

  return (
    <main style={{ padding: 24, display: "grid", gap: 16 }}>
      <h1>Dashboard</h1>
      <div style={{ fontSize: 14, color: "#444" }}>
        {me ? <>Signed in as <b>{me.name || me.sub}</b></> : "Loading…"}
      </div>

      <div style={{ fontSize: 14 }}>
        <a href="/approved">Go to Approved →</a>
      </div>


      <section style={{ display: "grid", gap: 8 }}>
        <h2>Compose</h2>
        <textarea
          value={commentary}
          onChange={e => setCommentary(e.target.value)}
          placeholder="Write your post…"
          style={{ width: "100%", height: 140, padding: 12 }}
        />
        <input
          value={hashtags}
          onChange={e => setHashtags(e.target.value)}
          placeholder="Hashtags (comma)"
          style={{ padding: 8 }}
        />

        <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
          <label>Target:</label>
          <select value={target} onChange={e => setTarget(e.target.value as any)}>
            <option value="AUTO">Auto (Org if configured)</option>
            <option value="MEMBER">Personal Profile</option>
            <option value="ORG">Company Page</option>
          </select>

          {target === "ORG" && (
            <>
              <select value={orgId} onChange={e => setOrgId(e.target.value)}>
                <option value="">-- select org --</option>
                {orgs.map((o: any) => (
                  <option key={o.urn} value={o.id}>{o.id}</option>
                ))}
              </select>
              <span style={{ fontSize: 12, color: "#666" }}>
                Tip: set LINKEDIN_ORG_ID in .env to prefer this automatically
              </span>
            </>
          )}

          <button onClick={publish} style={{ padding: "8px 12px", background: "#0A66C2", color: "#fff", borderRadius: 8 }}>
            Publish
          </button>
          <button onClick={runBatch} style={{ padding: "8px 12px", background: "#111", color: "#fff", borderRadius: 8 }}>
            Run Full Batch + Publish
          </button>
        </div>

        {msg && <div style={{ fontSize: 13 }}>{msg}</div>}
      </section>

      <section>
        <h2>Recent</h2>
        <div style={{ display: "grid", gap: 8 }}>
          {rows.map((r) => (
            <div key={r.id} style={{ border: "1px solid #ddd", padding: 12 }}>
              <div style={{ fontSize: 12, color: "#666" }}>{r.target_type} • {r.lifecycle}</div>
              <div style={{ whiteSpace: "pre-wrap", marginTop: 6 }}>{r.commentary}</div>
              {r.li_post_id && <div style={{ fontSize: 12, color: "#555", marginTop: 6 }}>LinkedIn ID: {r.li_post_id}</div>}
              {r.error_message && <div style={{ fontSize: 12, color: "#B00020", marginTop: 6 }}>Error: {r.error_message}</div>}
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
