import Link from "next/link";
import { HeroScene } from "@/components/game/HeroScene";

const players = [
  {
    name: "AI",
    strategy: "TypeSafe AI decides everything autonomously",
    bet: "AI-scored, balance-based (% of bankroll)",
    accent: true,
  },
  {
    name: "Basic",
    strategy: "Follows basic strategy (6-deck, dealer stands S17)",
    bet: "Always minimum bet",
    accent: false,
  },
  {
    name: "Random",
    strategy: "Random hit/stand decisions",
    bet: "Random flat bets ($10-$30)",
    accent: false,
  },
];

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col">
      {/* ─── N7 Brutal Slab Nav ─── */}
      <nav className="w-full border-b-2 border-border px-[var(--space-lg)] py-3 flex items-center justify-between">
        <span className="font-bold text-sm tracking-[0.16em] uppercase text-foreground">
          Typesafe 21
        </span>
        <div className="flex items-center gap-6 text-sm text-muted-foreground">
          <Link href="/history" className="hover:text-foreground transition-colors">
            History
          </Link>
          <Link
            href="/game"
            className="text-foreground font-medium hover:text-accent transition-colors"
          >
            Play
          </Link>
        </div>
      </nav>

      {/* ─── Marquee Hero ─── */}
      <section className="flex-1 grid grid-cols-1 lg:grid-cols-[1.2fr_0.8fr] gap-[var(--space-2xl)] items-center px-[var(--space-lg)] md:px-[var(--space-2xl)] py-[var(--space-3xl)] max-w-[76rem] mx-auto w-full">
        <div className="flex flex-col gap-[var(--space-lg)]">
          <h1 className="text-[var(--text-display)] font-light tracking-[var(--tracking-display)] leading-[var(--lh-tight)] text-foreground">
            Typesafe
            <br />
            <span className="text-accent">21</span>
          </h1>
          <p className="text-[var(--text-lg)] text-muted-foreground max-w-[40ch]">
            Three players. One shoe. Zero mercy.
          </p>
          <div className="pt-[var(--space-sm)]">
            <Link
              href="/game"
              className="inline-flex items-center gap-2 text-foreground font-medium text-[var(--text-md)] hover:text-accent transition-colors group"
            >
              Play
              <span className="group-hover:translate-x-1 transition-transform">&rarr;</span>
            </Link>
          </div>
        </div>
        <div className="flex justify-center lg:justify-end">
          <HeroScene />
        </div>
      </section>

      {/* ─── How It Works ─── */}
      <section className="px-[var(--space-lg)] md:px-[var(--space-2xl)] py-[var(--space-3xl)] max-w-[76rem] mx-auto w-full">
        <h2 className="text-[var(--text-display-s)] font-light tracking-[var(--tracking-tight)] text-foreground mb-[var(--space-xl)]">
          How it works
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-[1.2fr_1fr_0.8fr] gap-[var(--space-lg)]">
          {players.map((p) => (
            <div
              key={p.name}
              className={`flex flex-col gap-3 p-[var(--space-lg)] rounded-[10px] border transition-all duration-[var(--dur-short)] ${
                p.accent
                  ? "border-accent/30 bg-accent/5 hover:border-accent/50"
                  : "border-border bg-card hover:border-border/80"
              }`}
            >
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold text-foreground">{p.name}</span>
                {p.accent && (
                  <span className="text-[10px] font-medium tracking-[0.1em] uppercase text-accent">
                    AI
                  </span>
                )}
              </div>
              <p className="text-sm text-muted-foreground leading-relaxed">
                {p.strategy}
              </p>
              <p className="text-xs text-muted-foreground/70">
                Bet: {p.bet}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* ─── AI Primitives ─── */}
      <section className="px-[var(--space-lg)] md:px-[var(--space-2xl)] py-[var(--space-3xl)] max-w-[76rem] mx-auto w-full">
        <h2 className="text-[var(--text-display-s)] font-light tracking-[var(--tracking-tight)] text-foreground mb-[var(--space-xl)]">
          The AI brain
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-[var(--space-lg)]">
          <div className="flex flex-col gap-3 p-[var(--space-lg)] rounded-[10px] border border-border bg-card">
            <span className="text-xs font-medium tracking-[0.16em] uppercase text-accent">
              Choice
            </span>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Hit, stand, double, or split. Structured criteria with what, not_for, and examples for each action. The AI decides autonomously with zero local bias.
            </p>
          </div>
          <div className="flex flex-col gap-3 p-[var(--space-lg)] rounded-[10px] border border-border bg-card">
            <span className="text-xs font-medium tracking-[0.16em] uppercase text-accent">
              Score
            </span>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Bet sizing on a continuous 0-4 spectrum. Maps to balance-based percentages from 5% to 50%. The AI decides the aggressiveness.
            </p>
          </div>
        </div>
      </section>

      {/* ─── Rules ─── */}
      <section className="px-[var(--space-lg)] md:px-[var(--space-2xl)] py-[var(--space-3xl)] max-w-[76rem] mx-auto w-full">
        <h2 className="text-[var(--text-display-s)] font-light tracking-[var(--tracking-tight)] text-foreground mb-[var(--space-xl)]">
          Rules
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-x-[var(--space-xl)] gap-y-[var(--space-sm)] text-sm text-muted-foreground">
          <span>6-deck shoe</span>
          <span>Auto-reshuffle at 25%</span>
          <span>Dealer stands S17</span>
          <span>Blackjack pays 3:2</span>
          <span>Double down allowed</span>
          <span>Split pairs allowed</span>
          <span>Starting balance: $100</span>
          <span>Minimum bet: $10</span>
        </div>
      </section>

      {/* ─── Ft5 Statement Footer ─── */}
      <footer className="px-[var(--space-lg)] md:px-[var(--space-2xl)] py-[var(--space-3xl)] border-t-2 border-border">
        <div className="max-w-[76rem] mx-auto flex flex-col gap-[var(--space-lg)]">
          <p className="text-[var(--text-display-s)] font-light tracking-[var(--tracking-tight)] text-foreground max-w-[38ch]">
            The AI always wins.
            <br />
            Sometimes.
          </p>
          <div className="flex items-center gap-6 text-xs text-muted-foreground">
            <span className="font-medium tracking-[0.16em] uppercase">Typesafe 21</span>
            <Link href="/history" className="hover:text-foreground transition-colors">
              History
            </Link>
            <Link href="/game" className="hover:text-foreground transition-colors">
              Play
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
