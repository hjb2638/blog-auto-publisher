import { useEffect, useRef } from 'react';

interface SSEEvent {
  event: string;
  data: Record<string, unknown>;
}

export function useSSE(
  articleId: string | undefined,
  onEvent: (event: SSEEvent) => void,
  enabled: boolean = true,
) {
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;

  useEffect(() => {
    if (!articleId || !enabled) return;

    const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
    const url = `${baseUrl}/articles/${articleId}/stream`;
    const source = new EventSource(url);

    const events = ['section_complete', 'progress', 'status', 'error', 'done'];

    const handler = (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data);
        onEventRef.current({ event: e.type, data });
      } catch { /* ignore parse errors */ }
    };

    for (const evt of events) {
      source.addEventListener(evt, handler);
    }

    source.onerror = () => { /* EventSource auto-reconnects */ };

    return () => source.close();
  }, [articleId, enabled]);
}
