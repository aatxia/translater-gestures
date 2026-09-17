import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
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

  it("feeds a confirmed camera gloss (final_prediction) into the avatar", async () => {
    render(<TranslatorView />);

    await waitFor(() => expect(lastInstance).not.toBeNull());

    act(() => {
      lastInstance?.onmessage?.({
        data: JSON.stringify({
          type: "final_prediction",
          text: "[DEMO] Так.",
          gloss: "TAK",
          confidence: 0.91,
          is_final: true,
          facial_grammar: "NONE",
        }),
      } as MessageEvent<string>);
    });

    // The live translation panel reflects the confirmed message, confirming
    // it flowed through useWebSocket -> TranslatorView -> both the panel and
    // the Avatar's glossSequence prop (Avatar itself falls back to an honest
    // "WebGL не підтримується" message in jsdom, which has no real GL
    // context -- the gloss-driven pose is covered by
    // components/Avatar/player.test.ts, not re-tested here). Avatar is
    // next/dynamic-loaded (ssr: false), so it briefly shows a loading
    // placeholder before this resolves -- worth its own waitFor.
    await waitFor(() => {
      expect(screen.getByText("[DEMO] Так.")).toBeInTheDocument();
    });
    await waitFor(() => {
      expect(screen.getByText(/WebGL не підтримується/)).toBeInTheDocument();
    });
    expect(screen.queryByText(/Брови/)).not.toBeInTheDocument();
  });

  it("shows a question-marker badge (Phase 17) when eyebrows are raised", async () => {
    render(<TranslatorView />);

    await waitFor(() => expect(lastInstance).not.toBeNull());

    act(() => {
      lastInstance?.onmessage?.({
        data: JSON.stringify({
          type: "final_prediction",
          text: "[DEMO] Так?",
          gloss: "TAK",
          confidence: 0.91,
          is_final: true,
          facial_grammar: "EYEBROWS_RAISED",
        }),
      } as MessageEvent<string>);
    });

    await waitFor(() => {
      expect(screen.getByText(/Брови підняті/)).toBeInTheDocument();
    });
  });

  it("translates typed text into a real Ukrainian sentence via the Phase 14 API, never the internal gloss codes", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) => {
        if (url.toString().endsWith("/translate/text-to-gloss")) {
          return {
            ok: true,
            json: async () => ({
              gloss_sequence: ["I", "WANT", "WATER"],
              gloss_labels: [
                { text: "Я", is_fingerspell: false },
                { text: "хотіти", is_fingerspell: false },
                { text: "вода", is_fingerspell: false },
              ],
              composed_text: "Я хочу води.",
            }),
          };
        }
        throw new Error("no backend in this test");
      }),
    );
    const user = userEvent.setup();

    render(<TranslatorView />);

    await user.type(screen.getByPlaceholderText(/Введіть текст/), "Я хочу води.");
    await user.click(screen.getByRole("button", { name: "Перекласти" }));

    await waitFor(() => {
      expect(screen.getByText("Я хочу води.")).toBeInTheDocument();
    });
    expect(screen.getByText("хотіти")).toBeInTheDocument();
    expect(screen.getByText("вода")).toBeInTheDocument();
    expect(screen.queryByText("WANT")).not.toBeInTheDocument();
    expect(screen.queryByText("WATER")).not.toBeInTheDocument();
  });
});
