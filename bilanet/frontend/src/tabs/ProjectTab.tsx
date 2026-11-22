import { useEffect, useState } from "react";
import { api } from "../api";
import { useI18n } from "../i18n";
import { CodeBlock, Output } from "../Answer";

type Template = { id: string; name: string };
type TemplateDetail = Template & { tree: string; files: Record<string, string> };
const STACKS = ["Python", "Python + FastAPI", "Python + Flask", "Python + Django", "HTML/CSS/JavaScript", "React", "Node.js + Express", "Java", "C++", "PHP + MySQL", "Android (Kotlin)", "Flutter"];

export function ProjectTab({ ready, disabled }: { ready: boolean; disabled: boolean }) {
  const { t, replyLanguage } = useI18n();
  const [mode, setMode] = useState<"templates" | "ai">("templates");
  const [templates, setTemplates] = useState<Template[]>([]);
  const [detail, setDetail] = useState<TemplateDetail | null>(null);
  const [description, setDescription] = useState("");
  const [stack, setStack] = useState(STACKS[0]);
  const [plan, setPlan] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => { if (ready) api<Template[]>("/project/templates").then(r => { if (r.ok) setTemplates(r.data); }); }, [ready]);

  async function open(id: string) {
    const r = await api<TemplateDetail>(`/project/templates/${id}`);
    if (r.ok) setDetail(r.data); else setError(r.error);
  }
  async function scaffold() {
    setLoading(true); setError("");
    const r = await api("/project/scaffold", { description, stack, reply_language: replyLanguage });
    setLoading(false);
    if (r.ok) setPlan(r.data.plan); else setError(r.error);
  }

  return (
    <section className="panel">
      <div className="segmented" role="group">
        <button className={mode === "templates" ? "active" : ""} onClick={() => setMode("templates")}>{t("projectTemplates")}</button>
        <button className={mode === "ai" ? "active" : ""} onClick={() => setMode("ai")}>{t("projectCustom")}</button>
      </div>
      {mode === "templates" ? (
        <>
          <div className="cards">
            {templates.map(tp => (
              <button key={tp.id} className={"card " + (detail?.id === tp.id ? "active" : "")} onClick={() => open(tp.id)}>{tp.name}</button>
            ))}
          </div>
          {detail && (
            <>
              <CodeBlock code={detail.tree} title={t("files")} />
              {Object.entries(detail.files).filter(([, body]) => body.trim()).map(([path, body]) => (
                <CodeBlock key={path} code={body} title={path} />
              ))}
            </>
          )}
        </>
      ) : (
        <>
          <label className="field">{t("stack")}
            <select value={stack} onChange={e => setStack(e.target.value)}>
              {STACKS.map(s => <option key={s}>{s}</option>)}
            </select>
          </label>
          <textarea rows={4} value={description} onChange={e => setDescription(e.target.value)} placeholder={t("projectDescribe")} />
          <button className="primary" onClick={scaffold} disabled={disabled || loading || !description.trim()}>{t("createPlan")}</button>
          <Output loading={loading} text={plan} error={error} />
        </>
      )}
      {mode === "templates" && error && <div className="output error">{error}</div>}
    </section>
  );
}
