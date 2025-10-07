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

export default function LinkedInAppSettings() {
  const [settings, setSettings] = React.useState<LinkedInSettings | null>(null);
  const [clientId, setClientId] = React.useState("");
  const [clientSecret, setClientSecret] = React.useState("");
  const [redirectUri, setRedirectUri] = React.useState("");
  const [saving, setSaving] = React.useState(false);
  const [message, setMessage] = React.useState<{ type: "success" | "error" | "warning" | "info"; text: string } | null>(null);
  const [expanded, setExpanded] = React.useState(true);
  const [copied, setCopied] = React.useState(false);
  const [currentUrl, setCurrentUrl] = React.useState("");

  const fetchSettings = React.useCallback(async () => {
    try {
      const s = await apiGet<LinkedInSettings>("/api/settings/linkedin");
      setSettings(s);
      
      // Pre-fill form if settings exist
      if (s.client_id) setClientId(s.client_id);
      if (s.redirect_uri) {
        setRedirectUri(s.redirect_uri);
      } else if (s.suggested_redirect_uri) {
        setRedirectUri(s.suggested_redirect_uri);
      }
      
      // Show form if no settings configured
      if (!s.has_secret) {
        setExpanded(true);
        setMessage({
          type: "info",
          text: "Please configure your LinkedIn OAuth app credentials to get started."
        });
      } else {
        setExpanded(false);
      }
    } catch (err) {
      console.error("Failed to load LinkedIn settings:", err);
      setExpanded(true);
      setMessage({
        type: "error",
        text: "Failed to load settings. Please try refreshing the page."
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
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setMessage(null);

    // Validation
    if (!clientId.trim()) {
      setMessage({ type: "error", text: "Client ID is required" });
      setSaving(false);
      return;
    }
    if (!clientSecret.trim() && !settings?.has_secret) {
      setMessage({ type: "error", text: "Client Secret is required" });
      setSaving(false);
      return;
    }
    if (!redirectUri.trim()) {
      setMessage({ type: "error", text: "Redirect URI is required" });
      setSaving(false);
      return;
    }

    try {
      const response = await apiPost<{ ok: boolean; message: string; redirect_uri_correct?: boolean }>(
        "/api/settings/linkedin",
        {
          client_id: clientId.trim(),
          client_secret: clientSecret.trim() || undefined,
          redirect_uri: redirectUri.trim(),
        }
      );

      if (response.redirect_uri_correct === false) {
        setMessage({
          type: "warning",
          text: "Settings saved, but the redirect URI might not match the expected value. Double-check your LinkedIn app configuration.",
        });
      } else {
        setMessage({ type: "success", text: "Settings saved successfully! You can now connect your LinkedIn account." });
        setExpanded(false);
      }

      await fetchSettings();
      setClientSecret(""); // Clear secret after saving
    } catch (err: any) {
      const errorMessage = err?.message || "Failed to save settings";
      setMessage({ 
        type: "error", 
        text: errorMessage.includes("detail") ? JSON.parse(errorMessage).detail : errorMessage
      });
    } finally {
      setSaving(false);
    }
  }

  const suggestedRedirect = settings?.suggested_redirect_uri || `${API_BASE}/auth/linkedin/callback`;
  const loginHref = linkedInLoginUrl(true, currentUrl || undefined);
  const isConfigured = settings?.has_secret === true;

  return (
    <div className="space-y-4">
      {/* Main Settings Card */}
      <Card className="p-0">
        <div 
          className="px-4 py-3 border-b cursor-pointer hover:bg-zinc-50"
          onClick={() => setExpanded(!expanded)}
        >
          <div className="flex items-center justify-between">
            <div>
              <div className="font-semibold">
                LinkedIn OAuth Configuration
                {isConfigured && <span className="ml-2 text-green-600">✓</span>}
              </div>
              <div className="text-sm text-zinc-600">
                {isConfigured 
                  ? "Your LinkedIn app is configured. Click Connect LinkedIn to authenticate."
                  : "Set up your LinkedIn OAuth app credentials"}
              </div>
            </div>
            <Button variant="ghost" size="sm" type="button" onClick={(e) => {
              e.stopPropagation();
              setExpanded(!expanded);
            }}>
              {expanded ? "Hide" : "Edit"}
            </Button>
          </div>
        </div>

        {expanded && (
          <div className="p-4 space-y-4">
            {/* Quick Instructions */}
            <div className="bg-blue-50 rounded-lg p-3 text-sm">
              <div className="font-medium mb-2">Quick Setup:</div>
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
                <li>In Auth tab, add the OAuth Redirect URL below</li>
                <li>In Products tab, request "Sign In with LinkedIn" and "Share on LinkedIn"</li>
                <li>Copy your Client ID and Secret from the Auth tab</li>
              </ol>
            </div>

            {/* Redirect URI Display */}
            <div className="space-y-2">
              <div className="text-sm font-medium">OAuth 2.0 Redirect URL (add this to your LinkedIn app):</div>
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
                ⚠️ Must match EXACTLY in your LinkedIn app (including https://)
              </div>
            </div>

            {/* Credentials Form */}
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
                  placeholder="e.g., 77abcd1234wxyz"
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
                  placeholder={settings?.has_secret ? "Leave blank to keep current secret" : "Your client secret"}
                  required={!settings?.has_secret}
                  className="w-full px-3 py-2 border rounded-md text-sm font-mono"
                />
                <div className="text-xs text-gray-500 mt-1">
                  {settings?.has_secret ? "Already set. Leave blank to keep current." : "Required for first-time setup"}
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
                    Warning: This doesn't match the expected URL. Make sure it's correct.
                  </div>
                )}
              </div>

              <Button type="submit" disabled={saving} className="w-full">
                {saving ? "Saving..." : "Save LinkedIn Settings"}
              </Button>
            </form>

            {/* Message Display */}
            {message && (
              <div className={`rounded-lg p-3 text-sm ${
                message.type === "success" ? "bg-green-50 text-green-800" :
                message.type === "warning" ? "bg-amber-50 text-amber-800" :
                message.type === "error" ? "bg-red-50 text-red-800" :
                "bg-blue-50 text-blue-800"
              }`}>
                {message.text}
              </div>
            )}
          </div>
        )}
      </Card>

      {/* Connect LinkedIn Button - Only show when configured */}
      {isConfigured && (
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-semibold">Connect Your LinkedIn Account</div>
              <div className="text-sm text-zinc-600">
                Authenticate with LinkedIn to start publishing content
              </div>
            </div>
            <a href={loginHref}>
              <Button>
                Connect LinkedIn →
              </Button>
            </a>
          </div>
        </Card>
      )}

      {/* Troubleshooting */}
      {expanded && (
        <details className="text-sm">
          <summary className="cursor-pointer font-medium text-gray-700 hover:text-gray-900">
            Common Issues & Solutions
          </summary>
          <div className="mt-3 space-y-2 ml-4 text-gray-600">
            <div>
              <strong>Invalid redirect_uri:</strong> The URL in your LinkedIn app must match exactly
            </div>
            <div>
              <strong>Unauthorized scope:</strong> Request required products in LinkedIn app
            </div>
            <div>
              <strong>Can't post to org:</strong> Need "Advertising API" product + org admin access
            </div>
          </div>
        </details>
      )}
    </div>
  );
}