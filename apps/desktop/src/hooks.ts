import { useCallback, useEffect, useState } from "react";
import { api } from "./api/client";
import type { Health } from "./api/types";

function read<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key);
    return raw === null ? fallback : (JSON.parse(raw) as T);
  } catch {
    return fallback;
  }
}

export function useStored<T>(key: string, fallback: T): [T, (value: T) => void] {
  const [value, setValue] = useState<T>(() => read(key, fallback));
  const update = useCallback(
    (next: T) => {
      setValue(next);
      try {
        localStorage.setItem(key, JSON.stringify(next));
      } catch {
        return;
      }
    },
    [key],
  );
  return [value, update];
}

export type Connection = "checking" | "ok" | "degraded" | "offline";

export function useConnection(intervalMs = 10000): { connection: Connection; health: Health | null } {
  const [health, setHealth] = useState<Health | null>(null);
  const [connection, setConnection] = useState<Connection>("checking");

  useEffect(() => {
    let alive = true;
    const check = async () => {
      try {
        const result = await api.health();
        if (!alive) return;
        setHealth(result);
        setConnection(result.status === "ok" ? "ok" : "degraded");
      } catch {
        if (alive) setConnection("offline");
      }
    };
    check();
    const timer = window.setInterval(check, intervalMs);
    return () => {
      alive = false;
      window.clearInterval(timer);
    };
  }, [intervalMs]);

  return { connection, health };
}

export function useUiScale(): [number, (value: number) => void] {
  const [scale, setScale] = useStored("cip.scale", 100);
  useEffect(() => {
    document.documentElement.style.setProperty("--ui-scale", `${scale}%`);
  }, [scale]);
  return [scale, (value: number) => setScale(Math.min(130, Math.max(90, value)))];
}

export function useElapsed(running: boolean): string {
  const [start] = useState(() => Date.now());
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (!running) return;
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [running]);
  const seconds = Math.floor((now - start) / 1000);
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
}
