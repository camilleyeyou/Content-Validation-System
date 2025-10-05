// app/components/ConnectButton.tsx
"use client";

export default function ConnectButton() {
  const apiBase = process.env.NEXT_PUBLIC_API_BASE!;
  const href = `${apiBase}/auth/linkedin/login?include_org=true`;

  return (
    <a
      href={href}
      className="inline-flex items-center rounded-lg bg-black px-4 py-2 text-white hover:bg-zinc-800"
    >
      Connect LinkedIn
    </a>
  );
}
