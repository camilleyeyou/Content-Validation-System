"use client";

import * as React from "react";

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "default" | "secondary" | "outline" | "ghost";
  isLoading?: boolean;
};

export function Button({
  className,
  variant = "default",
  isLoading,
  disabled,
  children,
  ...props
}: ButtonProps) {
  const base =
    "inline-flex items-center justify-center rounded-lg px-4 py-2 text-sm font-medium transition focus:outline-none focus:ring-2 focus:ring-black/10";
  const variants: Record<NonNullable<ButtonProps["variant"]>, string> = {
    default: "bg-black text-white hover:bg-zinc-800",
    secondary: "bg-zinc-900 text-white hover:bg-zinc-800",
    outline: "border border-zinc-300 bg-white hover:bg-zinc-50",
    ghost: "bg-transparent hover:bg-zinc-100",
  };
  return (
    <button
      className={cn(base, variants[variant], className)}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? "…" : children}
    </button>
  );
}

// Exported so other UI bits (e.g., Card) can reuse it.
export function cn(...parts: Array<string | false | null | undefined>) {
  return parts.filter(Boolean).join(" ");
}
