// portal/frontend/components/ui/card.tsx
"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

export function Card({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("rounded-2xl border border-zinc-200 bg-white", className)} {...props} />;
}

export function CardHeader({
  title,
  description,
  actions,
  className,
  ...props
}: {
  title?: React.ReactNode;
  description?: React.ReactNode;
  actions?: React.ReactNode;
} & React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("flex items-start justify-between gap-3 px-6 py-4 border-b border-zinc-100", className)} {...props}>
      <div className="min-w-0">
        {title ? <div className="font-medium truncate">{title}</div> : null}
        {description ? <div className="text-sm text-zinc-600">{description}</div> : null}
      </div>
      {actions ? <div className="flex-shrink-0">{actions}</div> : null}
    </div>
  );
}

export function CardContent({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("px-6 py-4", className)} {...props} />;
}

export function CardFooter({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("px-6 py-4 border-t border-zinc-100", className)} {...props} />;
}
