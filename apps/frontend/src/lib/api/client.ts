// The only place the frontend talks to the backend (ARCHITECTURE.md: the frontend talks only to the FastAPI API).

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

/** Development only: serve made-up values instead of calling the API. The UI shows a banner while this is on. */
export const USE_SAMPLE_DATA = process.env.NEXT_PUBLIC_USE_SAMPLE_DATA === "true";

export class ApiError extends Error {}

export async function apiGet<T>(path: string): Promise<T> {
  if (USE_SAMPLE_DATA) {
    // Loaded on demand so sample data stays out of the bundle when the flag is off.
    const { sampleResponse } = await import("@/lib/api/sample");
    return sampleResponse(path) as T;
  }

  if (!API_BASE_URL) {
    throw new ApiError("NEXT_PUBLIC_API_BASE_URL is not set, so the dashboard has no API to read from.");
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`);
  } catch {
    throw new ApiError(`Can't reach the Darya API at ${API_BASE_URL}.`);
  }
  if (!response.ok) {
    throw new ApiError(`The Darya API returned ${response.status} for ${path}.`);
  }
  return response.json() as Promise<T>;
}
