import { useEffect, useRef, useState } from "react";
import { api } from "./client";
import { TERMINAL, type JobEvent } from "./types";

export type StreamStatus = "idle" | "connecting" | "open" | "reconnecting" | "closed";

export function useJobEvents(jobId: string | null, onEvent: (event: JobEvent) => void): StreamStatus {
  const [status, setStatus] = useState<StreamStatus>("idle");
  const handler = useRef(onEvent);
  handler.current = onEvent;

  useEffect(() => {
    if (!jobId) {
      setStatus("idle");
      return;
    }
    setStatus("connecting");
    const source = new EventSource(api.eventsUrl(jobId));
    source.onopen = () => setStatus("open");
    source.onerror = () => setStatus(source.readyState === EventSource.CLOSED ? "closed" : "reconnecting");
    source.onmessage = (message) => {
      const event = JSON.parse(message.data) as JobEvent;
      handler.current(event);
      if (TERMINAL.includes(event.type)) {
        source.close();
        setStatus("closed");
      }
    };
    return () => source.close();
  }, [jobId]);

  return status;
}
