// portal/frontend/components/ConnectLinkedInButton.tsx
"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";
import { linkedInLoginUrl } from "@/lib/config";

interface ConnectLinkedInButtonProps {
  includeOrg?: boolean;
  variant?: "default" | "outline" | "secondary" | "ghost";
  children?: React.ReactNode;
}

export default function ConnectLinkedInButton({ 
  includeOrg = false, 
  variant = "default",
  children 
}: ConnectLinkedInButtonProps) {
  const [currentUrl, setCurrentUrl] = React.useState<string>("");

  React.useEffect(() => {
    if (typeof window !== "undefined") {
      setCurrentUrl(window.location.href);
    }
  }, []);

  const loginHref = linkedInLoginUrl(includeOrg, currentUrl || undefined);

  return (
    <a href={loginHref}>
      <Button variant={variant}>
        {children || "Connect LinkedIn"}
      </Button>
    </a>
  );
}