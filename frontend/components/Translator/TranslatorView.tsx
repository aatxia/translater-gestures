"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Avatar } from "@/components/Avatar";
import { Camera } from "@/components/Camera";
import { ConnectionStatus } from "@/components/ConnectionStatus";
import { TextInput } from "@/components/TextInput";
import { Transcript } from "@/components/Transcript";
import { VoiceInput } from "@/components/VoiceInput";
import { useWebSocket, type WebSocketStatus } from "@/hooks/useWebSocket";
import { ApiError, textToGloss } from "@/lib/api";
import type { TranslationState } from "@/types/translation";

const WS_STATUS_LABEL: Record<WebSocketStatus, string> = {
  idle: "Не з'єднано",
  connecting: "З'єднання...",
  open: "З'єднано",
  closed: "З'єднання закрито",
  error: "Помилка з'єднання",
};

export function TranslatorView(): React.ReactElement {
  const { status, lastMessage, connect, disconnect, sendFrame } = useWebSocket();
  const [inputText, setInputText] = useState("");
  const [translationState, setTranslationState] = useState<TranslationState>({ status: "idle" });
  // Avatar (Phase 15) is driven by whichever source most recently produced a
  // gloss sequence: a Phase 14 text/voice translation, or a live confirmed
  // sign from the camera (Phase 11's final_prediction, accumulated here).
  const [avatarGlossSequence, setAvatarGlossSequence] = useState<string[]>([]);
  const recognizedGlossesRef = useRef<string[]>([]);

  useEffect(() => {
    connect();
    return () => disconnect();
    // Connect once on mount; connect/disconnect identities are stable (useCallback).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (lastMessage?.type === "final_prediction") {
      recognizedGlossesRef.current = [...recognizedGlossesRef.current, lastMessage.gloss];
      setAvatarGlossSequence(recognizedGlossesRef.current);
    }
  }, [lastMessage]);

  const handleTranslate = useCallback(async (text: string) => {
    setTranslationState({ status: "loading" });
    try {
      const result = await textToGloss(text);
      setTranslationState({ status: "success", glossSequence: result.gloss_sequence });
      setAvatarGlossSequence(result.gloss_sequence);
    } catch (err) {
      setTranslationState({
        status: "error",
        message: err instanceof ApiError ? err.message : "Не вдалося перекласти текст.",
      });
    }
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
        <div className="flex flex-col gap-3">
          <VoiceInput onTranscript={setInputText} />
          <TextInput
            value={inputText}
            onChange={setInputText}
            onSubmit={(text) => void handleTranslate(text)}
            disabled={translationState.status === "loading"}
          />
          <Transcript state={translationState} />
        </div>
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-6">
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
          3D Avatar
        </h2>
        <Avatar glossSequence={avatarGlossSequence} />
      </section>
    </div>
  );
}
