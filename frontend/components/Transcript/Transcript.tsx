"use client";

import { CaseSensitive } from "lucide-react";
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
            className={`inline-flex items-center gap-1 rounded-md px-2 py-1 font-mono text-sm ${
              item.isFingerspell
                ? "border border-slate-200 bg-slate-50 text-slate-700"
                : "bg-brand-50 text-brand-700"
            }`}
          >
            {item.isFingerspell && <CaseSensitive className="h-3.5 w-3.5" aria-hidden />}
            {item.label}
          </span>
        ))}
      </div>
      <p className="text-xs text-slate-400">
        Послідовність gloss для 3D-аватара нижче. Позначені літерами чипи — дактилологія (слово
        поза лексиконом, розкладене по літерах).
      </p>
    </div>
  );
}
