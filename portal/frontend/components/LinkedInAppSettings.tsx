"use client";
import * as React from "react";
import { Button } from "@/components/ui/button";

const API_BASE =
  (process.env.NEXT_PUBLIC_API_BASE || "").replace(/\/+$/, "") ||
  "http://localhost:8001";

type SaveResp = { cfg: string; login_url: string };

export default function LinkedInAppSettings() {
  const [clientId, setClientId] = React.useState("");
  const [clientSecret, setClientSecret] = React.useState("");
  const [redirectUri, setRedirectUri] = React.useState(
    `${API_BASE}/auth/linkedin/callback`
  );
  const [orgId, setOrgId] = React.useState("");
  const [includeOrg, setIncludeOrg] = React.useState(true);
  const [saving, setSaving] = React.useState(false);
  const [err, setErr] = React.useState<string | null>(null);

  async function onSaveAndConnect() {
    setSaving(true);
    setErr(null);
    try {
      const res = await fetch(`${API_BASE}/api/settings/linkedin`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          client_id: clientId,
          client_secret: clientSecret,
          redirect_uri: redirectUri,
          org_id: orgId || null,
          include_org_scopes: includeOrg,
        }),
      });
      if (!res.ok) {
        const j = await res.json().catch(() => ({}));
        throw new Error(j.error || j.detail || `${res.status} ${res.statusText}`);
      }
      const data = (await res.json()) as SaveResp;
      // Hard redirect to LinkedIn (auth screen)
      window.location.href = data.login_url;
    } catch (e: any) {
      setErr(e?.message || "Failed to start LinkedIn auth");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="rounded-2xl border border-zinc-200 bg-white p-4 space-y-3">
      <div className="font-medium">Bring Your Own LinkedIn App</div>
      <p className="text-sm text-zinc-600">
        Paste your LinkedIn App credentials. We’ll use these for OAuth and posting.
      </p>
      <div className="grid sm:grid-cols-2 gap-3">
        <label className="space-y-1">
          <span className="text-sm text-zinc-600">Client ID</span>
          <input
            className="w-full rounded-lg border border-zinc-300 px-3 py-2"
            value={clientId}
            onChange={(e) => setClientId(e.target.value)}
            placeholder="e.g. 77abc123..."
          />
        </label>
        <label className="space-y-1">
          <span className="text-sm text-zinc-600">Client Secret</span>
          <input
            className="w-full rounded-lg border border-zinc-300 px-3 py-2"
            value={clientSecret}
            onChange={(e) => setClientSecret(e.target.value)}
            placeholder="Your secret"
            type="password"
          />
        </label>
        <label className="space-y-1 sm:col-span-2">
          <span className="text-sm text-zinc-600">Redirect URI</span>
          <input
            className="w-full rounded-lg border border-zinc-300 px-3 py-2"
            value={redirectUri}
            onChange={(e) => setRedirectUri(e.target.value)}
            placeholder={`${API_BASE}/auth/linkedin/callback`}
          />
          <span className="text-xs text-zinc-500">
            This must match exactly in your LinkedIn app settings.
          </span>
        </label>
        <label className="space-y-1">
          <span className="text-sm text-zinc-600">Org ID (optional)</span>
          <input
            className="w-full rounded-lg border border-zinc-300 px-3 py-2"
            value={orgId}
            onChange={(e) => setOrgId(e.target.value)}
            placeholder="123456789"
          />
        </label>
        <label className="flex items-center gap-2 pt-5">
          <input
            type="checkbox"
            checked={includeOrg}
            onChange={(e) => setIncludeOrg(e.target.checked)}
          />
          <span className="text-sm text-zinc-700">Request organization scopes</span>
        </label>
      </div>
      {err ? (
        <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
          {err}
        </div>
      ) : null}
      <div className="pt-1">
        <Button onClick={onSaveAndConnect} isLoading={saving}>
          Save & Connect
        </Button>
      </div>
    </div>
  );
}
