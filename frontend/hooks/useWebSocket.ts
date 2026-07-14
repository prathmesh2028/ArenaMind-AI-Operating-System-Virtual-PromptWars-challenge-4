/**
 * Reusable WebSocket connection hook.
 *
 * Manages the common connect → onmessage → reconnect lifecycle that was
 * duplicated across operations, fan, and volunteer page components.
 */
"use client";

import { useState, useEffect, useRef } from "react";
import { WS_BASE_URL } from "../lib/constants";
import type { WsRawEvent } from "../lib/types";

interface UseWebSocketOptions {
  /** JWT token – connection is deferred until this is truthy. */
  token: string;
  /** Callback invoked with every parsed WebSocket message. */
  onMessage: (event: WsRawEvent) => void;
  /** If true, the WebSocket will not connect (e.g. offline mode). */
  disabled?: boolean;
}

interface UseWebSocketResult {
  /** Whether the WebSocket is currently in the OPEN state. */
  connected: boolean;
}

/**
 * Establishes and manages a WebSocket connection to the dashboard stream.
 *
 * Automatically cleans up on unmount or when `token` / `disabled` changes.
 */
export function useWebSocket({
  token,
  onMessage,
  disabled = false,
}: UseWebSocketOptions): UseWebSocketResult {
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const onMessageRef = useRef(onMessage);

  // Sync onMessage callback ref to prevent stale closures
  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);

  useEffect(() => {
    if (!token || disabled) {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
        setConnected(false);
      }
      return;
    }

    const socket = new WebSocket(`${WS_BASE_URL}/dashboard/ws`);
    wsRef.current = socket;

    socket.onopen = () => {
      setConnected(true);
    };

    socket.onmessage = (event) => {
      try {
        const rawEvent: WsRawEvent = JSON.parse(event.data);
        onMessageRef.current(rawEvent);
      } catch (err) {
        console.error("[WS] Error parsing message:", err);
      }
    };

    socket.onclose = () => {
      setConnected(false);
    };

    return () => {
      socket.close();
      wsRef.current = null;
    };
  }, [token, disabled]);

  return { connected };
}
