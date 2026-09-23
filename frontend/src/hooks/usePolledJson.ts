"use client";

import { useCallback, useSyncExternalStore } from "react";

interface PollEntry {
  data: unknown;
  subscribers: Set<() => void>;
  timer: ReturnType<typeof setInterval>;
}

// One poller per URL, shared by every mounted component that requests it. The
// game page renders both a mobile and a desktop tree, so without this each
// panel would fetch on its own.
const registry = new Map<string, PollEntry>();

function subscribeTo(url: string, intervalMs: number, onChange: () => void): () => void {
  let entry = registry.get(url);
  if (!entry) {
    const subscribers = new Set<() => void>();
    const load = async () => {
      try {
        const res = await fetch(url);
        if (!res.ok) return;
        const json = (await res.json()) as unknown;
        const current = registry.get(url);
        if (!current) return;
        current.data = json;
        subscribers.forEach((cb) => cb());
      } catch {
        /* keep the last good data */
      }
    };
    entry = { data: null, subscribers, timer: setInterval(load, intervalMs) };
    registry.set(url, entry);
    load();
  }

  entry.subscribers.add(onChange);
  return () => {
    const current = registry.get(url);
    if (!current) return;
    current.subscribers.delete(onChange);
    if (current.subscribers.size === 0) {
      clearInterval(current.timer);
      registry.delete(url);
    }
  };
}

export function usePolledJson<T>(url: string | null, intervalMs: number): T | null {
  const subscribe = useCallback(
    (onChange: () => void) => (url ? subscribeTo(url, intervalMs, onChange) : () => {}),
    [url, intervalMs]
  );

  const getSnapshot = useCallback(
    () => (url ? ((registry.get(url)?.data as T | undefined) ?? null) : null),
    [url]
  );

  return useSyncExternalStore(subscribe, getSnapshot, getSnapshot);
}
