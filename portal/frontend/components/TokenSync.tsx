// portal/frontend/components/TokenSync.tsx
"use client";

import { useEffect } from "react";

/**
 * Cleans OAuth query params (code/state/app_session) from the URL
 * after the backend has already set the session cookie.
 */
export default function TokenSync() {
  useEffect(() => {
    if (typeof window === "undefined") return;

    const url = new URL(window.location.href);
    const params = url.searchParams;
    const hadOauthParams =
      params.has("code") || params.has("state") || params.has("app_session");

    if (hadOauthParams) {
      // Remove all query params to keep the URL pretty post-login
      window.history.replaceState({}, "", url.pathname);
    }
  }, []);

  return null;
}
