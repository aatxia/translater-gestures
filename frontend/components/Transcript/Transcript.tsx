"use client";

import { groupGlossesForDisplay } from "@/lib/glossDisplay";
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

  const items = groupGlossesForDisplay(state.glossSequence);

  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap gap-2">
        {items.map((item) => (
          <span
            key={item.key}
            className={`rounded-md px-2 py-1 font-mono text-sm ${
              item.isFingerspell ? "bg-amber-50 text-amber-700" : "bg-brand-50 text-brand-700"
            }`}
          >
            {item.label}
          </span>
        ))}
      </div>
      <p className="text-xs text-slate-400">
        Послідовність gloss для 3D-аватара (Phase 15) нижче. 🔤 позначає дактилологію (Phase
        16, слово поза лексиконом, розкладене по літерах) — аватар не показує окремі літери
        (немає моделі пальців), лише тримає нейтральну позу для таких жестів.
      </p>
    </div>
  );
}
