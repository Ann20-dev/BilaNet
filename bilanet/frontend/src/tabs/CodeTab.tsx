import { useState } from "react";
import { api, CODE_LANGUAGES } from "../api";
import { useI18n } from "../i18n";
import type { StringKey } from "../i18n/en";
import { CodeBlock, Output } from "../Answer";

export type CodeMode = "generate" | "explain" | "debug" | "optimize" | "translate";

// Endpoint and the field of the response that holds the answer, per mode.
const MODES: Record<CodeMode, { path: string; field: string; button: StringKey }> = {
  generate: { path: "/code/generate", field: "code", button: "generate" },
  explain: { path: "/code/explain", field: "explanation", button: "explain" },
  debug: { path: "/code/debug", field: "debug", button: "debug" },
  optimize: { path: "/code/optimize", field: "optimized", button: "optimize" },
  translate: { path: "/code/translate", field: "translated", button: "translate" },
};

// One shared code box across the code tabs, so you can paste once, explain, then debug, then translate.
export function CodeTab({ mode, disabled, code, setCode }: { mode: CodeMode; disabled: boolean; code: string; setCode: (c: string) => void }) {
  const { t, replyLanguage } = useI18n();
  const [lang, setLang] = useState("python");
  const [target, setTarget] = useState("javascript");
  const [description, setDescription] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [out, setOut] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  // Debug (Python): run the code so the AI explains the real error instead of guessing.
  const [runCode, setRunCode] = useState(true);
  const [ran, setRan] = useState<{ error: string | null; output: string } | null>(null);
  const m = MODES[mode];
  const ready = mode === "generate" ? description.trim() : code.trim();

  async function run() {
    setLoading(true); setError("");
    const res = await api(m.path, {
      code, language: lang, description, target_language: target,
      error: errorMsg || null, reply_language: replyLanguage, run_code: runCode,
    });
    setLoading(false);
    if (mode === "debug") setRan(res.ok ? res.data.run ?? null : null);
    if (res.ok) setOut({ ...out, [mode]: res.data[m.field] });
    else setError(res.error);
  }

  const langSelect = (value: string, set: (v: string) => void, label: string) => (
    <label className="field">{label}
      <select value={value} onChange={e => set(e.target.value)}>
        {CODE_LANGUAGES.map(([id, name]) => <option key={id} value={id}>{name}</option>)}
      </select>
    </label>
  );

  return (
    <section className="panel">
      <div className="row wrap">
        {langSelect(lang, setLang, mode === "translate" ? t("from") : t("programmingLanguage"))}
        {mode === "translate" && langSelect(target, setTarget, t("to"))}
      </div>
      {mode === "generate"
        ? <textarea value={description} onChange={e => setDescription(e.target.value)} rows={4} placeholder={t("describePlaceholder")} />
        : <textarea className="code" dir="ltr" spellCheck={false} value={code} onChange={e => setCode(e.target.value)} rows={12} placeholder={t("codePlaceholder")} />}
      {mode === "debug" && (
        <textarea className="code" dir="ltr" spellCheck={false} value={errorMsg} onChange={e => setErrorMsg(e.target.value)} rows={2} placeholder={t("errorPlaceholder")} />
      )}
      {mode === "debug" && lang === "python" && (
        <label className="check">
          <input type="checkbox" checked={runCode} onChange={e => setRunCode(e.target.checked)} />
          {t("runCode")}
        </label>
      )}
      <div className="row">
        <button className="primary" onClick={run} disabled={disabled || loading || !ready}>{t(m.button)}</button>
        <button onClick={() => { setCode(""); setDescription(""); setErrorMsg(""); setOut({ ...out, [mode]: "" }); setError(""); if (mode === "debug") setRan(null); }}>{t("clear")}</button>
      </div>
      {mode === "debug" && ran && !loading && (
        ran.error
          ? <CodeBlock title={t("realError")} code={ran.error} />
          : <CodeBlock title={t("ranOk")} code={ran.output.trim() || "—"} />
      )}
      <Output loading={loading} text={out[mode] ?? ""} error={error} />
    </section>
  );
}
