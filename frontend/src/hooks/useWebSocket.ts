import { useEffect, useRef, useState, useCallback } from "react";
import type { ProgressEvent } from "../types";

export function useRunWebSocket(runId: string | null) {
  const [events, setEvents] = useState<ProgressEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!runId) return;

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const url = `${protocol}//${window.location.host}/api/ws/runs/${runId}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (e) => {
      const event: ProgressEvent = JSON.parse(e.data);
      setEvents((prev) => [...prev, event]);
    };

    return () => {
      ws.close();
      setConnected(false);
    };
  }, [runId]);

  const cancel = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "cancel" }));
    }
  }, []);

  const latestEvent = events.length > 0 ? events[events.length - 1] : null;

  return { events, latestEvent, connected, cancel };
}
