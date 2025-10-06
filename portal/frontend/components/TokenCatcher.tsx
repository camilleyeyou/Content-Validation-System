// portal/frontend/components/TokenCatcher.tsx
"use client";

import { useEffect } from "react";

// Redundant safety if the token arrives on subsequent pages.
export default function TokenCatcher() {
  useEffect(() => {
    try {
      const url = new URL(window.location.href);
      const t = url.searchParams.get("t");
      if (t) {
        localStorage.setItem("portal_token", t);
        url.searchParams.delete("t");
        window.history.replaceState({}, "", url.toString());
      }
    } catch {}
  }, []);
  return null;
}
