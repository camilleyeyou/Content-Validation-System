// portal/frontend/app/components/ConnectLinkedInButton.tsx
"use client";

export default function ConnectLinkedInButton() {
  const href = `${process.env.NEXT_PUBLIC_API_BASE}/auth/linkedin/login?include_org=true`;
  // IMPORTANT: this must be an absolute URL to your API; avoid "//auth/..."
  return (
    <a
      href={href}
      className="inline-flex items-center rounded-lg bg-black px-4 py-2 text-white hover:bg-zinc-800"
    >
      Connect LinkedIn
    </a>
  );
}
