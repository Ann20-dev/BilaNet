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

// The online server (Render free plan) sleeps after ~15 minutes without visitors and needs
// up to a minute to start again. While it starts, Render answers without CORS headers, so the
// browser only reports "Failed to fetch" (or a 502/503). Then we wait for it and try again.
const WAKE_STATUSES = [502, 503, 504];
const WAKE_TIMEOUT_MS = 120_000;
const sleep = (ms: number) => new Promise((res) => setTimeout(res, ms));

async function waitForServer(): Promise<boolean> {
  const end = Date.now() + WAKE_TIMEOUT_MS;
  while (Date.now() < end) {
    try {
      const r = await fetch(API_URL + "/api/v1/health", { cache: "no-store" });
      if (r.ok) return true;
    } catch { /* still starting */ }
    await sleep(3000);
  }
  return false;
}

function send(path: string, body?: unknown) {
  return fetch(API_URL + "/api/v1" + path, body === undefined
    ? {}
    : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
}

// Turn a failed request into a message that says what actually went wrong.
export async function api<T = any>(path: string, body?: unknown): Promise<ApiResult<T>> {
  const canWake = !IS_DESKTOP && !!API_URL;
  let r: Response | null = null;
  let reason = "";
  for (let attempt = 0; attempt < 2; attempt++) {
    try {
      r = await send(path, body);
      if (!(canWake && attempt === 0 && WAKE_STATUSES.includes(r.status))) break;
    } catch (e) {
      // fetch only throws when no response arrived: offline, DNS, CORS block, or blocked by an extension.
      r = null;
      reason = e instanceof Error ? e.message : String(e);
      if (!canWake || attempt === 1) break;
    }
    if (!(await waitForServer())) break;
  }
  if (!r) {
    if (typeof navigator !== "undefined" && navigator.onLine === false) {
      return { ok: false, error: "You are offline. Connect to the internet to use the online demo, or use the desktop app, which works without internet." };
    }
    return { ok: false, error: `Could not reach the BilaNet server at ${API_URL || "this site"} (${reason}). It may still be starting up: please wait a minute and try again. If it keeps failing, a browser extension (like an ad blocker) may be blocking it.` };
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
