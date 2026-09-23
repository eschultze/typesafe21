"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export function Nav() {
  const pathname = usePathname();
  const isHistory = pathname.startsWith("/history");
  const isGame = pathname.startsWith("/game");

  return (
    <nav className="w-full border-b-2 border-border px-[var(--space-lg)] py-3 flex items-center justify-between">
      <span className="font-bold text-sm tracking-[0.16em] uppercase text-foreground">
        Typesafe 21
      </span>
      <div className="flex items-center gap-6 text-sm text-muted-foreground">
        <Link
          href="/history"
          className={
            isHistory
              ? "text-foreground font-medium hover:text-accent transition-colors"
              : "hover:text-foreground transition-colors"
          }
        >
          History
        </Link>
        <Link
          href="/game"
          className={
            isGame
              ? "text-foreground font-medium hover:text-accent transition-colors"
              : "hover:text-foreground transition-colors"
          }
        >
          Play
        </Link>
      </div>
    </nav>
  );
}
