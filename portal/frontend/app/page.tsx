// portal/frontend/app/page.tsx
const API = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8001";

export default function Home() {
  return (
    <main style={{ display: "grid", gap: 12 }}>
      <h1>LinkedIn Content Portal</h1>
      <p>Authenticate with LinkedIn, generate content, and publish to your profile or company page.</p>
      <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
        <a
          href={`${API}/auth/linkedin/login?include_org=true`}
          style={{ display: "inline-block", padding: "10px 14px", background: "#0A66C2", color: "#fff", borderRadius: 8 }}
        >
          Connect LinkedIn
        </a>
        <a
          href="/dashboard"
          style={{ display: "inline-block", padding: "10px 14px", background: "#111", color: "#fff", borderRadius: 8 }}
        >
          Go to Dashboard
        </a>
        <a
          href="/approved"
          style={{ display: "inline-block", padding: "10px 14px", background: "#555", color: "#fff", borderRadius: 8 }}
        >
          View Approved
        </a>
      </div>
    </main>
  );
}
