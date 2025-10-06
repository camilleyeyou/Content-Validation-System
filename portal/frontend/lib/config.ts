// portal/frontend/app/lib/config.ts
// One source of truth for the backend base URL.
// No localhost fallback on purpose — fail fast if misconfigured.
export const API_BASE: string = process.env.NEXT_PUBLIC_API_BASE as string;

if (!API_BASE) {
  throw new Error(
    "NEXT_PUBLIC_API_BASE is not set. Add it in Vercel → Project Settings → Environment Variables."
  );
}
