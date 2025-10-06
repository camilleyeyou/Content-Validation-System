"use client";

import ConnectLinkedInButton from "@/components/ConnectLinkedInButton";
import LinkedInAppSettings from "@/components/LinkedInAppSettings";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

export default function HomePage() {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader title="Welcome" description="Validate, approve, and publish LinkedIn content." />
        <CardContent className="flex items-center justify-between">
          <div className="text-sm text-zinc-600">
            Use the button to connect your LinkedIn account. You will be redirected back here.
          </div>
          <ConnectLinkedInButton label="Connect LinkedIn" variant="secondary" />
        </CardContent>
      </Card>

      {/* Allow runtime app credentials configuration */}
      <LinkedInAppSettings />
    </div>
  );
}
