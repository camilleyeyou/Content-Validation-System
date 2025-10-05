"use client";

import * as React from "react";

type Variant =
  | "primary"
  | "secondary"
  | "ghost"
  | "outline"
  | "destructive"
  | "link";

type Size = "sm" | "md" | "lg";

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

function cn(...classes: Array<string | false | null | undefined>) {
  return classes.filter(Boolean).join(" ");
}

const base =
  "inline-flex items-center justify-center rounded-xl font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-black/20 disabled:opacity-60 disabled:cursor-not-allowed";

const sizes: Record<Size, string> = {
  sm: "text-sm px-3 py-1.5",
  md: "text-sm px-4 py-2",
  lg: "text-base px-5 py-2.5",
};

const variants: Record<Variant, string> = {
  primary:
    "bg-black text-white hover:bg-zinc-800 shadow-sm active:translate-y-px",
  secondary:
    "bg-zinc-900/5 text-zinc-900 hover:bg-zinc-900/10 shadow-sm active:translate-y-px",
  ghost:
    "bg-transparent hover:bg-zinc-100 text-zinc-900 active:translate-y-px",
  outline:
    "border border-zinc-300 bg-white hover:bg-zinc-50 text-zinc-900 active:translate-y-px",
  destructive:
    "bg-red-600 text-white hover:bg-red-500 shadow-sm active:translate-y-px",
  link: "bg-transparent underline underline-offset-4 hover:opacity-80 px-0 py-0",
};

export function Button({
  className,
  isLoading,
  leftIcon,
  rightIcon,
  size = "md",
  variant = "primary",
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(base, sizes[size], variants[variant], className)}
      disabled={isLoading || props.disabled}
      {...props}
    >
      {leftIcon ? <span className="mr-2">{leftIcon}</span> : null}
      <span className={cn(isLoading && "opacity-80")}>{children}</span>
      {isLoading && (
        <span className="ml-2 inline-block">
          <svg
            className="h-4 w-4 animate-spin"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
              fill="none"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
            />
          </svg>
        </span>
      )}
      {rightIcon ? <span className="ml-2">{rightIcon}</span> : null}
    </button>
  );
}
