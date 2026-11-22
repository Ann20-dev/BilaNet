import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { en, type StringKey } from "./en";
import { LOCALES, STABLE_REPLY_LANGUAGES, type Locale } from "./locales";

export { LOCALES, STABLE_REPLY_LANGUAGES };

type Ctx = {
  locale: Locale;
  setLocale: (code: string) => void;
  replyLanguage: string;
  setReplyLanguage: (code: string) => void;
  t: (key: StringKey, vars?: Record<string, string | number>) => string;
};

const I18n = createContext<Ctx | null>(null);

// localStorage can throw (private windows, blocked storage); the app must still work.
const load = (k: string) => { try { return localStorage.getItem(k); } catch { return null; } };
const save = (k: string, v: string) => { try { localStorage.setItem(k, v); } catch { /* ignore */ } };

function initialLocale(): string {
  const saved = load("bilanet.ui");
  if (saved && LOCALES.some(l => l.code === saved)) return saved;
  const browser = (navigator.language || "en").slice(0, 2).toLowerCase();
  return LOCALES.some(l => l.code === browser) ? browser : "en";
}

// The language the AI answers in when the user has not picked one: the UI language if the
// model writes it reliably, otherwise French where it is widely read, otherwise English.
const FRENCH_FIRST = ["wo", "ln", "mg"];
function defaultReply(ui: string): string {
  if (STABLE_REPLY_LANGUAGES.includes(ui)) return ui;
  return FRENCH_FIRST.includes(ui) ? "fr" : "en";
}

export function I18nProvider({ children }: { children: ReactNode }) {
  const [code, setCode] = useState(initialLocale);
  // By default the AI answers in the UI language; the user can pick a different one.
  const [reply, setReply] = useState(() => load("bilanet.reply") || defaultReply(code));
  const locale = LOCALES.find(l => l.code === code) ?? LOCALES[0];

  useEffect(() => {
    document.documentElement.lang = locale.code;
    document.documentElement.dir = locale.dir ?? "ltr";
  }, [locale]);

  const value = useMemo<Ctx>(() => ({
    locale,
    setLocale: (c) => {
      setCode(c); save("bilanet.ui", c);
      // Keep the AI language in step unless the user chose one on purpose.
      if (!load("bilanet.reply")) setReply(defaultReply(c));
    },
    replyLanguage: reply,
    setReplyLanguage: (c) => { setReply(c); save("bilanet.reply", c); },
    t: (key, vars) => {
      let s: string = locale.strings[key] ?? en[key];
      if (vars) for (const [k, v] of Object.entries(vars)) s = s.replace(`{${k}}`, String(v));
      return s;
    },
  }), [locale, reply]);

  return <I18n.Provider value={value}>{children}</I18n.Provider>;
}

export function useI18n() {
  const ctx = useContext(I18n);
  if (!ctx) throw new Error("useI18n must be used inside I18nProvider");
  return ctx;
}
