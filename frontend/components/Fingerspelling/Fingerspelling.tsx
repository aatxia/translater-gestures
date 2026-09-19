"use client";

import { useEffect, useRef, useState } from "react";
import type { LetterPredictionMessage } from "@/types/api";

interface FingerspellingProps {
  /** Latest letter_prediction/letter_confirmed (backend/websocket/
   * protocol.py) -- a SEPARATE real classifier (ml/fingerspelling/,
   * trained on real photos) from the word-level panel's text, which
   * still comes from the synthetic-only checkpoint. */
  letterMessage: LetterPredictionMessage | null;
}

/** Accumulates confirmed letters into a spelled word, live, as the signer
 * fingerspells -- the only place in the UI backed by a real (not demo)
 * trained model, so it's labeled as such rather than blending in with the
 * "[DEMO]" word-level prediction panel next to it. */
export function Fingerspelling({ letterMessage }: FingerspellingProps): React.ReactElement {
  const [spelledWord, setSpelledWord] = useState("");
  // Guards against React StrictMode's dev-only double-invoked effect
  // appending the same confirmed letter twice -- the backend itself only
  // ever sends one letter_confirmed per real confirmation (ml/inference/
  // aggregator.py's GlossSequenceAggregator dedupes on its own).
  const lastAppendedRef = useRef<LetterPredictionMessage | null>(null);

  useEffect(() => {
    if (!letterMessage || !letterMessage.is_final) return;
    if (lastAppendedRef.current === letterMessage) return;
    lastAppendedRef.current = letterMessage;
    setSpelledWord((current) => current + letterMessage.letter);
  }, [letterMessage]);

  return (
    <div className="flex flex-col gap-2 rounded-xl bg-slate-100 p-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-slate-500">
          Дактиль <span className="font-semibold text-emerald-600">(реальна модель, не демо)</span>
        </span>
        <button
          type="button"
          onClick={() => setSpelledWord("")}
          disabled={spelledWord.length === 0}
          className="text-xs font-medium text-slate-500 hover:text-brand-600 disabled:cursor-not-allowed disabled:text-slate-300"
        >
          Очистити
        </button>
      </div>
      <div className="min-h-8 text-lg font-semibold tracking-wide text-slate-900">
        {spelledWord ? (
          spelledWord
        ) : (
          <span className="text-sm font-normal text-slate-400">Покажи літеру дактилю на камеру...</span>
        )}
        {letterMessage && !letterMessage.is_final && (
          <span className="ml-1 text-slate-400">{letterMessage.letter}?</span>
        )}
      </div>
    </div>
  );
}
