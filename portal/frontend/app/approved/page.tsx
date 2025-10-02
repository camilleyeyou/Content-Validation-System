"use client";
import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8001";

type Approved = {
  id: string;
  content: string;
  hashtags: string[];
  status: "APPROVED" | "DRAFT_CREATED" | "PUBLISHED";
  li_post_id?: string | null;
  error_message?: string | null;
  created_at: string;
};

async function fetchJSON(url: string, opts: RequestInit = {}) {
  const r = await fetch(url, { credentials: "include", ...opts });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export default function ApprovedPage() {
  const [rows, setRows] = useState<Approved[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [target, setTarget] = useState<"AUTO" | "MEMBER" | "ORG">("AUTO");
  const [orgId, setOrgId] = useState("");
  const [publishNow, setPublishNow] = useState(false);
  const [msg, setMsg] = useState("");
  const [orgs, setOrgs] = useState<any[]>([]);

  useEffect(() => {
    (async () => {
      try { setRows(await fetchJSON(`${API}/api/approved`)); } catch (e: any) { setMsg(e.message); }
      try { const d = await fetchJSON(`${API}/api/orgs`); setOrgs(d.orgs || []); } catch {}
    })();
  }, []);

  function toggle(id: string) {
    setSelected(s => (s.includes(id) ? s.filter(x => x !== id) : [...s, id]));
  }

  async function publishSelected() {
    if (selected.length === 0) { setMsg("Select at least one post"); return; }
    setMsg("Publishing…");
    try {
      const payload: any = { ids: selected, target, publish_now: publishNow };
      if (target === "ORG" && orgId) payload.org_id = orgId;

      const res = await fetchJSON(`${API}/api/approved/publish`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const ok = res.successful || 0;
      setMsg(`Published ${ok}/${selected.length} as ${publishNow ? "LIVE" : "DRAFT"}`);
      setSelected([]);
      setRows(await fetchJSON(`${API}/api/approved`));
    } catch (e: any) {
      setMsg(e?.message || "Error");
    }
  }

  return (
    <main style={{ display: "grid", gap: 16 }}>
      <h1>Approved posts</h1>

      <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
        <label>Target:</label>
        <select value={target} onChange={e => setTarget(e.target.value as any)}>
          <option value="AUTO">Auto (Org if configured)</option>
          <option value="MEMBER">Personal Profile</option>
          <option value="ORG">Company Page</option>
        </select>

        {target === "ORG" && (
          <select value={orgId} onChange={e => setOrgId(e.target.value)}>
            <option value="">-- select org --</option>
            {orgs.map((o: any) => (
              <option key={o.urn} value={o.id}>{o.id}</option>
            ))}
          </select>
        )}

        <label style={{ display: "flex", gap: 6, alignItems: "center" }}>
          <input type="checkbox" checked={publishNow} onChange={e => setPublishNow(e.target.checked)} />
          Publish as LIVE (unchecked = create drafts)
        </label>

        <button onClick={publishSelected} style={{ padding: "8px 12px", background: "#0A66C2", color: "#fff", borderRadius: 8 }}>
          Publish selected
        </button>
      </div>

      {msg && <div style={{ fontSize: 13 }}>{msg}</div>}

      <section style={{ display: "grid", gap: 12 }}>
        {rows.length === 0 && <div>No approved posts yet. Run a batch on the Dashboard.</div>}
        {rows.map(r => (
          <div key={r.id} style={{ border: "1px solid #ddd", padding: 12 }}>
            <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
              <input type="checkbox" checked={selected.includes(r.id)} onChange={() => toggle(r.id)} />
              <div style={{ fontSize: 12, color: "#666" }}>
                {r.status} • {new Date(r.created_at).toLocaleString()}
                {r.li_post_id ? ` • LI: ${r.li_post_id}` : ""}
              </div>
            </div>
            <div style={{ whiteSpace: "pre-wrap", marginTop: 6 }}>{r.content}</div>
            {r.hashtags?.length > 0 && (
              <div style={{ marginTop: 6, fontSize: 12, color: "#444" }}>
                Hashtags: {r.hashtags.join(", ")}
              </div>
            )}
            {r.error_message && (
              <div style={{ marginTop: 6, fontSize: 12, color: "#B00020" }}>
                Error: {r.error_message}
              </div>
            )}
          </div>
        ))}
      </section>
    </main>
  );
}
