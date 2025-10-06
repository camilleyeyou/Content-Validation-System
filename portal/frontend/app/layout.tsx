// portal/frontend/app/layout.tsx
import "./globals.css";
import type { Metadata } from "next";
import Header from "@/components/Header";
import TokenSync from "@/components/TokenSync";

export const metadata: Metadata = {
  title: "LinkedIn Content Portal",
  description: "Validate, approve and publish LinkedIn content",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ fontFamily: "system-ui, -apple-system, Segoe UI, Roboto, sans-serif" }}>
        <TokenSync />
        <Header />
        <div className="mx-auto max-w-5xl p-4">{children}</div>
      </body>
    </html>
  );
}
