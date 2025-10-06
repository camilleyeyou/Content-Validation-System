// portal/frontend/app/page.tsx
import Link from "next/link";
import ConnectButton from "@/components/ConnectButton";

export default function Home() {
  return (
    <main className="min-h-[70vh] flex flex-col items-center justify-center gap-6 p-8">
      <h1 className="text-3xl font-semibold">LinkedIn Content Portal</h1>
      <p className="text-zinc-600 max-w-prose text-center">
        Validate, approve and publish LinkedIn content to your profile or company page.
      </p>
      <div className="flex items-center gap-3">
        <ConnectButton />
        <Link
          href="/dashboard"
          className="inline-flex items-center rounded-lg border border-zinc-300 px-4 py-2 hover:bg-zinc-50"
        >
          Go to Dashboard
        </Link>
      </div>
    </main>
  );
}
