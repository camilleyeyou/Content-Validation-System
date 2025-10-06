// portal/frontend/components/ui/button.tsx
"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

type Variant = "default" | "secondary" | "outline" | "ghost";
type Size = "sm" | "md" | "lg";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  isLoading?: boolean;
}

const variants: Record<Variant, string> = {
  default: "bg-black text-white hover:bg-zinc-800",
  secondary: "bg-zinc-900 text-white hover:bg-zinc-800",
  outline: "border border-zinc-300 bg-white hover:bg-zinc-50",
  ghost: "bg-transparent hover:bg-zinc-100",
};

const sizes: Record<Size, string> = {
  sm: "h-8 px-3 text-sm",
  md: "h-9 px-4 text-sm",
  lg: "h-11 px-5 text-base",
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { className, variant = "default", size = "md", isLoading, children, disabled, ...props },
  ref
) {
  return (
    <button
      ref={ref}
      disabled={isLoading || disabled}
      className={cn(
        "inline-flex items-center justify-center rounded-xl font-medium transition focus:outline-none focus:ring-2 focus:ring-black/10",
        variants[variant],
        sizes[size],
        (isLoading || disabled) && "opacity-60 cursor-not-allowed",
        className
      )}
      {...props}
    >
      {isLoading ? "..." : children}
    </button>
  );
});
