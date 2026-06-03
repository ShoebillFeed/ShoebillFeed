import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import LanguageDetector from "i18next-browser-languagedetector";
import en from "./en";
import de from "./de";

function getStoredLocale(): string | undefined {
  try {
    const raw = localStorage.getItem("shoebill-feed-prefs");
    if (raw) {
      const parsed = JSON.parse(raw);
      return (parsed?.state?.uiLocale as string) ?? undefined;
    }
  } catch {
    // ignore
  }
  return undefined;
}

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      de: { translation: de },
    },
    lng: getStoredLocale(),
    fallbackLng: "en",
    interpolation: { escapeValue: false },
    detection: {
      order: ["navigator"],
      caches: [],
    },
  });

export default i18n;
