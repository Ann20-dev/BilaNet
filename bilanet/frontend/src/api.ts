// Where the backend lives:
// - Desktop app: the Tauri shell starts the bundled backend and injects its address as window.__BILANET_API__.
// - Online demo (Vercel): VITE_API_URL points at the Render backend.
// - Local dev: empty, and the Vite proxy forwards /api.
declare global {
  interface Window { __BILANET_API__?: string; __BILANET_BACKEND_ERROR__?: string }
}
export const IS_DESKTOP = typeof window !== "undefined" && !!window.__BILANET_API__;
export const API_URL = (window.__BILANET_API__ ?? import.meta.env.VITE_API_URL ?? "").replace(/\/$/, "");

export type ApiResult<T = any> = { ok: true; data: T } | { ok: false; error: string };

// Turn a failed request into a message that says what actually went wrong.
export async function api<T = any>(path: string, body?: unknown): Promise<ApiResult<T>> {
  let r: Response;
  try {
    r = await fetch(API_URL + "/api/v1" + path, body === undefined
      ? {}
      : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  } catch (e) {
    // fetch only throws when no response arrived: offline, DNS, CORS block, or blocked by an extension.
    const reason = e instanceof Error ? e.message : String(e);
    return { ok: false, error: `Could not reach the backend at ${API_URL || "this site"} (${reason}). It may be waking up, blocked by CORS, or blocked by a browser extension. Check the browser console (F12) for details.` };
  }
  const text = await r.text();
  let data: any = null;
  try { data = text ? JSON.parse(text) : null; } catch { /* not JSON */ }
  if (!r.ok) {
    let detail = data?.detail;
    if (Array.isArray(detail)) {
      // Pydantic validation errors: show the readable part.
      detail = detail.map((d: any) => d?.msg ?? JSON.stringify(d)).join("; ");
    } else if (detail && typeof detail !== "string") detail = JSON.stringify(detail);
    return { ok: false, error: `Backend error ${r.status}: ${detail || text.slice(0, 200) || r.statusText}` };
  }
  if (data === null) return { ok: false, error: `Backend returned an unexpected response (status ${r.status}): ${text.slice(0, 200)}` };
  return { ok: true, data };
}

export const CODE_LANGUAGES: [string, string][] = [
  ["python", "Python"], ["javascript", "JavaScript"], ["typescript", "TypeScript"], ["java", "Java"],
  ["c", "C"], ["cpp", "C++"], ["csharp", "C#"], ["go", "Go"], ["php", "PHP"], ["sql", "SQL"],
  ["html", "HTML/CSS"], ["rust", "Rust"],
];
