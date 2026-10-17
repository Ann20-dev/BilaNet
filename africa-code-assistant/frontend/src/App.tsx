import { useState, useEffect } from "react";

const LANGS = ["python","javascript","typescript","java","c","cpp","php","html","css","sql","bash"];

export default function App() {
  const [msg, setMsg] = useState("");
  const [code, setCode] = useState("");
  const [lang, setLang] = useState("python");
  const [resp, setResp] = useState("");
  const [health, setHealth] = useState("");
  const [loading, setLoading] = useState(false);
  useEffect(() => { fetch("http://127.0.0.1:8000/api/v1/health").then(r=>r.json()).then(d=>setHealth(d.status)).catch(()=>setHealth("offline")); }, []);
  async function send() {
    setLoading(true);
    try {
      const r = await fetch("http://127.0.0.1:8000/api/v1/chat", { method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({message: msg}) });
      const d = await r.json();
      setResp(r.ok ? d.response : (d.detail || "Request failed"));
    } catch (e) {
      setResp("Backend unavailable");
    }
    setLoading(false);
  }
  async function gen() {
    setLoading(true);
    try {
      const r = await fetch("http://127.0.0.1:8000/api/v1/code/generate", { method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({description: msg, language: lang}) });
      const d = await r.json();
      setCode(r.ok ? d.code : (d.detail || "Request failed"));
    } catch (e) {
      setCode("Backend unavailable");
    }
    setLoading(false);
  }
  return (
    <div style={{display:"flex",height:"100vh",fontFamily:"sans-serif"}}>
      <aside style={{width:220,padding:12,borderRight:"1px solid #ccc"}}>
        <h3>Africa Code Assistant</h3>
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
