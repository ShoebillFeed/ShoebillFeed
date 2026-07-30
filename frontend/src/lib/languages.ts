export const SHARED_LANGUAGES = [
  { code: "en", label: "English",    native: "English" },
  { code: "de", label: "German",     native: "Deutsch" },
  { code: "fr", label: "French",     native: "Français" },
  { code: "es", label: "Spanish",    native: "Español" },
  { code: "it", label: "Italian",    native: "Italiano" },
  { code: "nl", label: "Dutch",      native: "Nederlands" },
  { code: "pl", label: "Polish",     native: "Polski" },
  { code: "pt", label: "Portuguese", native: "Português" },
  { code: "ro", label: "Romanian",   native: "Română" },
  { code: "ru", label: "Russian",    native: "Русский" },
  { code: "uk", label: "Ukrainian",  native: "Українська" },
  { code: "zh", label: "Chinese",    native: "中文" },
  { code: "ja", label: "Japanese",   native: "日本語" },
  { code: "ko", label: "Korean",     native: "한국어" },
  { code: "tr", label: "Turkish",    native: "Türkçe" },
  { code: "sv", label: "Swedish",    native: "Svenska" },
  { code: "da", label: "Danish",     native: "Dansk" },
  { code: "nb", label: "Norwegian",  native: "Norsk" },
  { code: "fi", label: "Finnish",    native: "Suomi" },
  { code: "cs", label: "Czech",      native: "Čeština" },
  { code: "hu", label: "Hungarian",  native: "Magyar" },
];

export const CONTENT_LANGUAGES = [
  ...SHARED_LANGUAGES,
  { code: "ar", label: "Arabic", native: "العربية" },
];

export const UI_LANGUAGES = SHARED_LANGUAGES;
