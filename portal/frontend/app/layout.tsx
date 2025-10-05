import "./globals.css";
import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "LinkedIn Content Portal",
  description: "Validate, approve and publish LinkedIn content",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="font-sans">
        <div className="mx-auto max-w-6xl px-4">
          <header className="flex items-center justify-between py-5">
            <Link href="/" className="text-lg font-semibold tracking-tight">
              Content Portal
            </Link>

            <nav className="flex items-center gap-4 text-sm">
              <Link href="/dashboard" className="rounded-lg px-3 py-2 hover:bg-neutral-100">
                Dashboard
              </Link>
              <Link href="/approved" className="rounded-lg px-3 py-2 hover:bg-neutral-100">
                Approved
              </Link>
              <a
                className="rounded-xl bg-black px-4 py-2 text-sm font-medium text-white hover:bg-neutral-800"
                href={`${process.env.NEXT_PUBLIC_PORTAL_BACKEND_LOGIN ?? "http://localhost:8001/auth/linkedin/login?include_org=true"}`}
              >
                Connect LinkedIn
              </a>
            </nav>
          </header>

          {children}
        </div>
      </body>
    </html>
  );
}
