"use client";

import LinkedInAppSettings from "@/components/LinkedInAppSettings";
import { Button } from "@/components/ui/button";
import { linkedInLoginUrl, getLoginSid } from "@/lib/config";
import { useEffect, useState } from "react";

export default function HomePage() {
  const [sid, setSid] = useState<string | undefined>(undefined);
  useEffect(() => setSid(getLoginSid()), []);
  const href = linkedInLoginUrl(true, sid);

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-zinc-200 p-6">
        <h1 className="text-2xl font-semibold">LinkedIn Content Portal</h1>
        <p className="text-sm text-zinc-600 mt-1">
          Validate, approve and publish LinkedIn content.
        </p>
        <div className="mt-4">
          <a href={href}><Button>Connect LinkedIn</Button></a>
        </div>
      </div>

      <LinkedInAppSettings />
    </div>
  );
}
