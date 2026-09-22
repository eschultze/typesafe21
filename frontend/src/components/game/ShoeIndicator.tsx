"use client";

import { useGameStore } from "@/stores/gameStore";
import { Badge } from "@/components/ui/badge";

export function ShoeIndicator() {
  const shoe = useGameStore((s) => s.state.shoe);

  const pct = shoe.total > 0 ? ((shoe.total - shoe.remaining) / shoe.total) * 100 : 0;

  return (
    <div className="flex items-center gap-3 p-3 rounded-[10px] bg-card border border-border">
      <div className="flex flex-col">
        <span className="text-xs text-muted-foreground">Shoe</span>
        <span className="text-sm font-bold tabular-nums">{shoe.remaining}/{shoe.total}</span>
      </div>
      <div className="flex-1 h-2 bg-border rounded-full overflow-hidden">
        <div
          className="h-full bg-accent transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>
      <div className="flex flex-col items-end">
        <span className="text-xs text-muted-foreground">Count</span>
        <Badge
          variant={shoe.true_count > 0 ? "default" : shoe.true_count < 0 ? "destructive" : "secondary"}
          className={`text-xs tabular-nums ${shoe.true_count > 0 ? "bg-accent/20 text-accent" : ""}`}
        >
          {shoe.true_count > 0 ? "+" : ""}{shoe.true_count.toFixed(1)}
        </Badge>
      </div>
    </div>
  );
}
