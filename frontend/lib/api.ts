import type { HealthResponse } from "@/types/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {}

export async function fetchHealth(): Promise<HealthResponse> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}/health`, { cache: "no-store" });
  } catch (cause) {
    throw new ApiError(
      `Не вдалося з'єднатися з backend на ${API_URL}. Переконайся, що ` +
        `\`uvicorn app.main:app --reload\` запущено.`,
      { cause },
    );
  }

  if (!response.ok) {
    throw new ApiError(`Backend health check failed: HTTP ${response.status}`);
  }

  return (await response.json()) as HealthResponse;
}
