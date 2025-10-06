// portal/frontend/app/page.tsx
"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardFooter } from "@/components/ui/card";
import LinkedInAppSettings from "@/components/LinkedInAppSettings";

const API_BASE =
  (process.env.NEXT_PUBLIC_API_BASE || "").replace(/\/+$/, "") ||
  "http://localhost:8001";

export default function HomePage() {
  const loginUrl = `${API_BASE}/auth/linkedin/login?include_org=true`;

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* HERO */}
      <section className="rounded-2xl border border-zinc-200 bg-white p-8">
        <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
          <div className="max-w-2xl">
            <h1 className="text-3xl font-semibold tracking-tight">
              Content Validation & Publishing Portal
            </h1>
            <p className="mt-2 text-zinc-600">
              Generate, validate, approve, and publish high-quality LinkedIn posts to your
              profile or company page—backed by a clean workflow and audit trail.
            </p>
            <div className="mt-4 flex flex-wrap items-center gap-3">
              <a href={loginUrl}>
                <Button>Connect LinkedIn</Button>
              </a>
              <a href="/dashboard">
                <Button variant="outline">Go to Dashboard</Button>
              </a>
              <a href="/approved">
                <Button variant="ghost">View Approved Queue</Button>
              </a>
            </div>
          </div>
          <ul className="grid w-full gap-3 sm:grid-cols-2 md:max-w-sm">
            <li className="rounded-xl border border-zinc-200 p-4">
              <div className="text-sm font-medium">End-to-End Flow</div>
              <div className="text-xs text-zinc-600">
                Draft → Validate → Approve → Publish (Member/Org)
              </div>
            </li>
            <li className="rounded-xl border border-zinc-200 p-4">
              <div className="text-sm font-medium">Org Posting</div>
              <div className="text-xs text-zinc-600">
                Supports <span className="font-medium">w_organization_social</span>
              </div>
            </li>
            <li className="rounded-xl border border-zinc-200 p-4">
              <div className="text-sm font-medium">Batch Pipeline</div>
              <div className="text-xs text-zinc-600">
                Generate & stash approved content in one click
              </div>
            </li>
            <li className="rounded-xl border border-zinc-200 p-4">
              <div className="text-sm font-medium">Audit Friendly</div>
              <div className="text-xs text-zinc-600">
                Tracks statuses, errors, and LinkedIn IDs
              </div>
            </li>
          </ul>
        </div>
      </section>

      {/* BYO LinkedIn App settings (so you don't need server envs) */}
      <LinkedInAppSettings />

      {/* HOW IT WORKS */}
      <section className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader
            title="1) Connect"
            description="Sign in with LinkedIn using your app’s credentials and scopes."
          />
          <CardContent className="text-sm text-zinc-600">
            The portal supports both member and organization posting. You can add your
            app credentials below without redeploying.
          </CardContent>
          <CardFooter>
            <a href={loginUrl}>
              <Button variant="secondary">Connect LinkedIn</Button>
            </a>
          </CardFooter>
        </Card>

        <Card>
          <CardHeader
            title="2) Generate"
            description="Run your validation pipeline to produce approved posts."
          />
          <CardContent className="text-sm text-zinc-600">
            Head to the Dashboard to run the batch. Approved items land in the queue
            ready for publishing or drafting.
          </CardContent>
          <CardFooter>
            <a href="/dashboard">
              <Button variant="outline">Open Dashboard</Button>
            </a>
          </CardFooter>
        </Card>

        <Card>
          <CardHeader
            title="3) Publish"
            description="Publish as member or company page—instantly or as a draft."
          />
          <CardContent className="text-sm text-zinc-600">
            The Approved page lets you select items and publish to member or org, with
            status and LinkedIn post IDs recorded.
          </CardContent>
          <CardFooter>
            <a href="/approved">
              <Button>Go to Approved Queue</Button>
            </a>
          </CardFooter>
        </Card>
      </section>
    </div>
  );
}
