/** UI-only state for the text/voice -> gloss translation flow (Phase 14) --
 * not part of the wire protocol, see types/api.ts TextToGlossResponse for that. */
export type TranslationState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; glossSequence: string[] }
  | { status: "error"; message: string };
