// portal/frontend/components/LinkedInAppSettings.tsx
"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { apiGet, apiPost, API_BASE, linkedInLoginUrl } from "@/lib/config";

type LinkedInSettings = {
  client_id?: string | null;
  redirect_uri?: string | null;
  has_secret?: boolean;
  suggested_redirect_uri?: string | null;
  deployment_url?: string | null;
};

type Msg = { type: "success" | "error" | "warning" | "info"; text: string };

export default function LinkedInAppSettings() {
  const [settings, setSettings] = React.useState<LinkedInSettings | null>(null);
  const [clientId, setClientId] = React.useState("");
  const [clientSecret, setClientSecret] = React.useState("");
  const [redirectUri, setRedirectUri] = React.useState("");
  const [saving, setSaving] = React.useState(false);
  const [message, setMessage] = React.useState<Msg | null>(null);
  const [expanded, setExpanded] = React.useState(true);
  const [copied, setCopied] = React.useState(false);
  const [currentUrl, setCurrentUrl] = React.useState("");

  const fetchSettings = React.useCallback(async () => {
    try {
      const s = await apiGet<LinkedInSettings>("/api/settings/linkedin");
      setSettings(s);

      // Prefill
      if (s.client_id) setClientId(s.client_id);
      const prefillRedirect =
        s.redirect_uri ||
        s.suggested_redirect_uri ||
        `${API_BASE}/auth/linkedin/callback`;
      setRedirectUri(prefillRedirect);

      // Toggle panel depending on configuration
      if (!s.has_secret) {
        setExpanded(true);
        setMessage({
          type: "info",
          text: "Please configure your LinkedIn OAuth app credentials to get started.",
        });
      } else {
        setExpanded(false);
        setMessage(null);
      }
    } catch (err) {
      console.error("Failed to load LinkedIn settings:", err);
      setExpanded(true);
      setMessage({
        type: "error",
        text: "Failed to load settings. Please refresh and try again.",
      });
    }
  }, []);

  React.useEffect(() => {
    fetchSettings();
    if (typeof window !== "undefined") {
      setCurrentUrl(window.location.href);
    }
  }, [fetchSettings]);

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setMessage(null);

    if (!clientId.trim()) {
      setMessage({ type: "error", text: "Client ID is required." });
      setSaving(false);
      return;
    }
    if (!clientSecret.trim() && !settings?.has_secret) {
      setMessage({ type: "error", text: "Client Secret is required." });
      setSaving(false);
      return;
    }
    if (!redirectUri.trim()) {
      setMessage({ type: "error", text: "Redirect URI is required." });
      setSaving(false);
      return;
    }

    try {
      const resp = await apiPost<{ ok: boolean; message: string; redirect_uri_correct?: boolean }>(
        "/api/settings/linkedin",
        {
          client_id: clientId.trim(),
          client_secret: clientSecret.trim() || undefined,
          redirect_uri: redirectUri.trim(),
        }
      );

      if (resp.redirect_uri_correct === false) {
        setMessage({
          type: "warning",
          text: "Saved, but your LinkedIn app’s redirect URI may not match exactly. Double-check it in the LinkedIn Developer portal.",
        });
      } else {
        setMessage({ type: "success", text: "Settings saved. You can now connect your LinkedIn account." });
        setExpanded(false);
      }

      await fetchSettings();
      setClientSecret(""); // Never keep the secret in memory after save
    } catch (err: any) {
      let text = err?.message || "Failed to save settings.";
      // Try to derive a cleaner message if the server returned JSON
      try {
        const parsed = JSON.parse(text);
        text = parsed?.detail || parsed?.error || parsed?.message || text;
      } catch {
        // not JSON — leave as-is
      }
      setMessage({ type: "error", text });
    } finally {
      setSaving(false);
    }
  }

  const suggestedRedirect =
    settings?.suggested_redirect_uri || `${API_BASE}/auth/linkedin/callback`;
  const loginHref = linkedInLoginUrl(true, currentUrl || undefined);
  const isConfigured = settings?.has_secret === true;

  return (
    <div className="space-y-4">
      {/* Settings */}
      <Card className="p-0">
        <div
          className="px-4 py-3 border-b cursor-pointer hover:bg-zinc-50"
          onClick={() => setExpanded((s) => !s)}
        >
          <div className="flex items-center justify-between">
            <div>
              <div className="font-semibold">
                LinkedIn OAuth Configuration
                {isConfigured && <span className="ml-2 text-green-600">✓</span>}
              </div>
              <div className="text-sm text-zinc-600">
                {isConfigured
                  ? "Your LinkedIn app is configured. Use Connect to authenticate."
                  : "Set your LinkedIn OAuth app credentials"}
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                setExpanded((s) => !s);
              }}
            >
              {expanded ? "Hide" : "Edit"}
            </Button>
          </div>
        </div>

        {expanded && (
          <div className="p-4 space-y-4">
            {/* Guide */}
            <div className="bg-blue-50 rounded-lg p-3 text-sm">
              <div className="font-medium mb-2">Quick Setup</div>
              <ol className="space-y-1 ml-4 list-decimal">
                <li>
                  <a
                    href="https://www.linkedin.com/developers/apps/new"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline"
                  >
                    Create a LinkedIn App →
                  </a>
                </li>
                <li>Add the OAuth Redirect URL shown below to your app.</li>
                <li>Under “Products”, add “Sign In with LinkedIn” and “Share on LinkedIn”.</li>
                <li>Copy your Client ID and Client Secret from the “Auth” tab.</li>
              </ol>
            </div>

            {/* Redirect */}
            <div className="space-y-2">
              <div className="text-sm font-medium">
                OAuth 2.0 Redirect URL (must match exactly in your LinkedIn app):
              </div>
              <div className="flex items-center gap-2 p-2 bg-gray-50 rounded border">
                <code className="text-xs flex-1 font-mono break-all">{suggestedRedirect}</code>
                <Button
                  size="sm"
                  variant="outline"
                  type="button"
                  onClick={() => copyToClipboard(suggestedRedirect)}
                >
                  {copied ? "Copied!" : "Copy"}
                </Button>
              </div>
              <div className="text-xs text-amber-600">
                ⚠️ Include <span className="font-mono">https://</span> and ensure no extra slashes/spaces.
              </div>
            </div>

            {/* Form */}
            <form onSubmit={handleSave} className="space-y-3">
              <div>
                <label htmlFor="client_id" className="block text-sm font-medium mb-1">
                  Client ID
                </label>
                <input
                  id="client_id"
                  type="text"
                  value={clientId}
                  onChange={(e) => setClientId(e.target.value)}
                  placeholder="e.g. 77abc123xyz"
                  required
                  className="w-full px-3 py-2 border rounded-md text-sm font-mono"
                />
              </div>

              <div>
                <label htmlFor="client_secret" className="block text-sm font-medium mb-1">
                  Client Secret
                </label>
                <input
                  id="client_secret"
                  type="password"
                  value={clientSecret}
                  onChange={(e) => setClientSecret(e.target.value)}
                  placeholder={settings?.has_secret ? "Leave blank to keep current" : "Your client secret"}
                  required={!settings?.has_secret}
                  className="w-full px-3 py-2 border rounded-md text-sm font-mono"
                />
                <div className="text-xs text-gray-500 mt-1">
                  {settings?.has_secret ? "Already set. Leave blank to keep." : "Required for first-time setup."}
                </div>
              </div>

              <div>
                <label htmlFor="redirect_uri" className="block text-sm font-medium mb-1">
                  Redirect URI
                </label>
                <input
                  id="redirect_uri"
                  type="text"
                  value={redirectUri}
                  onChange={(e) => setRedirectUri(e.target.value)}
                  placeholder={suggestedRedirect}
                  required
                  className="w-full px-3 py-2 border rounded-md text-sm font-mono"
                />
                {redirectUri && redirectUri !== suggestedRedirect && (
                  <div className="text-xs text-amber-600 mt-1">
                    Heads up: This differs from the expected value above — make sure it’s correct in your app.
                  </div>
                )}
              </div>

              <Button type="submit" disabled={saving} className="w-full">
                {saving ? "Saving..." : "Save LinkedIn Settings"}
              </Button>
            </form>

            {message && (
              <div
                className={`rounded-lg p-3 text-sm ${
                  message.type === "success"
                    ? "bg-green-50 text-green-800"
                    : message.type === "warning"
                    ? "bg-amber-50 text-amber-800"
                    : message.type === "error"
                    ? "bg-red-50 text-red-800"
                    : "bg-blue-50 text-blue-800"
                }`}
              >
                {message.text}
              </div>
            )}
          </div>
        )}
      </Card>

      {/* Connect CTA */}
      {isConfigured && (
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-semibold">Connect Your LinkedIn Account</div>
              <div className="text-sm text-zinc-600">Authenticate to start generating and publishing content.</div>
            </div>
            <a href={loginHref}>
              <Button>Connect LinkedIn →</Button>
            </a>
          </div>
        </Card>
      )}

      {/* Help */}
      {expanded && (
        <details className="text-sm">
          <summary className="cursor-pointer font-medium text-gray-700 hover:text-gray-900">
            Common Issues & Solutions
          </summary>
          <div className="mt-3 space-y-2 ml-4 text-gray-600">
            <div>
              <strong>Invalid redirect_uri:</strong> the LinkedIn app must include the exact URL shown above.
            </div>
            <div>
              <strong>Unauthorized scope:</strong> add required products/scopes in the LinkedIn app.
            </div>
            <div>
              <strong>Can’t post to org:</strong> you need org admin access and the right product approvals.
            </div>
          </div>
        </details>
      )}
    </div>
  );
}
