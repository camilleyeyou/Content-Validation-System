import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";

export default function Home() {
  return (
    <main className="grid gap-6 py-8 md:grid-cols-2">
      <Card className="md:col-span-2">
        <CardHeader>
          <CardTitle>Welcome</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-neutral-600">
          Use <strong>Connect LinkedIn</strong> to authenticate, then visit the Dashboard to generate a batch,
          review in <strong>Approved</strong>, and publish manually to your profile or company page.
        </CardContent>
      </Card>
    </main>
  );
}
