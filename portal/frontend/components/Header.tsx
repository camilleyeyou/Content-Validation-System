// portal/frontend/components/Header.tsx
"use client";

import Link from "next/link";
import { linkedInLoginUrl } from "@/lib/config";
import { Button } from "@/components/ui/button";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

export default function Header() {
  const pathname = usePathname();
  const nav = [
    { href: "/", label: "Home" },
    { href: "/dashboard", label: "Dashboard" },
    { href: "/approved", label: "Approved" },
  ];

  return (
    <header className="sticky top-0 z-30 bg-white/80 backdrop-blur supports-[backdrop-filter]:bg-white/60 border-b border-zinc-100">
      <div className="mx-auto max-w-5xl px-4 h-14 flex items-center justify-between">
        <nav className="flex items-center gap-6">
          <Link href="/" className="font-semibold">
            Content Portal
          </Link>
          {nav.map((n) => (
            <Link
              key={n.href}
              href={n.href}
              className={cn(
                "text-sm text-zinc-600 hover:text-zinc-900",
                pathname === n.href && "text-zinc-900 font-medium"
              )}
            >
              {n.label}
            </Link>
          ))}
        </nav>
        <a href={linkedInLoginUrl(true)}>
          <Button variant="outline">Connect LinkedIn</Button>
        </a>
      </div>
    </header>
  );
}
