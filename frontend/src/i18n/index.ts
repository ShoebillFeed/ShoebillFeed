import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import LanguageDetector from "i18next-browser-languagedetector";
import en from "./en";
import de from "./de";
import fr from "./fr";
import es from "./es";
import it from "./it";
import nl from "./nl";
import pl from "./pl";
import pt from "./pt";
import ro from "./ro";
import ru from "./ru";
import uk from "./uk";

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
      fr: { translation: fr },
      es: { translation: es },
      it: { translation: it },
      nl: { translation: nl },
      pl: { translation: pl },
      pt: { translation: pt },
      ro: { translation: ro },
      ru: { translation: ru },
      uk: { translation: uk },
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
