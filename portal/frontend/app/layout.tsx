// portal/frontend/app/layout.tsx
export const metadata = {
  title: "LinkedIn Content Portal",
  description: "Validate, approve and publish LinkedIn content",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ fontFamily: "system-ui, -apple-system, Segoe UI, Roboto, sans-serif" }}>
        <div style={{ maxWidth: 980, margin: "0 auto", padding: 16 }}>
          <header style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
            <a href="/" style={{ fontWeight: 700, fontSize: 18 }}>Content Portal</a>
            <nav style={{ display: "flex", gap: 12 }}>
              <a href="/dashboard">Dashboard</a>
              <a href="/approved">Approved</a>
            </nav>
          </header>
          {children}
        </div>
      </body>
    </html>
  );
}
