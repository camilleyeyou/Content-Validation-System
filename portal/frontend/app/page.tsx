// portal/frontend/app/page.tsx
"use client";

import * as React from "react";
import { linkedInLoginUrl } from "@/lib/config";
import LinkedInAppSettings from "@/components/LinkedInAppSettings";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

export default function HomePage() {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader
          title="Welcome to LinkedIn Content Portal"
          description="Run your pipeline, approve content, and publish as a member or organization."
          actions={
            <a href={linkedInLoginUrl(true)}>
              <Button>Connect LinkedIn</Button>
            </a>
          }
        />
        <CardContent className="space-y-3">
          <p className="text-sm text-zinc-700">
            Use the <span className="font-medium">Dashboard</span> to generate approved posts,
            then go to <span className="font-medium">Approved</span> to publish them.
          </p>
          <p className="text-xs text-zinc-500">
            Tip: If your app credentials change, update them below, then “Connect LinkedIn” again.
          </p>
        </CardContent>
      </Card>

      {/* App Settings on Home as requested */}
      <LinkedInAppSettings />
    </div>
  );
}
