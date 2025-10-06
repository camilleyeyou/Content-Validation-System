"use client";

import * as React from "react";
import { cn } from "./button"; // reuse cn

export function Card({
  className,
  children,
}: React.PropsWithChildren<{ className?: string }>) {
  return (
    <div className={cn("rounded-2xl border border-zinc-200 bg-white", className)}>
      {children}
    </div>
  );
}

export function CardHeader({
  title,
  description,
  actions,
  className,
}: {
  title?: React.ReactNode;
  description?: React.ReactNode;
  actions?: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex items-center justify-between gap-3 border-b border-zinc-200 p-4", className)}>
      <div>
        {title ? <div className="text-sm font-medium">{title}</div> : null}
        {description ? <div className="text-xs text-zinc-600">{description}</div> : null}
      </div>
      {actions ? <div className="flex items-center gap-2">{actions}</div> : null}
    </div>
  );
}

export function CardContent({
  className,
  children,
}: React.PropsWithChildren<{ className?: string }>) {
  return <div className={cn("p-4", className)}>{children}</div>;
}

export function CardFooter({
  className,
  children,
}: React.PropsWithChildren<{ className?: string }>) {
  return <div className={cn("border-t border-zinc-200 p-4", className)}>{children}</div>;
}
