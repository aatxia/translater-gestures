"use client";

import { useEffect } from "react";
import { Camera } from "@/components/Camera";
import { ConnectionStatus } from "@/components/ConnectionStatus";
import { useWebSocket, type WebSocketStatus } from "@/hooks/useWebSocket";

const WS_STATUS_LABEL: Record<WebSocketStatus, string> = {
  idle: "Не з'єднано",
  connecting: "З'єднання...",
  open: "З'єднано",
  closed: "З'єднання закрито",
  error: "Помилка з'єднання",
};

export function TranslatorView(): React.ReactElement {
  const { status, lastMessage, connect, disconnect, sendFrame } = useWebSocket();

  useEffect(() => {
    connect();
    return () => disconnect();
    // Connect once on mount; connect/disconnect identities are stable (useCallback).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const translationText =
    lastMessage?.type === "prediction" || lastMessage?.type === "final_prediction"
      ? lastMessage.text
      : lastMessage?.type === "error"
        ? lastMessage.message
        : "Увімкни камеру, щоб побачити відповідь backend у реальному часі.";

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">Перекладач УЖМ</h1>
        <ConnectionStatus />
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <section className="flex flex-col rounded-2xl border border-slate-200 bg-white p-6">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
            Камера
          </h2>
          <Camera onFrame={sendFrame} />
        </section>

        <section className="flex flex-col rounded-2xl border border-slate-200 bg-white p-6">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
              Переклад
            </h2>
            <span className="text-xs font-medium text-slate-500">
              WS: {WS_STATUS_LABEL[status]}
            </span>
          </div>
          <div className="flex flex-1 items-center justify-center rounded-xl bg-slate-100 p-4 text-center text-sm text-slate-500">
            {translationText}
          </div>
        </section>
      </div>

      <section className="rounded-2xl border border-slate-200 bg-white p-6">
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
          Текст / Голос → Жести
        </h2>
        <div className="flex gap-3">
          <input
            type="text"
            disabled
            placeholder="Введіть текст... (буде активовано в Phase 14)"
            className="flex-1 rounded-lg border border-slate-200 bg-slate-50 px-4 py-2 text-sm text-slate-400 disabled:cursor-not-allowed"
          />
          <button
            type="button"
            disabled
            className="rounded-lg bg-slate-200 px-5 py-2 text-sm font-medium text-slate-400 disabled:cursor-not-allowed"
          >
            Перекласти
          </button>
        </div>
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-6">
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
          3D Avatar
        </h2>
        <div className="flex h-40 items-center justify-center rounded-xl bg-slate-100 text-sm text-slate-400">
          Three.js avatar буде доданий у Phase 15
        </div>
      </section>
    </div>
  );
}
