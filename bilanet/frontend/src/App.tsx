import { useState, useEffect } from "react";

// Where the backend lives:
// - Desktop app: the Tauri shell starts the bundled backend and injects its address as window.__BILANET_API__.
// - Online demo (Vercel): VITE_API_URL points at the Render backend.
// - Local dev: empty, and the Vite proxy forwards /api.
declare global {
  interface Window { __BILANET_API__?: string; __BILANET_BACKEND_ERROR__?: string }
}
const IS_DESKTOP = typeof window !== "undefined" && !!window.__BILANET_API__;
const API_URL = (window.__BILANET_API__ ?? import.meta.env.VITE_API_URL ?? "").replace(/\/$/, "");

type ModelStatus = {
  provider: string;
  model_present?: boolean;
  download?: { state: string; downloaded: number; total: number; error: string | null };
};

const gb = (n: number) => (n / 1e9).toFixed(2) + " GB";

const LANGS = ["python","javascript","typescript","java","c","cpp","php","html","css","sql","bash"];

// Turn a failed request into a message that says what actually went wrong.
async function callApi(path: string, body: unknown): Promise<{ ok: true; data: any } | { ok: false; error: string }> {
  let r: Response;
  try {
    r = await fetch(API_URL + path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  } catch (e) {
    // fetch only throws when no response arrived: offline, DNS, CORS block, or blocked by an extension.
    const reason = e instanceof Error ? e.message : String(e);
    return { ok: false, error: `Could not reach the backend at ${API_URL || "this site"} (${reason}). It may be waking up, blocked by CORS, or blocked by a browser extension. Check the browser console (F12) for details.` };
  }
  const text = await r.text();
  let data: any = null;
  try { data = text ? JSON.parse(text) : null; } catch { /* not JSON */ }
  if (!r.ok) {
    const detail = data?.detail ? (typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail)) : text.slice(0, 200) || r.statusText;
    return { ok: false, error: `Backend error ${r.status}: ${detail}` };
  }
  if (data === null) return { ok: false, error: `Backend returned an unexpected response (status ${r.status}): ${text.slice(0, 200)}` };
  return { ok: true, data };
}

export default function App() {
  const [msg, setMsg] = useState("");
  const [code, setCode] = useState("");
  const [lang, setLang] = useState("python");
  const [resp, setResp] = useState("");
  const [health, setHealth] = useState(() => window.__BILANET_BACKEND_ERROR__ ? "failed to start: " + window.__BILANET_BACKEND_ERROR__ : "");
  const [loading, setLoading] = useState(false);
  const [model, setModel] = useState<ModelStatus | null>(null);

  // Keep checking until the backend answers: the desktop backend needs a few seconds to start,
  // and the free online server can take up to a minute to wake up.
  useEffect(() => {
    if (window.__BILANET_BACKEND_ERROR__) return;
    let stopped = false;
    const started = Date.now();
    const check = () => {
      fetch(API_URL + "/api/v1/health").then(r => r.json()).then(d => { if (!stopped) setHealth(d.status); })
        .catch(() => {
          if (stopped) return;
          const waited = (Date.now() - started) / 1000;
          setHealth(waited < 90 ? (IS_DESKTOP ? "starting…" : "waking up…") : "offline");
          setTimeout(check, 1500);
        });
    };
    check();
    return () => { stopped = true; };
  }, []);

  // Once the backend is up, find out whether the local model still needs downloading.
  useEffect(() => {
    if (health !== "ok") return;
    fetch(API_URL + "/api/v1/model/status").then(r => r.json()).then(setModel).catch(() => {});
  }, [health]);

  const downloading = model?.download?.state === "downloading";
  useEffect(() => {
    if (!downloading) return;
    const t = setInterval(() => {
      fetch(API_URL + "/api/v1/model/status").then(r => r.json()).then(setModel).catch(() => {});
    }, 1000);
    return () => clearInterval(t);
  }, [downloading]);

  async function startDownload() {
    await callApi("/api/v1/model/download", {});
    fetch(API_URL + "/api/v1/model/status").then(r => r.json()).then(setModel).catch(() => {});
  }
  const needsModel = model?.provider === "local" && !model.model_present;
  async function send() {
    setLoading(true);
    const res = await callApi("/api/v1/chat", { message: msg });
    setResp(res.ok ? res.data.response : res.error);
    setLoading(false);
  }
  async function gen() {
    setLoading(true);
    const res = await callApi("/api/v1/code/generate", { description: msg, language: lang });
    setCode(res.ok ? res.data.code : res.error);
    setLoading(false);
  }
  return (
    <div style={{display:"flex",height:"100vh",fontFamily:"sans-serif"}}>
      <aside style={{width:220,padding:12,borderRight:"1px solid #ccc"}}>
        <h3>BilaNet</h3>
        <p>Status: <b>{health}</b></p>
        <label>Language</label>
        <select value={lang} onChange={e=>setLang(e.target.value)} style={{width:"100%"}}>
          {LANGS.map(l=><option key={l}>{l}</option>)}
        </select>
      </aside>
      <main style={{flex:1,display:"flex",flexDirection:"column",padding:12}}>
        <textarea value={code} onChange={e=>setCode(e.target.value)} placeholder="Code editor" style={{flex:1,fontFamily:"monospace",fontSize:14}} />
        <div style={{display:"flex",gap:8,marginTop:8}}>
          <button onClick={gen} disabled={loading || needsModel}>Generate</button>
          <button onClick={()=>{navigator.clipboard.writeText(code)}}>Copy</button>
          <button onClick={()=>{setCode("");setMsg("");setResp("")}}>Clear</button>
        </div>
      </main>
      <aside style={{width:320,padding:12,borderLeft:"1px solid #ccc",display:"flex",flexDirection:"column"}}>
        {needsModel && (
          <div style={{border:"1px solid #c9a227",background:"#fff8e1",color:"#333",padding:10,marginBottom:10,borderRadius:6}}>
            <b>One-time setup</b>
            <p style={{margin:"6px 0"}}>BilaNet needs to download its AI model once (about 2 GB). After that it works fully offline.</p>
            {downloading ? (
              <>
                <progress value={model?.download?.downloaded ?? 0} max={model?.download?.total || undefined} style={{width:"100%"}} />
                <div style={{fontSize:12}}>
                  {gb(model?.download?.downloaded ?? 0)}{model?.download?.total ? " of " + gb(model.download.total) : ""}. You can keep the app open while it downloads.
                </div>
              </>
            ) : (
              <>
                {model?.download?.state === "error" && (
                  <p style={{color:"#b00020",fontSize:12,margin:"6px 0"}}>Download stopped: {model.download.error}. Click again to resume where it left off.</p>
                )}
                <button onClick={startDownload}>{model?.download?.state === "error" ? "Resume download" : "Download AI model"}</button>
              </>
            )}
          </div>
        )}
        <textarea value={msg} onChange={e=>setMsg(e.target.value)} placeholder="Ask the assistant..." rows={4} style={{width:"100%"}} />
        <button onClick={send} disabled={loading || needsModel} style={{marginTop:8}}>Send</button>
        <pre style={{flex:1,overflow:"auto",marginTop:8,background:"#f5f5f5",padding:8,whiteSpace:"pre-wrap"}}>{loading ? (IS_DESKTOP ? "Thinking… (the first answer takes longer while the model loads)" : "Thinking…") : resp}</pre>
      </aside>
    </div>
  );
}
