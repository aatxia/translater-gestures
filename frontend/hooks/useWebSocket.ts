"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { FrameMessage, ServerMessage } from "@/types/api";
import type { CapturedFrame } from "@/types/camera";

export type WebSocketStatus = "idle" | "connecting" | "open" | "closed" | "error";

interface UseWebSocketResult {
  status: WebSocketStatus;
  lastMessage: ServerMessage | null;
  connect: () => void;
  disconnect: () => void;
  sendFrame: (frame: CapturedFrame) => void;
}

const WS_URL = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000/ws";

function isServerMessage(value: unknown): value is ServerMessage {
  return (
    typeof value === "object" &&
    value !== null &&
    "type" in value &&
    typeof (value as { type: unknown }).type === "string"
  );
}

export function useWebSocket(): UseWebSocketResult {
  const socketRef = useRef<WebSocket | null>(null);
  const [status, setStatus] = useState<WebSocketStatus>("idle");
  const [lastMessage, setLastMessage] = useState<ServerMessage | null>(null);

  const connect = useCallback(() => {
    if (socketRef.current && socketRef.current.readyState <= WebSocket.OPEN) {
      return; // already connecting/connected
    }
    if (typeof WebSocket === "undefined") {
      setStatus("error");
      return;
    }

    setStatus("connecting");
    const socket = new WebSocket(WS_URL);
    socketRef.current = socket;

    // React StrictMode (dev only) double-invokes effects: mount -> cleanup -> mount.
    // That closes this exact socket almost immediately while a second one opens.
    // Without this guard, the first socket's belated onclose/onerror would
    // overwrite the status set by the second (current) socket's onopen.
    const isStale = () => socketRef.current !== socket;

    socket.onopen = () => {
      if (isStale()) return;
      setStatus("open");
    };
    socket.onclose = () => {
      if (isStale()) return;
      setStatus("closed");
    };
    socket.onerror = () => {
      if (isStale()) return;
      setStatus("error");
    };
    socket.onmessage = (event: MessageEvent<string>) => {
      if (isStale()) return;
      try {
        const parsed: unknown = JSON.parse(event.data);
        if (isServerMessage(parsed)) {
          setLastMessage(parsed);
        }
      } catch {
        // Malformed message from the server -- ignore rather than crash the UI.
      }
    };
  }, []);

  const disconnect = useCallback(() => {
    socketRef.current?.close();
    socketRef.current = null;
    setStatus("closed");
  }, []);

  const sendFrame = useCallback((frame: CapturedFrame) => {
    const socket = socketRef.current;
    if (!socket || socket.readyState !== WebSocket.OPEN) return;

    const message: FrameMessage = {
      type: "frame",
      timestamp: frame.timestamp,
      data: frame.dataUrl,
    };
    socket.send(JSON.stringify(message));
  }, []);

  useEffect(() => {
    return () => {
      socketRef.current?.close();
    };
  }, []);

  return { status, lastMessage, connect, disconnect, sendFrame };
}
