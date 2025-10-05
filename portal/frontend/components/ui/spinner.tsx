import { cn } from "../../lib/cn";

export function Spinner({ className }: { className?: string }) {
  return (
    <div className={cn("inline-block h-4 w-4 animate-spin rounded-full border-2 border-neutral-300 border-t-neutral-900", className)} />
  );
}
