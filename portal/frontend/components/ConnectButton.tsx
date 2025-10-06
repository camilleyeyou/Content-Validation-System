// portal/frontend/app/components/ConnectButton.tsx
"use client";

import { API_BASE } from "@/lib/config";

export default function ConnectButton() {
  const href = `${API_BASE}/auth/linkedin/login?include_org=true`;

  return (
    <a
      href={href}
      className="inline-flex items-center rounded-lg bg-black px-4 py-2 text-white hover:bg-zinc-800"
    >
      Connect LinkedIn
    </a>
  );
}
