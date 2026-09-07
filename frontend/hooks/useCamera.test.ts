import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useCamera } from "./useCamera";

function makeFakeStream(): MediaStream {
  const track = { stop: vi.fn(), kind: "video" } as unknown as MediaStreamTrack;
  return {
    getTracks: () => [track],
  } as unknown as MediaStream;
}

describe("useCamera", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("starts streaming when permission is granted", async () => {
    const fakeStream = makeFakeStream();
    const getUserMedia = vi.fn().mockResolvedValue(fakeStream);
    vi.stubGlobal("navigator", { mediaDevices: { getUserMedia } });

    const { result } = renderHook(() => useCamera());

    expect(result.current.status).toBe("idle");

    await act(async () => {
      await result.current.start();
    });

    await waitFor(() => {
      expect(result.current.status).toBe("streaming");
    });
    expect(getUserMedia).toHaveBeenCalledWith(
      expect.objectContaining({ audio: false, video: expect.any(Object) }),
    );
  });

  it("reports permission_denied when getUserMedia rejects with NotAllowedError", async () => {
    const deniedError = Object.assign(new Error("denied"), { name: "NotAllowedError" });
    const getUserMedia = vi.fn().mockRejectedValue(deniedError);
    vi.stubGlobal("navigator", { mediaDevices: { getUserMedia } });

    const { result } = renderHook(() => useCamera());

    await act(async () => {
      await result.current.start();
    });

    await waitFor(() => {
      expect(result.current.status).toBe("error");
    });
    expect(result.current.error?.reason).toBe("permission_denied");
  });

  it("reports unsupported when the browser has no mediaDevices API", async () => {
    vi.stubGlobal("navigator", {});

    const { result } = renderHook(() => useCamera());

    await act(async () => {
      await result.current.start();
    });

    await waitFor(() => {
      expect(result.current.status).toBe("error");
    });
    expect(result.current.error?.reason).toBe("unsupported");
  });

  it("stops all tracks and resets status when stop() is called", async () => {
    const fakeStream = makeFakeStream();
    const getUserMedia = vi.fn().mockResolvedValue(fakeStream);
    vi.stubGlobal("navigator", { mediaDevices: { getUserMedia } });

    const { result } = renderHook(() => useCamera());

    await act(async () => {
      await result.current.start();
    });
    await waitFor(() => expect(result.current.status).toBe("streaming"));

    act(() => {
      result.current.stop();
    });

    expect(result.current.status).toBe("stopped");
    const [track] = fakeStream.getTracks();
    expect(track).toBeDefined();
    expect(track?.stop).toHaveBeenCalled();
  });

  it("clamps configured FPS into the 10-15 range", () => {
    const { result } = renderHook(() => useCamera({ config: { fps: 60 } }));
    expect(result.current.config.fps).toBe(15);
  });
});
