import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useWebSocket } from "./useWebSocket";

class MockWebSocket {
  static OPEN = 1;
  static CONNECTING = 0;
  static CLOSED = 3;

  readyState = MockWebSocket.CONNECTING;
  onopen: (() => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: (() => void) | null = null;
  onmessage: ((event: MessageEvent<string>) => void) | null = null;
  sentMessages: string[] = [];

  constructor(public url: string) {
    instances.push(this);
  }

  send(data: string): void {
    this.sentMessages.push(data);
  }

  close(): void {
    this.readyState = MockWebSocket.CLOSED;
    this.onclose?.();
  }

  // Test helpers, not part of the real WebSocket API
  simulateOpen(): void {
    this.readyState = MockWebSocket.OPEN;
    this.onopen?.();
  }

  simulateMessage(data: unknown): void {
    this.onmessage?.({ data: JSON.stringify(data) } as MessageEvent<string>);
  }
}

let instances: MockWebSocket[] = [];

describe("useWebSocket", () => {
  beforeEach(() => {
    instances = [];
    vi.stubGlobal("WebSocket", MockWebSocket);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("transitions to 'open' once the socket connects", async () => {
    const { result } = renderHook(() => useWebSocket());

    act(() => {
      result.current.connect();
    });
    expect(result.current.status).toBe("connecting");

    act(() => {
      instances[0]?.simulateOpen();
    });

    await waitFor(() => {
      expect(result.current.status).toBe("open");
    });
  });

  it("stores the last valid server message", async () => {
    const { result } = renderHook(() => useWebSocket());

    act(() => result.current.connect());
    act(() => instances[0]?.simulateOpen());

    act(() => {
      instances[0]?.simulateMessage({
        type: "error",
        message: "Sign-recognition ML pipeline is not implemented yet",
      });
    });

    await waitFor(() => {
      expect(result.current.lastMessage?.type).toBe("error");
    });
  });

  it("ignores malformed (non-JSON) server messages without crashing", async () => {
    const { result } = renderHook(() => useWebSocket());

    act(() => result.current.connect());
    act(() => instances[0]?.simulateOpen());

    act(() => {
      instances[0]?.onmessage?.({ data: "not json" } as MessageEvent<string>);
    });

    expect(result.current.lastMessage).toBeNull();
  });

  it("only sends a frame once the socket is open", async () => {
    const { result } = renderHook(() => useWebSocket());
    const frame = { dataUrl: "data:image/jpeg;base64,AAA", timestamp: 123, width: 640, height: 480 };

    act(() => result.current.connect());
    result.current.sendFrame(frame); // socket still CONNECTING -- must be a no-op
    expect(instances[0]?.sentMessages).toHaveLength(0);

    act(() => instances[0]?.simulateOpen());
    act(() => result.current.sendFrame(frame));

    expect(instances[0]?.sentMessages).toHaveLength(1);
    const sent = JSON.parse(instances[0]!.sentMessages[0]!);
    expect(sent).toEqual({ type: "frame", timestamp: 123, data: frame.dataUrl });
  });

  it("transitions to 'closed' when disconnect() is called", async () => {
    const { result } = renderHook(() => useWebSocket());

    act(() => result.current.connect());
    act(() => instances[0]?.simulateOpen());
    act(() => result.current.disconnect());

    expect(result.current.status).toBe("closed");
  });
});
