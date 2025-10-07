// portal/frontend/app/dashboard/page.tsx
"use client";

import * as React from "react";
import TokenSync from "@/components/TokenSync";
import LinkedInAppSettings from "@/components/LinkedInAppSettings";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { apiGet, apiPost } from "@/lib/config";

type Me = { 
  sub: string; 
  name: string; 
  email?: string | null; 
  org_preferred?: string | null;
  token_expires_in?: number;
};

type ApprovedRec = {
  id: string;
  content: string;
  hashtags: string[];
  status: string;
  created_at: string;
  li_post_id?: string | null;
  error_message?: string | null;
};

type OrgsResp = { orgs: { id: string; urn: string }[] } | { error?: string };

export default function DashboardPage() {
  const [me, setMe] = React.useState<Me | null>(null);
  const [orgs, setOrgs] = React.useState<{ id: string; urn: string }[]>([]);
  const [approved, setApproved] = React.useState<ApprovedRec[]>([]);
  const [sel, setSel] = React.useState<Record<string, boolean>>({});
  const [busyGen, setBusyGen] = React.useState(false);
  const [busyPub, setBusyPub] = React.useState(false);
  const [notice, setNotice] = React.useState<string | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [isAuthenticated, setIsAuthenticated] = React.useState(false);
  const [loading, setLoading] = React.useState(true);
  const [debug, setDebug] = React.useState(false); // Debug toggle

  const selectedIds = React.useMemo(
    () => Object.entries(sel).filter(([, v]) => v).map(([k]) => k),
    [sel]
  );

  const fetchAll = React.useCallback(async () => {
    setError(null);
    setLoading(true);
    
    try {
      // Always fetch approved posts (works even when not authenticated)
      const approvedResp = await apiGet<ApprovedRec[]>("/api/approved");
      console.log("Fetched approved posts:", approvedResp); // Debug log
      setApproved(approvedResp || []); // Ensure we always set an array

      // Try to fetch user info
      try {
        const meResp = await apiGet<Me>("/api/me");
        setMe(meResp);
        setIsAuthenticated(true);

        // If authenticated, try to fetch orgs
        try {
          const o = await apiGet<OrgsResp>("/api/orgs");
          if (o && "orgs" in o) {
            setOrgs(o.orgs || []);
          }
        } catch (orgError) {
          console.log("Could not fetch orgs - may need additional permissions");
        }
      } catch (authError) {
        // Not authenticated - this is normal
        setMe(null);
        setIsAuthenticated(false);
        setOrgs([]);
      }
    } catch (e: any) {
      console.error("Error fetching data:", e); // Debug log
      setError(e?.message || "Failed to load data");
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    fetchAll();
    // Poll every 5 seconds when authenticated to catch session updates
    const interval = setInterval(() => {
      if (document.visibilityState === 'visible') {
        fetchAll();
      }
    }, 5000);
    return () => clearInterval(interval);
  }, [fetchAll]);

  function clearSelection() {
    setSel({});
  }

  function isSelected(id: string) {
    return !!sel[id];
  }

  async function onGenerateApproved() {
    if (!isAuthenticated) {
      setError("Please connect your LinkedIn account first");
      return;
    }

    setBusyGen(true);
    setNotice(null);
    setError(null);
    
    try {
      console.log("Generating posts..."); // Debug log
      const res = await apiPost<{ approved_count: number; batch_id?: string }>("/api/run-batch", {});
      console.log("Generate response:", res); // Debug log
      
      setNotice(`Generated ${res.approved_count} approved post(s). Refreshing...`);
      
      // Force a refresh after a short delay to ensure backend has saved
      setTimeout(async () => {
        await fetchAll();
        // Check if posts were actually added
        const newApproved = await apiGet<ApprovedRec[]>("/api/approved");
        console.log("After generate, approved posts:", newApproved); // Debug log
        if (newApproved && newApproved.length > approved.length) {
          setNotice(`Successfully added ${newApproved.length - approved.length} new posts!`);
        } else if (newApproved && newApproved.length === approved.length) {
          setError("Posts were generated but may not have been saved. Try refreshing the page.");
        }
        setApproved(newApproved || []);
      }, 500);
      
    } catch (e: any) {
      console.error("Generate error:", e); // Debug log
      setError(`Generate failed: ${e?.message || e}`);
    } finally {
      setBusyGen(false);
    }
  }

  async function onPublish(target: "MEMBER" | "ORG", publishNow: boolean) {
    if (!isAuthenticated) {
      setError("Please connect your LinkedIn account first");
      return;
    }
    
    if (selectedIds.length === 0) {
      setError("Please select at least one post to publish");
      return;
    }
    
    setBusyPub(true);
    setNotice(null);
    setError(null);
    
    try {
      const payload: any = { 
        ids: selectedIds, 
        target, 
        publish_now: publishNow 
      };
      
      if (target === "ORG") {
        if (orgs.length === 0) {
          throw new Error("No organizations available. Check your LinkedIn app permissions.");
        }
        payload.org_id = orgs[0].id;
      }

      console.log("Publishing with payload:", payload); // Debug log
      const res = await apiPost<{ successful: number; results: any[] }>(
        "/api/approved/publish",
        payload
      );
      console.log("Publish response:", res); // Debug log
      
      setNotice(`Successfully ${publishNow ? 'published' : 'drafted'} ${res.successful} of ${selectedIds.length} posts`);
      clearSelection();
      await fetchAll();
    } catch (e: any) {
      console.error("Publish error:", e); // Debug log
      setError(`Publish failed: ${e?.message || e}`);
    } finally {
      setBusyPub(false);
    }
  }

  if (loading) {
    return (
      <>
        <TokenSync />
        <div className="max-w-5xl mx-auto space-y-6">
          <div className="flex items-center justify-center py-12">
            <div className="text-zinc-600">Loading...</div>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <TokenSync />
      <div className="max-w-5xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Dashboard</h1>
            <p className="text-sm text-zinc-600">
              Configure LinkedIn, generate content, and publish
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => fetchAll()}>
              Refresh
            </Button>
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => setDebug(!debug)}
            >
              {debug ? "Hide" : "Show"} Debug
            </Button>
          </div>
        </div>

        {/* Debug Info */}
        {debug && (
          <Card className="p-4 bg-gray-50 text-xs font-mono">
            <div>Authenticated: {isAuthenticated ? "Yes" : "No"}</div>
            <div>User: {me?.name || "None"}</div>
            <div>Orgs: {orgs.length}</div>
            <div>Approved Posts: {approved.length}</div>
            <div>Posts Data: {JSON.stringify(approved.slice(0, 1), null, 2)}</div>
          </Card>
        )}

        {/* Status Messages */}
        {notice && (
          <div className="rounded-xl bg-green-50 text-green-800 border border-green-200 px-4 py-3">
            {notice}
          </div>
        )}
        {error && (
          <div className="rounded-xl bg-red-50 text-red-800 border border-red-200 px-4 py-3">
            {error}
          </div>
        )}

        {/* Step 1: LinkedIn Configuration */}
        <LinkedInAppSettings />

        {/* Step 2: Account Status */}
        {isAuthenticated ? (
          <Card className="p-4 space-y-3 border-green-200 bg-green-50/50">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-semibold text-green-800">✓ Connected to LinkedIn</div>
                <div className="text-sm text-green-700">
                  Signed in as <strong>{me?.name || "LinkedIn User"}</strong>
                  {me?.email && <span className="text-green-600"> ({me.email})</span>}
                </div>
              </div>
            </div>
            {orgs.length > 0 && (
              <div className="text-sm text-green-700">
                Organizations available: <strong>{orgs.map(o => o.id).join(", ")}</strong>
              </div>
            )}
          </Card>
        ) : (
          <Card className="p-4 border-amber-200 bg-amber-50/50">
            <div className="font-semibold text-amber-800">⚠️ Not Connected</div>
            <div className="text-sm text-amber-700 mt-1">
              Please configure your LinkedIn app above and connect your account
            </div>
          </Card>
        )}

        {/* Step 3: Generate Content */}
        <Card className="p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-semibold">Generate Approved Posts</div>
              <div className="text-sm text-zinc-600">
                Run your content generation pipeline
              </div>
            </div>
            <Button 
              onClick={onGenerateApproved} 
              disabled={busyGen || !isAuthenticated}
            >
              {busyGen ? "Generating…" : "Generate"}
            </Button>
          </div>
          {!isAuthenticated && (
            <div className="text-sm text-amber-600">
              Connect your LinkedIn account to generate posts
            </div>
          )}
        </Card>

        {/* Step 4: Approved Queue */}
        <Card className="p-0">
          <div className="px-4 py-3 border-b">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-semibold">Approved Queue</div>
                <div className="text-sm text-zinc-600">
                  {approved.length 
                    ? `${approved.length} post${approved.length === 1 ? '' : 's'} ready` 
                    : "No approved posts yet"}
                </div>
              </div>
              {approved.length > 0 && (
                <div className="text-sm">
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      onChange={(e) => {
                        if (e.target.checked) {
                          const newSel: Record<string, boolean> = {};
                          approved.forEach(p => newSel[p.id] = true);
                          setSel(newSel);
                        } else {
                          setSel({});
                        }
                      }}
                      checked={approved.length > 0 && approved.every(p => sel[p.id])}
                    />
                    Select all
                  </label>
                </div>
              )}
            </div>
          </div>

          {/* Publishing Controls */}
          {approved.length > 0 && (
            <div className="p-4 border-b">
              <div className="flex flex-wrap gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onPublish("MEMBER", false)}
                  disabled={busyPub || selectedIds.length === 0 || !isAuthenticated}
                >
                  Draft as Member
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => onPublish("MEMBER", true)}
                  disabled={busyPub || selectedIds.length === 0 || !isAuthenticated}
                >
                  Publish as Member
                </Button>
                {orgs.length > 0 && (
                  <>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => onPublish("ORG", false)}
                      disabled={busyPub || selectedIds.length === 0 || !isAuthenticated}
                    >
                      Draft as Org
                    </Button>
                    <Button
                      size="sm"
                      onClick={() => onPublish("ORG", true)}
                      disabled={busyPub || selectedIds.length === 0 || !isAuthenticated}
                    >
                      Publish as Org
                    </Button>
                  </>
                )}
              </div>
              {!isAuthenticated && selectedIds.length > 0 && (
                <div className="text-sm text-amber-600 mt-2">
                  Connect your LinkedIn account to publish posts
                </div>
              )}
            </div>
          )}

          {/* Post List */}
          <div className="divide-y divide-zinc-100">
            {!approved || approved.length === 0 ? (
              <div className="px-6 py-8 text-sm text-zinc-600 text-center">
                No posts yet. Click "Generate" to create some sample posts.
              </div>
            ) : (
              approved.map((p, index) => (
                <label
                  key={p.id || index}
                  className="flex items-start gap-3 px-6 py-4 hover:bg-zinc-50 cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={isSelected(p.id)}
                    onChange={(e) =>
                      setSel((s) => ({ ...s, [p.id]: e.target.checked }))
                    }
                    className="mt-1 h-4 w-4"
                  />
                  <div className="min-w-0 flex-1">
                    <div className="font-medium">
                      {p.content || "No content"}
                    </div>
                    {p.hashtags && p.hashtags.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1.5">
                        {p.hashtags.map((h, i) => (
                          <span
                            key={i}
                            className="inline-flex items-center rounded-full bg-zinc-100 px-2.5 py-1 text-xs font-medium text-zinc-700"
                          >
                            #{h.replace(/^#/, "")}
                          </span>
                        ))}
                      </div>
                    )}
                    <div className="mt-2 text-xs text-zinc-600">
                      Status: <span className="font-medium">{p.status || "pending"}</span>
                      {p.li_post_id && (
                        <span className="ml-2">
                          LinkedIn ID: <span className="font-mono">{p.li_post_id}</span>
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="text-xs text-zinc-500 shrink-0">
                    {p.created_at ? new Date(p.created_at).toLocaleDateString() : "Now"}
                  </div>
                </label>
              ))
            )}
          </div>

          {/* Selection Summary */}
          {approved.length > 0 && (
            <div className="flex items-center justify-between px-6 py-3 border-t">
              <div className="text-sm text-zinc-600">
                Selected: <span className="font-semibold">{selectedIds.length}</span> of {approved.length}
              </div>
              <Button 
                variant="ghost" 
                size="sm"
                onClick={clearSelection} 
                disabled={!selectedIds.length}
              >
                Clear selection
              </Button>
            </div>
          )}
        </Card>
      </div>
    </>
  );
}