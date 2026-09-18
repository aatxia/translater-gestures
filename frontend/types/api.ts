export interface HealthResponse {
  status: string;
  app_env: string;
  model_type: string;
  features: {
    hands: boolean;
    pose: boolean;
    face: boolean;
  };
  ml_pipeline_status: "not_implemented" | "demo_mode" | "ready";
}

// --- WebSocket protocol types (implemented in Phase 5) ---
// Declared now so components built in later phases share one source of truth.

export interface FrameMessage {
  type: "frame";
  timestamp: number;
  data: string; // base64-encoded JPEG
}

/** Non-manual grammar marker (Phase 17): eyebrow position relative to the
 * signer's own calibrated neutral face. "NONE" also covers "no face
 * detected" and "still calibrating" -- see ml/features/facial_grammar.py. */
export type FacialGrammarMarker = "NONE" | "EYEBROWS_RAISED" | "EYEBROWS_FURROWED";

export interface PredictionMessage {
  type: "prediction" | "final_prediction";
  text: string;
  /** Raw predicted sign label for this frame (Phase 15: drives the avatar --
   * only consumed once is_final confirms it, never an interim guess). */
  gloss: string;
  confidence: number;
  is_final: boolean;
  facial_grammar: FacialGrammarMarker;
}

/** A single (x, y) point, image-normalized to [0, 1] in MediaPipe's own
 * frame space (not the centered/scaled coordinates used for ML features) --
 * suitable for drawing directly on the video frame. */
export type LandmarkPoint = [number, number];

/** Real per-frame detection (ml/preprocessing/normalization.py's `present`
 * dict), sent for every processed frame independent of ML readiness --
 * drives the opt-in "is my hand visible" indicator from frame 1. */
export interface LandmarksStatusMessage {
  type: "landmarks_status";
  left_hand: boolean;
  right_hand: boolean;
  pose: boolean;
  face: boolean;
  /** Raw (x, y) points for the overlay (frontend/components/Camera) --
   * null when that modality wasn't detected this frame. Face is
   * intentionally omitted (see backend/websocket/protocol.py). */
  left_hand_points: LandmarkPoint[] | null;
  right_hand_points: LandmarkPoint[] | null;
  pose_points: LandmarkPoint[] | null;
}

export interface ErrorMessage {
  type: "error";
  message: string;
}

export interface ConnectionMessage {
  type: "connection";
  status: "ok" | "closed";
}

export type ServerMessage =
  | PredictionMessage
  | LandmarksStatusMessage
  | ErrorMessage
  | ConnectionMessage;

// --- REST API types (Phase 14) ---

export interface TextToGlossRequest {
  text: string;
}

export interface GlossLabel {
  text: string;
  is_fingerspell: boolean;
}

export interface TextToGlossResponse {
  gloss_sequence: string[];
  /** Ukrainian word/phrase per gloss token -- gloss_sequence's own tokens
   * (e.g. "WANT", "CAR") are internal English identifiers, never meant to
   * be shown to a user. */
  gloss_labels: GlossLabel[];
  /** Full composed Ukrainian sentence, when the sequence matches a
   * supported grammatical pattern; null otherwise (gloss_labels still
   * shows what was understood, word by word). */
  composed_text: string | null;
}
