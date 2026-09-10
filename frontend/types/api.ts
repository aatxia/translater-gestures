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

export interface PredictionMessage {
  type: "prediction" | "final_prediction";
  text: string;
  /** Raw predicted sign label for this frame (Phase 15: drives the avatar --
   * only consumed once is_final confirms it, never an interim guess). */
  gloss: string;
  confidence: number;
  is_final: boolean;
}

export interface ErrorMessage {
  type: "error";
  message: string;
}

export interface ConnectionMessage {
  type: "connection";
  status: "ok" | "closed";
}

export type ServerMessage = PredictionMessage | ErrorMessage | ConnectionMessage;

// --- REST API types (Phase 14) ---

export interface TextToGlossRequest {
  text: string;
}

export interface TextToGlossResponse {
  gloss_sequence: string[];
}
