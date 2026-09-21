import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center gap-8 p-8">
      <h1 className="text-5xl font-bold tracking-tight">
        TypeSafe<span className="text-green-500">21</span>
      </h1>
      <p className="text-lg text-muted-foreground max-w-md text-center">
        AI-powered Blackjack. Three players, one shoe, zero mercy.
      </p>
      <Link
        href="/game"
        className="px-8 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-colors"
      >
        Play
      </Link>
    </main>
  );
}
