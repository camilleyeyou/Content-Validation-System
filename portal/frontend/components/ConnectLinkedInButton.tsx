"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";
import { API_BASE, linkedInLoginUrl } from "@/lib/config";

type Props = {
  includeOrg?: boolean;
  variant?: React.ComponentProps<typeof Button>["variant"];
  className?: string;
  children?: React.ReactNode;
};

export default function ConnectLinkedInButton({
  includeOrg = true,
  variant,
  className,
  children,
}: Props) {
  const [href, setHref] = React.useState<string>(linkedInLoginUrl(includeOrg));

  React.useEffect(() => {
    if (typeof window === "undefined") return;
    const redirect = window.location.href; // send them back to where they clicked
    const url = new URL(`${API_BASE}/auth/linkedin/login`);
    if (includeOrg) url.searchParams.set("include_org", "true");
    url.searchParams.set("redirect", redirect);
    setHref(url.toString());
  }, [includeOrg]);

  return (
    <a href={href}>
      <Button variant={variant} className={className}>
        {children ?? "Connect LinkedIn"}
      </Button>
    </a>
  );
}
