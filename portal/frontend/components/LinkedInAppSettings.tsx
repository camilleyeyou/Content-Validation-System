// portal/frontend/components/LinkedInAppSettings.tsx
"use client";

import * as React from "react";
import { apiGet, apiPost } from "@/lib/config";
import { Card, CardContent, CardHeader, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

type Settings = {
  client_id?: string;
  client_secret?: string; // masked when reading
  redirect_uri?: string;
  version?: string;
  org_id?: string;
  extra_scopes?: string;
  include_org_scopes?: boolean;
};

export default function LinkedInAppSettings() {
  const [form, setForm] = React.useState<Settings>({
    version: "202509",
    include_org_scopes: true,
  });
  const [loading, setLoading] = React.useState(false);
  const [saved, setSaved] = React.useState<string | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    (async () => {
      setError(null);
      try {
        const s = await apiGet<{ linkedin: Settings }>("/api/settings/linkedin");
        setForm((prev) => ({ ...prev, ...s.linkedin }));
      } catch (e: any) {
        // Not fatal if empty; show only if real error
        console.warn("settings load:", e?.message || e);
      }
    })();
  }, []);

  async function onSave() {
    setLoading(true);
    setSaved(null);
    setError(null);
    try {
      const payload = form;
      await apiPost("/api/settings/linkedin", payload);
      setSaved("LinkedIn settings saved.");
    } catch (e: any) {
      setError(e?.message || "Save failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card>
      <CardHeader
        title="LinkedIn App Settings"
        description="Provide your LinkedIn app credentials (client id/secret and redirect URI). These settings are used by the OAuth login."
        actions={<Button onClick={onSave} isLoading={loading}>Save</Button>}
      />
      <CardContent className="grid gap-4 sm:grid-cols-2">
        <div className="sm:col-span-1">
          <label className="block text-sm text-zinc-600 mb-1">Client ID</label>
          <input
            className="w-full rounded-xl border border-zinc-300 bg-white px-3 py-2 outline-none focus:ring-2 focus:ring-black/10"
            value={form.client_id || ""}
            onChange={(e) => setForm((f) => ({ ...f, client_id: e.target.value }))}
            placeholder="77xxxxxxxxxxxx"
          />
        </div>
        <div className="sm:col-span-1">
          <label className="block text-sm text-zinc-600 mb-1">Client Secret</label>
          <input
            className="w-full rounded-xl border border-zinc-300 bg-white px-3 py-2 outline-none focus:ring-2 focus:ring-black/10"
            value={form.client_secret || ""}
            onChange={(e) => setForm((f) => ({ ...f, client_secret: e.target.value }))}
            placeholder="********"
          />
        </div>
        <div className="sm:col-span-2">
          <label className="block text-sm text-zinc-600 mb-1">Redirect URI</label>
          <input
            className="w-full rounded-xl border border-zinc-300 bg-white px-3 py-2 outline-none focus:ring-2 focus:ring-black/10"
            value={form.redirect_uri || ""}
            onChange={(e) => setForm((f) => ({ ...f, redirect_uri: e.target.value }))}
            placeholder="https://YOUR-RAILWAY-DOMAIN/auth/linkedin/callback"
          />
          <p className="text-xs text-zinc-500 mt-1">
            Must exactly match the Redirect URL in your LinkedIn app.
          </p>
        </div>
        <div>
          <label className="block text-sm text-zinc-600 mb-1">LinkedIn Version</label>
          <input
            className="w-full rounded-xl border border-zinc-300 bg-white px-3 py-2 outline-none focus:ring-2 focus:ring-black/10"
            value={form.version || ""}
            onChange={(e) => setForm((f) => ({ ...f, version: e.target.value }))}
            placeholder="202509"
          />
        </div>
        <div>
          <label className="block text-sm text-zinc-600 mb-1">Org ID (optional)</label>
          <input
            className="w-full rounded-xl border border-zinc-300 bg-white px-3 py-2 outline-none focus:ring-2 focus:ring-black/10"
            value={form.org_id || ""}
            onChange={(e) => setForm((f) => ({ ...f, org_id: e.target.value }))}
            placeholder="123456"
          />
        </div>
        <div className="sm:col-span-2">
          <label className="block text-sm text-zinc-600 mb-1">Extra Scopes (space-separated)</label>
          <input
            className="w-full rounded-xl border border-zinc-300 bg-white px-3 py-2 outline-none focus:ring-2 focus:ring-black/10"
            value={form.extra_scopes || ""}
            onChange={(e) => setForm((f) => ({ ...f, extra_scopes: e.target.value }))}
            placeholder="rw_organization_admin w_organization_social"
          />
        </div>
        <label className="inline-flex items-center gap-2">
          <input
            type="checkbox"
            checked={!!form.include_org_scopes}
            onChange={(e) => setForm((f) => ({ ...f, include_org_scopes: e.target.checked }))}
          />
          <span className="text-sm text-zinc-700">Include org scopes in login</span>
        </label>
      </CardContent>
      <CardFooter>
        {saved ? <div className="text-green-700">{saved}</div> : null}
        {error ? <div className="text-red-700">{error}</div> : null}
      </CardFooter>
    </Card>
  );
}
