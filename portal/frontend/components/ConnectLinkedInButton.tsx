"use client";

import { linkedInLoginUrl } from "@/lib/config";
import { Button } from "@/components/ui/button";

export default function ConnectLinkedInButton({
  label = "Connect LinkedIn",
  includeOrg = true,
  variant = "outline",
}: {
  label?: string;
  includeOrg?: boolean;
  variant?: "default" | "secondary" | "outline" | "ghost";
}) {
  const href = linkedInLoginUrl(includeOrg);
  return (
    <a href={href}>
      <Button variant={variant}>{label}</Button>
    </a>
  );
}
