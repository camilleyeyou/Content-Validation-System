// portal/frontend/components/Header.tsx
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { linkedInLoginUrl } from "@/lib/config";
import { Button } from "@/components/ui/button";

function NavLink({
  href,
  children,
}: {
  href: string;
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const active =
    pathname === href || (href !== "/" && pathname?.startsWith(href));
  return (
    <Link
      href={href}
      className={`text-sm font-medium transition hover:text-zinc-900 ${
        active ? "text-zinc-900" : "text-zinc-600"
      }`}
    >
      {children}
    </Link>
  );
}

export default function Header() {
  return (
    <header className="sticky top-0 z-30 bg-white/80 backdrop-blur supports-[backdrop-filter]:bg-white/60 border-b border-zinc-100">
      <div className="mx-auto max-w-5xl px-4 h-14 flex items-center justify-between">
        <nav className="flex items-center gap-6">
          <NavLink href="/">Home</NavLink>
          <NavLink href="/dashboard">Dashboard</NavLink>
          <NavLink href="/approved">Approved</NavLink>
        </nav>
        <div className="flex items-center gap-3">
          <a href={linkedInLoginUrl(true)}>
            <Button variant="outline">Connect LinkedIn</Button>
          </a>
        </div>
      </div>
    </header>
  );
}
