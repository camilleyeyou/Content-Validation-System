const API = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8001";

export default function Home() {
  return (
    <main style={{ padding: 24 }}>
      <h1>LinkedIn Content Portal</h1>
      <p>Authenticate to start composing posts or run the full pipeline.</p>
      <div style={{ display: "flex", gap: 12, marginTop: 12 }}>
        <a
          href={`${API}/auth/linkedin/login?include_org=true`}
          style={{ display: "inline-block", padding: "8px 12px", background: "#0A66C2", color: "#fff", borderRadius: 8 }}
        >
          Connect LinkedIn
        </a>
        <a
          href="/dashboard"
          style={{ display: "inline-block", padding: "8px 12px", background: "#111", color: "#fff", borderRadius: 8 }}
        >
          Go to Dashboard
        </a>

        <a href="/approved" style={{ display:'inline-block', padding:'8px 12px', background:'#555', color:'#fff', borderRadius:8 }}>
          View Approved
        </a>

      </div>
    </main>
  );
}
