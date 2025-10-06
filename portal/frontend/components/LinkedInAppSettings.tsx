"use client";

import * as React from "react";
import { apiGet, apiPost } from "@/lib/config";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

type Settings = {
  client_id: string;
  client_secret: string;
  redirect_uri: string;
  scopes?: string[];
};

export default function LinkedInAppSettings() {
  const [form, setForm] = React.useState<Settings>({
    client_id: "",
    client_secret: "",
    redirect_uri: "",
    scopes: ["openid","profile","email","w_member_social","rw_organization_admin","w_organization_social"],
  });
  const [loaded, setLoaded] = React.useState(false);
  const [notice, setNotice] = React.useState<string | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [busy, setBusy] = React.useState(false);

  React.useEffect(() => {
    (async () => {
      try {
        const r = await apiGet<{exists:boolean; settings?: Settings}>("/api/settings/linkedin");
        if (r.exists && r.settings) setForm(r.settings);
      } catch (e:any) {
        // ignore load errors (most likely first run)
        console.warn("settings load:", e?.message || e);
      } finally {
        setLoaded(true);
      }
    })();
  }, []);

  async function onSave(e: React.FormEvent) {
    e.preventDefault();
    setNotice(null);
    setError(null);
    setBusy(true);
    try {
      const payload = { ...form, scopes: form.scopes ?? [] };
      await apiPost("/api/settings/linkedin", payload);
      setNotice("Saved LinkedIn app settings.");
    } catch (e:any) {
      setError(e?.message || "Save failed");
    } finally {
      setBusy(false);
    }
  }

  if (!loaded) return null;

  return (
    <Card>
      <CardHeader title="LinkedIn App Settings" description="Provide credentials used by the API for OAuth." />
      <CardContent>
        {notice && <div className="mb-3 rounded-md bg-green-50 border border-green-200 px-3 py-2 text-sm text-green-800">{notice}</div>}
        {error && <div className="mb-3 rounded-md bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-800">{error}</div>}
        <form onSubmit={onSave} className="grid gap-4 sm:grid-cols-2">
          <label className="text-sm">
            <div className="text-zinc-600 mb-1">Client ID</div>
            <input
              className="w-full rounded-md border border-zinc-300 px-3 py-2"
              value={form.client_id}
              onChange={e => setForm(f => ({...f, client_id: e.target.value}))}
              required
            />
          </label>
          <label className="text-sm">
            <div className="text-zinc-600 mb-1">Client Secret</div>
            <input
              className="w-full rounded-md border border-zinc-300 px-3 py-2"
              type="password"
              value={form.client_secret}
              onChange={e => setForm(f => ({...f, client_secret: e.target.value}))}
              required
            />
          </label>
          <label className="text-sm sm:col-span-2">
            <div className="text-zinc-600 mb-1">Redirect URI</div>
            <input
              className="w-full rounded-md border border-zinc-300 px-3 py-2"
              value={form.redirect_uri}
              onChange={e => setForm(f => ({...f, redirect_uri: e.target.value}))}
              placeholder="https://YOUR-API-HOST/auth/linkedin/callback"
              required
            />
          </label>
          <label className="text-sm sm:col-span-2">
            <div className="text-zinc-600 mb-1">Scopes (space separated)</div>
            <input
              className="w-full rounded-md border border-zinc-300 px-3 py-2"
              value={(form.scopes || []).join(" ")}
              onChange={e => setForm(f => ({...f, scopes: e.target.value.trim().split(/\s+/).filter(Boolean)}))}
            />
          </label>
          <div className="sm:col-span-2">
            <Button type="submit" isLoading={busy}>Save</Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
