"use client";

import { useCamera } from "@/hooks/useCamera";
import type { CapturedFrame } from "@/types/camera";

const STATUS_LABEL: Record<string, string> = {
  idle: "Не запущено",
  requesting_permission: "Очікую дозвіл...",
  streaming: "Активна",
  stopped: "Зупинено",
  error: "Помилка",
};

interface CameraProps {
  /** Called at the configured FPS while streaming (see useCamera). Optional --
   * omit for a plain preview-only camera (e.g. standalone demo usage). */
  onFrame?: (frame: CapturedFrame) => void;
}

export function Camera({ onFrame }: CameraProps = {}): React.ReactElement {
  const { videoRef, status, error, config, start, stop } = useCamera({ onFrame });

  const isStreaming = status === "streaming";
  const isBusy = status === "requesting_permission";

  return (
    <div className="flex flex-col gap-3">
      <div className="relative flex aspect-video items-center justify-center overflow-hidden rounded-xl bg-slate-900">
        {/* Live camera preview -- no captions applicable to a real-time video feed */}
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className={`h-full w-full object-cover ${isStreaming ? "block" : "hidden"}`}
        />
        {!isStreaming && (
          <p className="px-4 text-center text-sm text-slate-400">
            {status === "error" ? error?.message : "Камера не активна"}
          </p>
        )}
      </div>

      <div className="flex items-center justify-between text-xs text-slate-500">
        <span>
          {config.width}×{config.height} · {config.fps} FPS
        </span>
        <span
          className={
            status === "streaming"
              ? "font-medium text-emerald-600"
              : status === "error"
                ? "font-medium text-red-600"
                : "text-slate-400"
          }
        >
          {STATUS_LABEL[status]}
        </span>
      </div>

      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => void start()}
          disabled={isStreaming || isBusy}
          className="flex-1 rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          Увімкнути камеру
        </button>
        <button
          type="button"
          onClick={stop}
          disabled={!isStreaming}
          className="flex-1 rounded-lg border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:text-slate-300"
        >
          Вимкнути
        </button>
      </div>
    </div>
  );
}
