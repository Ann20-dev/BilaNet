import { useState, useEffect } from "react";

// In production (Vercel) VITE_API_URL points at the Render backend; locally the Vite proxy handles /api.
const API_URL = (import.meta.env.VITE_API_URL ?? "").replace(/\/$/, "");

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
  const [health, setHealth] = useState("");
  const [loading, setLoading] = useState(false);
  useEffect(() => { fetch(API_URL + "/api/v1/health").then(r=>r.json()).then(d=>setHealth(d.status)).catch(()=>setHealth("offline")); }, []);
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
          <button onClick={gen} disabled={loading}>Generate</button>
          <button onClick={()=>{navigator.clipboard.writeText(code)}}>Copy</button>
          <button onClick={()=>{setCode("");setMsg("");setResp("")}}>Clear</button>
        </div>
      </main>
      <aside style={{width:320,padding:12,borderLeft:"1px solid #ccc",display:"flex",flexDirection:"column"}}>
        <textarea value={msg} onChange={e=>setMsg(e.target.value)} placeholder="Ask the assistant..." rows={4} style={{width:"100%"}} />
        <button onClick={send} disabled={loading} style={{marginTop:8}}>Send</button>
        <pre style={{flex:1,overflow:"auto",marginTop:8,background:"#f5f5f5",padding:8}}>{loading?"...":resp}</pre>
      </aside>
    </div>
  );
}
