"use client";

import type { TranslationState } from "@/types/translation";

interface TranscriptProps {
  state: TranslationState;
}

export function Transcript({ state }: TranscriptProps): React.ReactElement {
  if (state.status === "idle") {
    return (
      <p className="text-sm text-slate-400">
        Введи текст або скажи щось голосом і натисни «Перекласти».
      </p>
    );
  }

  if (state.status === "loading") {
    return <p className="text-sm text-slate-400">Перекладаю...</p>;
  }

  if (state.status === "error") {
    return <p className="text-sm text-red-600">{state.message}</p>;
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap gap-2">
        {state.glossSequence.map((gloss, index) => (
          <span
            key={`${gloss}-${index}`}
            className="rounded-md bg-brand-50 px-2 py-1 font-mono text-sm text-brand-700"
          >
            {gloss}
          </span>
        ))}
      </div>
      <p className="text-xs text-slate-400">
        Послідовність gloss для аватара — Three.js avatar (Phase 15) ще не реалізований, тут
        лише текстовий результат Phase 14.
      </p>
    </div>
  );
}
