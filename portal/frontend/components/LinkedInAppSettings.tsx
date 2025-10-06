"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost, setLoginSid, getLoginSid, linkedInLoginUrl } from "@/lib/config";
import { Button } from "@/components/ui/button";

export default function LinkedInAppSettings() {
  const [client_id, setClientId] = useState("");
  const [client_secret, setClientSecret] = useState("");
  const [redirect_uri, setRedirectUri] = useState("");
  const [scope, setScope] = useState("openid profile email w_member_social rw_organization_admin w_organization_social");
  const [sid, setSid] = useState<string | undefined>(getLoginSid());
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const data = await apiGet<any>("/api/settings/linkedin");
        // if env has defaults, we can show redirect for convenience
        if (data?.redirect_uri && !redirect_uri) setRedirectUri(data.redirect_uri);
      } catch {
        // ignore
      } finally {
        setLoading(false);
      }
    })();
  }, []); // eslint-disable-line

  async function onSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      const resp = await apiPost<{ ok: boolean; sid: string }>("/api/settings/linkedin", {
        client_id,
        client_secret,
        redirect_uri,
        scope,
        include_org_default: true,
      });
      setSid(resp.sid);
      setLoginSid(resp.sid);
      alert("Saved! You can now use Connect LinkedIn.");
    } catch (err: any) {
      alert(err?.message || "Failed to save settings");
    } finally {
      setSaving(false);
    }
  }

  const loginHref = linkedInLoginUrl(true, sid);

  return (
    <div className="rounded-2xl border border-zinc-200 p-4 space-y-3">
      <h3 className="font-semibold">LinkedIn App Settings</h3>
      {loading ? (
        <div className="text-sm text-zinc-600">Loading…</div>
      ) : (
        <form onSubmit={onSave} className="space-y-3">
          <input
            className="w-full border rounded p-2"
            placeholder="Client ID"
            value={client_id}
            onChange={(e)=>setClientId(e.target.value)}
          />
          <input
            className="w-full border rounded p-2"
            placeholder="Client Secret"
            value={client_secret}
            onChange={(e)=>setClientSecret(e.target.value)}
          />
          <input
            className="w-full border rounded p-2"
            placeholder="Redirect URI"
            value={redirect_uri}
            onChange={(e)=>setRedirectUri(e.target.value)}
          />
          <input
            className="w-full border rounded p-2"
            placeholder="Scopes"
            value={scope}
            onChange={(e)=>setScope(e.target.value)}
          />
          <div className="flex items-center gap-2">
            <Button type="submit" isLoading={saving}>Save</Button>
            <a href={loginHref}><Button variant="outline">Connect LinkedIn</Button></a>
          </div>
          {sid ? <div className="text-xs text-zinc-500">sid: {sid}</div> : null}
        </form>
      )}
    </div>
  );
}
