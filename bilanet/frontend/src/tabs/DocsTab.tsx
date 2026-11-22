import { useEffect, useState } from "react";
import { api } from "../api";
import { useI18n } from "../i18n";
import { CodeBlock } from "../Answer";

type Hit = { title: string; library: string; signature: string; snippet: string; text: string };

// Offline search over Python, NumPy and pandas docs. Works without the AI model.
export function DocsTab({ ready, onAsk }: { ready: boolean; onAsk: (question: string) => void }) {
  const { t } = useI18n();
  const [q, setQ] = useState("");
  const [lib, setLib] = useState("");
  const [hits, setHits] = useState<Hit[] | null>(null);
  const [open, setOpen] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [available, setAvailable] = useState(true);

  useEffect(() => {
    if (ready) api("/documents/info").then(r => { if (r.ok) setAvailable(r.data.builtin_available); });
  }, [ready]);

  async function search() {
    if (!q.trim()) return;
    setError("");
    const res = await api<{ results: Hit[] }>("/documents/search", { query: q, top_k: 10, library: lib || null });
    if (res.ok) { setHits(res.data.results); setOpen(res.data.results[0]?.title ?? null); }
    else setError(res.error);
  }

  return (
    <section className="panel">
      {!available && <div className="notice">{t("docsMissing")}</div>}
      <div className="row">
        <input type="search" value={q} onChange={e => setQ(e.target.value)} placeholder={t("docsPlaceholder")}
          onKeyDown={e => { if (e.key === "Enter") search(); }} />
        <button className="primary" onClick={search} disabled={!ready || !q.trim()}>{t("search")}</button>
      </div>
      <div className="segmented" role="group">
        {[["", t("allLibraries")], ["python", "Python"], ["numpy", "NumPy"], ["pandas", "pandas"]].map(([id, name]) => (
          <button key={id} className={lib === id ? "active" : ""} onClick={() => setLib(id)}>{name}</button>
        ))}
      </div>
      {error && <div className="output error">{error}</div>}
      {hits && hits.length === 0 && <p className="muted">{t("noResults")}</p>}
      <ul className="hits">
        {hits?.map(h => (
          <li key={h.title}>
            <button className="hit-title" dir="ltr" onClick={() => setOpen(open === h.title ? null : h.title)}>
              <span className="chip">{h.library}</span> <b>{h.title}</b><span className="muted">{h.signature}</span>
            </button>
            {open === h.title
              ? <>
                  <CodeBlock code={h.text} title={h.title} />
                  <button className="small" onClick={() => onAsk(`${h.title}: ${q}`)}>{t("askAboutThis")}</button>
                </>
              : <p className="muted snippet" dir="ltr">{h.snippet}</p>}
          </li>
        ))}
      </ul>
    </section>
  );
}
