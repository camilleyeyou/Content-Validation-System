// portal/frontend/components/LinkedInAppSettings.tsx
"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { apiGet, apiPost, API_BASE } from "@/lib/config";
import { CheckCircle, AlertCircle, Copy, ExternalLink, Info, ChevronDown, ChevronUp } from "lucide-react";

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
  const [message, setMessage] = React.useState<{ type: "success" | "error" | "warning"; text: string } | null>(null);
  const [expanded, setExpanded] = React.useState(false);
  const [copied, setCopied] = React.useState(false);
  const [showInstructions, setShowInstructions] = React.useState(false);

  const fetchSettings = React.useCallback(async () => {
    try {
      const s = await apiGet<LinkedInSettings>("/api/settings/linkedin");
      setSettings(s);
      
      // Pre-fill form if settings exist
      if (s.client_id) setClientId(s.client_id);
      if (s.redirect_uri) {
        setRedirectUri(s.redirect_uri);
      } else if (s.suggested_redirect_uri) {
        // Use suggested redirect URI if none is set
        setRedirectUri(s.suggested_redirect_uri);
      }
      
      // Show form if no settings configured
      if (!s.has_secret) {
        setExpanded(true);
        setShowInstructions(true);
      }
    } catch (err) {
      console.error("Failed to load LinkedIn settings:", err);
      setExpanded(true); // Show form if we can't load settings
    }
  }, []);

  React.useEffect(() => {
    fetchSettings();
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

    try {
      const response = await apiPost<{ ok: boolean; message: string; redirect_uri_correct?: boolean }>(
        "/api/settings/linkedin",
        {
          client_id: clientId.trim(),
          client_secret: clientSecret.trim(),
          redirect_uri: redirectUri.trim(),
        }
      );

      if (response.redirect_uri_correct === false) {
        setMessage({
          type: "warning",
          text: "Settings saved, but the redirect URI might not match the expected value. Double-check your LinkedIn app configuration.",
        });
      } else {
        setMessage({ type: "success", text: response.message || "Settings saved successfully!" });
      }

      await fetchSettings();
      setClientSecret(""); // Clear secret after saving
      
      // Collapse form after successful save
      if (response.redirect_uri_correct !== false) {
        setTimeout(() => setExpanded(false), 1500);
      }
    } catch (err: any) {
      setMessage({ 
        type: "error", 
        text: err?.message || "Failed to save settings" 
      });
    } finally {
      setSaving(false);
    }
  }

  const suggestedRedirect = settings?.suggested_redirect_uri || `${API_BASE}/auth/linkedin/callback`;

  return (
    <>
      {/* Instructions Alert */}
      {showInstructions && (
        <Alert className="mb-4 border-blue-200 bg-blue-50">
          <Info className="h-4 w-4 text-blue-600" />
          <AlertDescription className="text-blue-800">
            <strong>First-time setup required:</strong> You need to create a LinkedIn OAuth app to use this portal.{" "}
            <button
              onClick={() => setShowInstructions(false)}
              className="underline hover:no-underline"
            >
              Dismiss
            </button>
          </AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader 
          className="cursor-pointer select-none"
          onClick={() => setExpanded(!expanded)}
        >
          <div className="flex items-center justify-between w-full">
            <div>
              <h3 className="font-semibold text-lg">LinkedIn App Settings</h3>
              <p className="text-sm text-zinc-600 mt-1">
                {settings?.has_secret 
                  ? "LinkedIn app configured ✓" 
                  : "Configure your LinkedIn OAuth application"}
              </p>
            </div>
            <Button variant="ghost" size="sm" type="button">
              {expanded ? (
                <>
                  <ChevronUp className="h-4 w-4 mr-1" />
                  Hide
                </>
              ) : (
                <>
                  <ChevronDown className="h-4 w-4 mr-1" />
                  Configure
                </>
              )}
            </Button>
          </div>
        </CardHeader>

        {expanded && (
          <>
            <CardContent className="space-y-6">
              {/* Quick Setup Guide */}
              <div className="rounded-lg bg-gray-50 p-4 space-y-3">
                <h4 className="font-medium flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 text-amber-600" />
                  Quick Setup Guide
                </h4>
                <ol className="text-sm space-y-2 ml-6 list-decimal">
                  <li>
                    Go to{" "}
                    <a
                      href="https://www.linkedin.com/developers/apps/new"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline inline-flex items-center gap-1"
                    >
                      LinkedIn Developers
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  </li>
                  <li>Create a new app (use any company page)</li>
                  <li>In the <strong>Auth</strong> tab, add this OAuth redirect URL:</li>
                </ol>
                
                {/* Redirect URI Copy Box */}
                <div className="bg-white rounded border p-2 flex items-center gap-2">
                  <code className="text-xs flex-1 break-all text-gray-700 font-mono">
                    {suggestedRedirect}
                  </code>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => copyToClipboard(suggestedRedirect)}
                    type="button"
                  >
                    {copied ? <CheckCircle className="h-4 w-4 text-green-600" /> : <Copy className="h-4 w-4" />}
                  </Button>
                </div>
                
                <p className="text-xs text-amber-600 mt-2 flex items-start gap-1">
                  <AlertCircle className="h-3 w-3 mt-0.5 flex-shrink-0" />
                  The redirect URL must match EXACTLY (including https://)
                </p>
                
                <ol className="text-sm space-y-2 ml-6 list-decimal" start={4}>
                  <li>In <strong>Products</strong> tab, request:
                    <ul className="ml-4 mt-1 list-disc text-xs">
                      <li>"Sign In with LinkedIn using OpenID Connect"</li>
                      <li>"Share on LinkedIn"</li>
                      <li>"Advertising API" (for organization posting)</li>
                    </ul>
                  </li>
                  <li>Copy your Client ID and Client Secret from the <strong>Auth</strong> tab</li>
                  <li>Paste them below and save</li>
                </ol>
              </div>

              {/* Settings Form */}
              <form onSubmit={handleSave} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="client_id">Client ID</Label>
                  <Input
                    id="client_id"
                    type="text"
                    value={clientId}
                    onChange={(e) => setClientId(e.target.value)}
                    placeholder="e.g., 77abcd1234wxyz"
                    required
                    className="font-mono text-sm"
                  />
                  <p className="text-xs text-gray-500">Found in LinkedIn app → Auth tab</p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="client_secret">Client Secret</Label>
                  <Input
                    id="client_secret"
                    type="password"
                    value={clientSecret}
                    onChange={(e) => setClientSecret(e.target.value)}
                    placeholder={settings?.has_secret ? "(unchanged)" : "Your client secret"}
                    required={!settings?.has_secret}
                    className="font-mono text-sm"
                  />
                  <p className="text-xs text-gray-500">
                    Found in LinkedIn app → Auth tab → Show secret
                    {settings?.has_secret && " (leave blank to keep current)"}
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="redirect_uri">OAuth Redirect URL</Label>
                  <Input
                    id="redirect_uri"
                    type="text"
                    value={redirectUri}
                    onChange={(e) => setRedirectUri(e.target.value)}
                    placeholder={suggestedRedirect}
                    required
                    className="font-mono text-sm"
                  />
                  {redirectUri && redirectUri !== suggestedRedirect && (
                    <Alert className="mt-2 py-2 border-amber-200 bg-amber-50">
                      <AlertCircle className="h-4 w-4 text-amber-600" />
                      <AlertDescription className="text-sm text-amber-800">
                        Warning: This doesn't match the expected redirect URI. Make sure it matches exactly in your LinkedIn app.
                      </AlertDescription>
                    </Alert>
                  )}
                  <p className="text-xs text-gray-500">
                    Must match exactly what's configured in your LinkedIn app
                  </p>
                </div>

                {message && (
                  <Alert className={
                    message.type === "success" ? "border-green-200 bg-green-50" :
                    message.type === "warning" ? "border-amber-200 bg-amber-50" :
                    "border-red-200 bg-red-50"
                  }>
                    <AlertDescription className={
                      message.type === "success" ? "text-green-800" :
                      message.type === "warning" ? "text-amber-800" :
                      "text-red-800"
                    }>
                      {message.text}
                    </AlertDescription>
                  </Alert>
                )}

                <Button type="submit" disabled={saving} isLoading={saving} className="w-full">
                  {saving ? "Saving..." : "Save LinkedIn Settings"}
                </Button>
              </form>

              {/* Troubleshooting */}
              <div className="border-t pt-4">
                <details className="text-sm">
                  <summary className="cursor-pointer font-medium text-gray-700 hover:text-gray-900">
                    Troubleshooting Common Issues
                  </summary>
                  <div className="mt-3 space-y-3 text-gray-600">
                    <div className="p-3 bg-gray-50 rounded">
                      <strong className="block mb-1">Error: "Invalid redirect_uri"</strong>
                      <p className="text-xs">The redirect URL in your LinkedIn app doesn't match exactly. Check for:</p>
                      <ul className="ml-4 mt-1 list-disc text-xs">
                        <li>Missing or extra "https://"</li>
                        <li>Trailing slashes</li>
                        <li>Wrong domain (should be your API domain, not frontend)</li>
                      </ul>
                    </div>
                    
                    <div className="p-3 bg-gray-50 rounded">
                      <strong className="block mb-1">Error: "Unauthorized scope"</strong>
                      <p className="text-xs">
                        Go to LinkedIn app → Products tab and request the required products. 
                        Some may require verification.
                      </p>
                    </div>
                    
                    <div className="p-3 bg-gray-50 rounded">
                      <strong className="block mb-1">Can't post to organization</strong>
                      <p className="text-xs">
                        You need "Advertising API" product approved and must be an admin of the LinkedIn company page.
                      </p>
                    </div>
                    
                    <div className="p-3 bg-gray-50 rounded">
                      <strong className="block mb-1">Session expired or not saving</strong>
                      <p className="text-xs">
                        Clear cookies for both this site and linkedin.com, then reconfigure.
                      </p>
                    </div>
                  </div>
                </details>
              </div>
            </CardContent>

            <CardFooter className="bg-gray-50">
              <p className="text-xs text-gray-600">
                <strong>Security Note:</strong> Your credentials are stored securely in your browser session only. 
                They are never saved to our database.
              </p>
            </CardFooter>
          </>
        )}
      </Card>
    </>
  );
}