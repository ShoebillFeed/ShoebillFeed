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
import zh from "./zh";
import ja from "./ja";
import ko from "./ko";
import tr from "./tr";
import sv from "./sv";
import da from "./da";
import nb from "./nb";
import fi from "./fi";
import cs from "./cs";
import hu from "./hu";

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
      zh: { translation: zh },
      ja: { translation: ja },
      ko: { translation: ko },
      tr: { translation: tr },
      sv: { translation: sv },
      da: { translation: da },
      nb: { translation: nb },
      fi: { translation: fi },
      cs: { translation: cs },
      hu: { translation: hu },
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
