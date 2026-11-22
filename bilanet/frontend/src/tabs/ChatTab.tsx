import { useEffect, useState } from "react";
import { api } from "../api";
import { useI18n } from "../i18n";
import { Output } from "../Answer";

type Turn = { q: string; a: string; sources: { title: string; library: string }[] };

export function ChatTab({ disabled, prefill }: { disabled: boolean; prefill?: { text: string; n: number } }) {
  const { t, replyLanguage } = useI18n();
  const [msg, setMsg] = useState("");
  const [useDocs, setUseDocs] = useState(true);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  // "Ask the AI about this" in the Docs tab fills in the question here.
  useEffect(() => { if (prefill) { setMsg(prefill.text); setUseDocs(true); } }, [prefill]);

  async function send() {
    if (!msg.trim()) return;
    setLoading(true); setError("");
    const res = await api("/chat", { message: msg, use_docs: useDocs, reply_language: replyLanguage });
    setLoading(false);
    if (!res.ok) return setError(res.error);
    setTurns([{ q: msg, a: res.data.response, sources: res.data.sources ?? [] }, ...turns]);
    setMsg("");
  }

  return (
    <section className="panel">
      <textarea value={msg} onChange={e => setMsg(e.target.value)} rows={4} placeholder={t("chatPlaceholder")}
        onKeyDown={e => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) send(); }} />
      <div className="row">
        <label className="check"><input type="checkbox" checked={useDocs} onChange={e => setUseDocs(e.target.checked)} /> {t("useDocs")}</label>
        <button className="primary" onClick={send} disabled={disabled || loading || !msg.trim()}>{t("send")}</button>
      </div>
      <Output loading={loading} text="" error={error} />
      {turns.map((turn, i) => (
        <div key={turns.length - i} className="turn">
          <div className="question" dir="auto">{turn.q}</div>
          <Output loading={false} text={turn.a} />
          {turn.sources.length > 0 && (
            <div className="sources">{t("sources")}: {turn.sources.map(s => <span key={s.title} className="chip" dir="ltr">{s.title}</span>)}</div>
          )}
        </div>
      ))}
    </section>
  );
}
