import { act, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { TranslatorView } from "./TranslatorView";

class MockWebSocket {
  static OPEN = 1;
  readyState = 0;
  onopen: (() => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: (() => void) | null = null;
  onmessage: ((event: MessageEvent<string>) => void) | null = null;

  constructor(public url: string) {
    lastInstance = this;
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN;
      this.onopen?.();
    }, 0);
  }

  send(): void {}
  close(): void {
    this.onclose?.();
  }
}

let lastInstance: MockWebSocket | null = null;

describe("TranslatorView", () => {
  beforeEach(() => {
    lastInstance = null;
    vi.stubGlobal("WebSocket", MockWebSocket);
    vi.stubGlobal("navigator", { mediaDevices: { getUserMedia: vi.fn() } });
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("no backend in this test")));
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows the WebSocket connecting then open status", async () => {
    render(<TranslatorView />);

    expect(screen.getByText(/WS: З'єднання/)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText(/WS: З'єднано/)).toBeInTheDocument();
    });
  });

  it("shows live backend error text once a message arrives", async () => {
    render(<TranslatorView />);

    await waitFor(() => expect(lastInstance).not.toBeNull());

    act(() => {
      lastInstance?.onmessage?.({
        data: JSON.stringify({ type: "error", message: "ML pipeline not implemented yet" }),
      } as MessageEvent<string>);
    });

    await waitFor(() => {
      expect(screen.getByText("ML pipeline not implemented yet")).toBeInTheDocument();
    });
  });
});
