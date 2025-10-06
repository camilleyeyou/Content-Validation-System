// portal/frontend/components/ConnectLinkedInButton.tsx
"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";
import { linkedInLoginUrl } from "@/lib/config";

export default function ConnectLinkedInButton({
  includeOrg = true,
  variant = "outline",
  children,
  className,
}: {
  includeOrg?: boolean;
  variant?: "default" | "secondary" | "outline" | "ghost";
  children?: React.ReactNode;
  className?: string;
}) {
  const href = linkedInLoginUrl(includeOrg);
  return (
    <a href={href} className={className}>
      <Button variant={variant}>{children ?? "Connect LinkedIn"}</Button>
    </a>
  );
}
