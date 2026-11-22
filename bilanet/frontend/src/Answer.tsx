import { useState } from "react";
import { useI18n } from "./i18n";
import { IS_DESKTOP } from "./api";

// Renders the AI's answer: plain text with ``` fenced code blocks shown as code with a Copy button.
// Deliberately tiny (no markdown library) to keep the app light.
export function Answer({ text }: { text: string }) {
  const parts = text.split(/```[^\n]*\n?/);
  return (
    <div className="answer">
      {parts.map((p, i) => i % 2 === 1
        ? <CodeBlock key={i} code={p.replace(/\n$/, "")} />
        : p.trim() && <p key={i} className="answer-text" dir="auto">{p.trim()}</p>)}
    </div>
  );
}

export function CodeBlock({ code, title }: { code: string; title?: string }) {
  const { t } = useI18n();
  const [copied, setCopied] = useState(false);
  return (
    <div className="code-block">
      <div className="code-bar">
        <span>{title}</span>
        <button className="small" onClick={() => {
          navigator.clipboard?.writeText(code).then(() => { setCopied(true); setTimeout(() => setCopied(false), 1500); }).catch(() => {});
        }}>{copied ? t("copied") : t("copy")}</button>
      </div>
      <pre dir="ltr"><code>{code}</code></pre>
    </div>
  );
}

export function Output({ loading, text, error }: { loading: boolean; text: string; error?: string }) {
  const { t } = useI18n();
  if (loading) return <div className="output muted" aria-live="polite">{t(IS_DESKTOP ? "thinkingFirst" : "thinking")}</div>;
  if (error) return <div className="output error" role="alert">{error}</div>;
  if (!text) return null;
  return <div className="output"><Answer text={text} /></div>;
}
