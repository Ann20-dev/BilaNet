import { useEffect, useState } from "react";
import { api, API_URL, IS_DESKTOP } from "./api";
import { I18nProvider, LOCALES, STABLE_REPLY_LANGUAGES, useI18n } from "./i18n";
import type { StringKey } from "./i18n/en";
import { ChatTab } from "./tabs/ChatTab";
import { CodeTab, type CodeMode } from "./tabs/CodeTab";
import { DocsTab } from "./tabs/DocsTab";
import { QuizTab } from "./tabs/QuizTab";
import { ProjectTab } from "./tabs/ProjectTab";
import "./App.css";

type ModelOption = { id: string; name: string; size: number; ram_needed: number; fits: boolean };
type ModelStatus = {
  provider: string;
  model_present?: boolean;
  download?: { state: string; downloaded: number; total: number; error: string | null };
  ram_total?: number;
  disk_free?: number;
  recommended?: string;
  options?: ModelOption[];
};
type Tab = "chat" | CodeMode | "docs" | "quiz" | "project";
const TABS: [Tab, StringKey][] = [
  ["chat", "tabChat"], ["generate", "tabGenerate"], ["explain", "tabExplain"], ["debug", "tabDebug"],
  ["optimize", "tabOptimize"], ["translate", "tabTranslate"], ["docs", "tabDocs"], ["quiz", "tabQuiz"], ["project", "tabProject"],
];
const gb = (n: number) => (n / 1e9).toFixed(2) + " GB";
const gb1 = (n: number) => (n / 1e9).toFixed(1) + " GB";
// Matches the backend's DISK_MARGIN, so the button is disabled exactly when the server would refuse.
const DISK_MARGIN = 300 * 1024 ** 2;

export default function App() {
  return <I18nProvider><Shell /></I18nProvider>;
}

function Shell() {
  const { t, locale, setLocale, replyLanguage, setReplyLanguage } = useI18n();
  const [health, setHealth] = useState(window.__BILANET_BACKEND_ERROR__ ? "failed" : "starting");
  const [model, setModel] = useState<ModelStatus | null>(null);
  const [tab, setTab] = useState<Tab>("chat");
  const [code, setCode] = useState("");
  const [prefill, setPrefill] = useState<{ text: string; n: number }>();
  const [picked, setPicked] = useState<string>();
  const [startError, setStartError] = useState<string>();

  // Keep checking until the backend answers: the desktop backend needs a few seconds to start,
  // and the free online server can take up to a minute to wake up.
  useEffect(() => {
    if (window.__BILANET_BACKEND_ERROR__) return;
    let stopped = false;
    const started = Date.now();
    const check = () => {
      fetch(API_URL + "/api/v1/health").then(r => r.json()).then(d => { if (!stopped) setHealth(d.status === "ok" ? "ok" : "offline"); })
        .catch(() => {
          if (stopped) return;
          setHealth((Date.now() - started) / 1000 < 90 ? "starting" : "offline");
          setTimeout(check, 1500);
        });
    };
    check();
    return () => { stopped = true; };
  }, []);

  const refreshModel = () => api<ModelStatus>("/model/status").then(r => { if (r.ok) setModel(r.data); });
  useEffect(() => { if (health === "ok") refreshModel(); }, [health]);
  const downloading = model?.download?.state === "downloading" || model?.download?.state === "verifying";
  useEffect(() => {
    if (!downloading) return;
    const timer = setInterval(refreshModel, 1000);
    return () => clearInterval(timer);
  }, [downloading]);

  const needsModel = model?.provider === "local" && !model.model_present;
  const choice = model?.options?.find(o => o.id === (picked ?? model.recommended)) ?? model?.options?.[0];
  const diskShort = !!(choice && model?.disk_free && model.disk_free < choice.size + DISK_MARGIN);
  const startDownload = async () => {
    setStartError(undefined);
    const r = await api<{ started: boolean; reason?: string }>("/model/download", { model: choice?.id });
    if (r.ok && !r.data.started && r.data.reason) setStartError(r.data.reason);
    refreshModel();
  };
  const aiDisabled = health !== "ok" || needsModel;
  const statusText = health === "ok" ? t("statusReady")
    : health === "failed" ? `${t("statusFailed")}: ${window.__BILANET_BACKEND_ERROR__}`
    : health === "starting" ? (IS_DESKTOP ? t("statusStarting") : t("statusWaking"))
    : t("statusOffline");

  return (
    <div className="app">
      <header className="top">
        <div className="brand">
          <h1>BilaNet</h1>
          <span className="muted">{t("tagline")}</span>
        </div>
        <div className="status"><span className={"dot " + health} aria-hidden="true" />{statusText}</div>
        <div className="langs">
          <label className="field">{t("uiLanguage")}
            <select value={locale.code} onChange={e => setLocale(e.target.value)}>
              {LOCALES.map(l => <option key={l.code} value={l.code}>{l.name}{l.name !== l.english ? ` (${l.english})` : ""}</option>)}
            </select>
          </label>
          <label className="field" title={t("replyHint")}>{t("replyLanguage")}
            <select value={replyLanguage} onChange={e => setReplyLanguage(e.target.value)}>
              {LOCALES.map(l => (
                <option key={l.code} value={l.code}>
                  {l.name}{STABLE_REPLY_LANGUAGES.includes(l.code) ? "" : ` (${t("experimentalTag")})`}
                </option>
              ))}
            </select>
          </label>
        </div>
      </header>
      {!locale.reviewed && <div className="draft">{t("draftNote")}</div>}
      {!STABLE_REPLY_LANGUAGES.includes(replyLanguage) && (
        <div className="notice experimental" role="status">
          {t("experimentalReply", { lang: LOCALES.find(l => l.code === replyLanguage)?.name ?? replyLanguage })}
        </div>
      )}

      {needsModel && (
        <div className="notice setup">
          <b>{t("setupTitle")}</b>
          <p>{t("setupBody", { size: choice ? gb1(choice.size) : "1–2 GB" })}</p>
          {downloading ? (
            <>
              <progress value={model?.download?.state === "verifying" ? undefined : model?.download?.downloaded ?? 0} max={model?.download?.total || undefined} />
              <p className="muted">{model?.download?.state === "verifying" ? t("verifying")
                : t("downloadProgress", { done: gb(model?.download?.downloaded ?? 0), total: gb(model?.download?.total || choice?.size || 0) })}</p>
            </>
          ) : (
            <>
              {!!model?.ram_total && (
                <p className="muted">{t("laptopInfo", { ram: gb1(model.ram_total), disk: model.disk_free ? gb1(model.disk_free) : "?" })}</p>
              )}
              {model?.options && model.options.length > 1 && (
                <fieldset className="model-choice">
                  <legend>{t("chooseModel")}</legend>
                  {model.options.map(o => (
                    <label key={o.id} className="model-option">
                      <input type="radio" name="model" value={o.id} checked={choice?.id === o.id} onChange={() => setPicked(o.id)} />
                      <span>
                        <b>{t(o.id === "small" ? "modelSmall" : "modelStandard")}</b>
                        <span className="muted"> · {o.name} · {gb1(o.size)}</span>
                        {o.id === model.recommended && <span className="tag">{t("recommendedTag")}</span>}
                        {!o.fits && <span className="warn-text"> {t("modelTooBig")}</span>}
                      </span>
                    </label>
                  ))}
                </fieldset>
              )}
              {diskShort && choice && <p className="error-text">{t("diskTooSmall", { size: gb1(choice.size + DISK_MARGIN) })}</p>}
              {startError && <p className="error-text">{startError}</p>}
              {model?.download?.state === "error" && <p className="error-text">{t("downloadStopped", { error: model.download.error ?? "" })}</p>}
              <button className="primary" disabled={diskShort} onClick={startDownload}>
                {model?.download?.state === "error" ? t("resumeDownload") : t("downloadModel")}
              </button>
              <p className="muted">{t("lowMemoryTip")}</p>
            </>
          )}
        </div>
      )}

      <nav className="tabs" role="tablist">
        {TABS.map(([id, key]) => (
          <button key={id} role="tab" aria-selected={tab === id} className={tab === id ? "active" : ""} onClick={() => setTab(id)}>{t(key)}</button>
        ))}
      </nav>

      {/* Tabs stay mounted (just hidden) so switching does not lose what you typed. */}
      <main>
        <div hidden={tab !== "chat"}><ChatTab disabled={aiDisabled} prefill={prefill} /></div>
        {(["generate", "explain", "debug", "optimize", "translate"] as CodeMode[]).map(m => (
          <div key={m} hidden={tab !== m}><CodeTab mode={m} disabled={aiDisabled} code={code} setCode={setCode} /></div>
        ))}
        <div hidden={tab !== "docs"}><DocsTab ready={health === "ok"} onAsk={q => { setPrefill({ text: q, n: Date.now() }); setTab("chat"); }} /></div>
        <div hidden={tab !== "quiz"}><QuizTab ready={health === "ok"} disabled={aiDisabled} /></div>
        <div hidden={tab !== "project"}><ProjectTab ready={health === "ok"} disabled={aiDisabled} /></div>
      </main>
    </div>
  );
}
