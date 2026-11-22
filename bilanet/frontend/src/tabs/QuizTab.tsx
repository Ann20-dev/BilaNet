import { useState } from "react";
import { api, CODE_LANGUAGES } from "../api";
import { useI18n } from "../i18n";
import { CodeBlock, Output } from "../Answer";

type Question = { id: string; topic: string; level: string; question: string; code?: string; options: string[]; answer: number; explanation: string };
const TOPICS = ["python", "pandas", "numpy", "javascript", "sql", "html", "java", "cpp", "general"];
const TOPIC_NAMES: Record<string, string> = { python: "Python", pandas: "pandas", numpy: "NumPy", javascript: "JavaScript", sql: "SQL", html: "HTML/CSS", java: "Java", cpp: "C++", general: "General" };
const LEVELS = ["beginner", "intermediate", "advanced"] as const;

export function QuizTab({ ready, disabled }: { ready: boolean; disabled: boolean }) {
  const { t } = useI18n();
  const [mode, setMode] = useState<"builtin" | "ai">("builtin");
  const [topic, setTopic] = useState("python");
  const [level, setLevel] = useState<(typeof LEVELS)[number]>("beginner");

  const pickers = (
    <div className="row wrap">
      <label className="field">{t("topic")}
        <select value={topic} onChange={e => setTopic(e.target.value)}>
          {TOPICS.map(x => <option key={x} value={x}>{TOPIC_NAMES[x]}</option>)}
        </select>
      </label>
      <label className="field">{t("level")}
        <select value={level} onChange={e => setLevel(e.target.value as typeof level)}>
          {LEVELS.map(l => <option key={l} value={l}>{t(l)}</option>)}
        </select>
      </label>
    </div>
  );

  return (
    <section className="panel">
      <div className="segmented" role="group">
        <button className={mode === "builtin" ? "active" : ""} onClick={() => setMode("builtin")}>{t("quizBuiltIn")}</button>
        <button className={mode === "ai" ? "active" : ""} onClick={() => setMode("ai")}>{t("quizAI")}</button>
      </div>
      {pickers}
      {mode === "builtin" ? <BuiltInQuiz topic={topic} level={level} ready={ready} /> : <AiChallenge topic={topic} level={level} disabled={disabled} />}
    </section>
  );
}

// Multiple-choice questions bundled with the app: instant, no AI model needed.
function BuiltInQuiz({ topic, level, ready }: { topic: string; level: string; ready: boolean }) {
  const { t } = useI18n();
  const [qs, setQs] = useState<Question[]>([]);
  const [i, setI] = useState(0);
  const [picked, setPicked] = useState<number | null>(null);
  const [score, setScore] = useState(0);
  const [error, setError] = useState("");

  async function start() {
    setError("");
    // Fall back to all levels for the topic when a level has few questions.
    let res = await api<Question[]>(`/quiz/questions?topic=${topic}&level=${level}&count=10`);
    if (res.ok && res.data.length < 3) res = await api<Question[]>(`/quiz/questions?topic=${topic}&count=10`);
    if (!res.ok) return setError(res.error);
    setQs(res.data); setI(0); setPicked(null); setScore(0);
  }

  const q = qs[i];
  const done = qs.length > 0 && i >= qs.length;
  return (
    <>
      <button className="primary" onClick={start} disabled={!ready}>{t("startQuiz")}</button>
      {error && <div className="output error">{error}</div>}
      {q && (
        <div className="quiz">
          <p className="muted">{i + 1} / {qs.length}</p>
          <p className="quiz-q" dir="ltr">{q.question}</p>
          {q.code && <CodeBlock code={q.code} />}
          <div className="options" dir="ltr">
            {q.options.map((o, k) => (
              <button key={k} disabled={picked !== null}
                className={picked === null ? "" : k === q.answer ? "right" : k === picked ? "wrong" : ""}
                onClick={() => { setPicked(k); if (k === q.answer) setScore(score + 1); }}>
                {o}
              </button>
            ))}
          </div>
          {picked !== null && (
            <div className={"feedback " + (picked === q.answer ? "right" : "wrong")}>
              <b>{picked === q.answer ? t("correct") : t("wrong")}</b> <span dir="ltr">{q.explanation}</span>
              <div><button className="primary" onClick={() => { setI(i + 1); setPicked(null); }}>{t("next")}</button></div>
            </div>
          )}
        </div>
      )}
      {(q || done) && <p className="score">{t("score", { score, total: qs.length })}</p>}
    </>
  );
}

// The AI writes a fresh challenge, then reviews the student's solution.
function AiChallenge({ topic, level, disabled }: { topic: string; level: string; disabled: boolean }) {
  const { t, replyLanguage } = useI18n();
  const [challenge, setChallenge] = useState("");
  const [solution, setSolution] = useState("");
  const [lang, setLang] = useState("python");
  const [feedback, setFeedback] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function newChallenge() {
    setLoading(true); setError(""); setFeedback(""); setSolution("");
    const res = await api("/quiz/challenge", { topic: TOPIC_NAMES[topic] ?? topic, level, reply_language: replyLanguage });
    setLoading(false);
    if (res.ok) setChallenge(res.data.challenge); else setError(res.error);
  }
  async function check() {
    setLoading(true); setError("");
    const res = await api("/quiz/check", { challenge, solution, language: lang, reply_language: replyLanguage });
    setLoading(false);
    if (res.ok) setFeedback(res.data.feedback); else setError(res.error);
  }

  return (
    <>
      <button className="primary" onClick={newChallenge} disabled={disabled || loading}>{t("newChallenge")}</button>
      <Output loading={loading && !challenge} text={challenge} error={challenge ? "" : error} />
      {challenge && (
        <>
          <label className="field">{t("yourSolution")}
            <select value={lang} onChange={e => setLang(e.target.value)}>
              {CODE_LANGUAGES.map(([id, name]) => <option key={id} value={id}>{name}</option>)}
            </select>
          </label>
          <textarea className="code" dir="ltr" spellCheck={false} rows={10} value={solution} onChange={e => setSolution(e.target.value)} />
          <button className="primary" onClick={check} disabled={disabled || loading || !solution.trim()}>{t("checkSolution")}</button>
          <Output loading={loading} text={feedback} error={error} />
        </>
      )}
    </>
  );
}
