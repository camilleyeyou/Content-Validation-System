// portal/frontend/components/TokenSync.tsx
"use client";

import { useEffect } from "react";
import { syncTokenFromUrl } from "@/lib/config";

/**
 * Mount this once (e.g., in layout) to clean up any stray query tokens
 * after OAuth redirects. It’s harmless if nothing is present.
 */
export default function TokenSync() {
  useEffect(() => {
    try {
      syncTokenFromUrl();
    } catch {
      // ignore
    }
  }, []);
  return null;
}
