"use client";

import { HelpCircle } from "lucide-react";
import dynamic from "next/dynamic";
import { useCallback, useEffect, useRef, useState } from "react";
import { Camera } from "@/components/Camera";
import { SignToSpeech } from "@/components/Illustration";
import { LandmarkIndicator } from "@/components/LandmarkIndicator";
import { TextInput } from "@/components/TextInput";
import { Transcript } from "@/components/Transcript";
import { VoiceInput } from "@/components/VoiceInput";
import { useWebSocket, type WebSocketStatus } from "@/hooks/useWebSocket";
import { ApiError, textToGloss } from "@/lib/api";
import type { TranslationState } from "@/types/translation";

// Three.js alone is ~540 KB -- the single largest dependency in this app.
// Deferred until the browser is idle after first paint instead of blocking
// the rest of the page (camera, WS connection, text input) on it; ssr:
// false because it touches canvas/WebGL, which don't exist on the server.
const Avatar = dynamic(() => import("@/components/Avatar").then((mod) => mod.Avatar), {
  ssr: false,
  loading: () => (
    <div className="flex h-72 items-center justify-center rounded-xl bg-slate-100 text-sm text-slate-400">
      Завантаження 3D-аватара...
    </div>
  ),
});

const WS_STATUS_LABEL: Record<WebSocketStatus, string> = {
  idle: "Не з'єднано",
  connecting: "З'єднання...",
  open: "З'єднано",
  closed: "З'єднання закрито",
  error: "Помилка з'єднання",
};

// Phase 17: non-manual grammar marker label, shown only when detected --
// "NONE" (no face / not yet calibrated / neutral) has no badge at all.
const FACIAL_GRAMMAR_LABEL: Partial<Record<string, string>> = {
  EYEBROWS_RAISED: "Брови підняті (питання «так/ні»)",
  EYEBROWS_FURROWED: "Брови насуплені (питання «хто/що/де»)",
};

export function TranslatorView(): React.ReactElement {
  const { status, lastMessage, landmarksStatus, connect, disconnect, sendFrame } = useWebSocket();
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

  const facialGrammarLabel =
    lastMessage?.type === "prediction" || lastMessage?.type === "final_prediction"
      ? FACIAL_GRAMMAR_LABEL[lastMessage.facial_grammar]
      : undefined;

  return (
    <div className="flex flex-col gap-6">
      <section className="grid items-center gap-6 py-4 sm:grid-cols-[1.1fr_0.9fr] sm:py-8">
        <div className="flex flex-col gap-3">
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            Жест стає словом миттєво
          </h1>
          <p className="max-w-md text-sm text-slate-500 sm:text-base">
            Камера розпізнає жест української жестової мови й одразу перекладає його на
            граматично коректне речення — а текст і голос перекладає назад у жести.
          </p>
        </div>
        <div className="mx-auto h-44 w-full max-w-sm sm:h-56">
          <SignToSpeech />
        </div>
      </section>

      <div className="grid gap-6 md:grid-cols-2">
        <section className="flex flex-col rounded-2xl border border-slate-200 bg-white p-6">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
            Камера
          </h2>
          <Camera onFrame={sendFrame} />
          <div className="mt-3">
            <LandmarkIndicator status={landmarksStatus} />
          </div>
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
          <div className="flex flex-1 flex-col items-center justify-center gap-2 rounded-xl bg-slate-100 p-4 text-center text-sm text-slate-500">
            <span>{translationText}</span>
            {facialGrammarLabel && (
              <span className="inline-flex items-center gap-1 rounded-full bg-brand-50 px-2 py-0.5 text-xs font-medium text-brand-700">
                <HelpCircle className="h-3 w-3" aria-hidden />
                {facialGrammarLabel}
              </span>
            )}
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
          3D-аватар
        </h2>
        <Avatar glossSequence={avatarGlossSequence} />
      </section>
    </div>
  );
}
