"use client";

import { useGameStore } from "@/stores/gameStore";
import { Badge } from "@/components/ui/badge";

export function ShoeIndicator() {
  const shoe = useGameStore((s) => s.state.shoe);

  const pct = shoe.total > 0 ? ((shoe.total - shoe.remaining) / shoe.total) * 100 : 0;

  return (
    <div className="flex items-center gap-3 p-3 rounded-lg bg-white/5 border border-white/10">
      <div className="flex flex-col">
        <span className="text-xs text-muted-foreground">Shoe</span>
        <span className="text-sm font-bold">{shoe.remaining}/{shoe.total}</span>
      </div>
      <div className="flex-1 h-2 bg-white/10 rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-green-500 to-yellow-500 transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>
      <div className="flex flex-col items-end">
        <span className="text-xs text-muted-foreground">Count</span>
        <Badge
          variant={shoe.true_count > 0 ? "default" : shoe.true_count < 0 ? "destructive" : "secondary"}
          className={`text-xs ${shoe.true_count > 0 ? "bg-green-700" : ""}`}
        >
          {shoe.true_count > 0 ? "+" : ""}{shoe.true_count}
        </Badge>
      </div>
    </div>
  );
}
