import { useState } from "react";
import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import {
  ChevronDown,
  ArrowBigUp,
  ArrowBigDown,
  Bookmark,
  Check,
  Share2,
  Trash2,
  TrendingUp,
  ExternalLink,
  Info,
} from "lucide-react";
import { Accordion } from "./Accordion";

function TechDetails({ children }: { children: ReactNode }) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  return (
    <div className="mt-2.5">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-1.5 text-xs text-indigo-500 dark:text-indigo-400 hover:text-indigo-700 dark:hover:text-indigo-300 transition-colors"
      >
        <ChevronDown
          size={12}
          className={`transition-transform duration-200 ${open ? "rotate-180" : ""}`}
        />
        {t("about.techLabel")}
      </button>
      {open && (
        <div className="mt-2 px-3 py-2.5 rounded-md bg-gray-50 dark:bg-gray-800/60 border border-gray-200 dark:border-gray-700">
          <p className="text-xs text-gray-500 dark:text-gray-400 leading-relaxed">{children}</p>
        </div>
      )}
    </div>
  );
}

export default function AboutPanel() {
  const { t } = useTranslation();

  const steps: { title: string; desc: string; tech: string }[] = [
    { title: t("about.step1"), desc: t("about.step1Desc"), tech: t("about.step1Tech") },
    { title: t("about.step2"), desc: t("about.step2Desc"), tech: t("about.step2Tech") },
    { title: t("about.step3"), desc: t("about.step3Desc"), tech: t("about.step3Tech") },
    { title: t("about.step4"), desc: t("about.step4Desc"), tech: t("about.step4Tech") },
    { title: t("about.step5"), desc: t("about.step5Desc"), tech: t("about.step5Tech") },
  ];

  // Same icons, sizes, and active-state colors as the real article card
  // (see components/feed/NewsCard.tsx) so this is a legend for what you'll
  // actually see, not just a description of it.
  const symbols: { icon: ReactNode; label: string; desc: string }[] = [
    { icon: <ArrowBigUp size={16} className="text-yellow-500" fill="currentColor" />, label: t("about.symbolRelevant"), desc: t("about.symbolRelevantDesc") },
    { icon: <ArrowBigDown size={16} className="text-red-500" fill="currentColor" />, label: t("about.symbolDislike"), desc: t("about.symbolDislikeDesc") },
    { icon: <Bookmark size={16} className="text-indigo-500" fill="currentColor" />, label: t("about.symbolReadLater"), desc: t("about.symbolReadLaterDesc") },
    { icon: <Check size={16} className="text-green-500" />, label: t("about.symbolRead"), desc: t("about.symbolReadDesc") },
    { icon: <Share2 size={16} className="text-gray-500 dark:text-gray-400" />, label: t("about.symbolShare"), desc: t("about.symbolShareDesc") },
    { icon: <Trash2 size={16} className="text-gray-500 dark:text-gray-400" />, label: t("about.symbolDelete"), desc: t("about.symbolDeleteDesc") },
    { icon: <TrendingUp size={16} className="text-gray-500 dark:text-gray-400" />, label: t("about.symbolImpact"), desc: t("about.symbolImpactDesc") },
    { icon: <ExternalLink size={16} className="text-indigo-500" />, label: t("about.symbolExternalLink"), desc: t("about.symbolExternalLinkDesc") },
    { icon: <Info size={16} className="text-gray-500 dark:text-gray-400" />, label: t("about.symbolLlmInfo"), desc: t("about.symbolLlmInfoDesc") },
    { icon: <ChevronDown size={16} className="text-gray-500 dark:text-gray-400" />, label: t("about.symbolExpand"), desc: t("about.symbolExpandDesc") },
  ];

  return (
    <div>
      <Accordion title={t("about.whatTitle")} defaultOpen>
        <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">{t("about.whatBody")}</p>
      </Accordion>

      <Accordion title={t("about.howTitle")}>
        <div className="flex flex-col gap-6">
          {steps.map(({ title, desc, tech }, i) => (
            <div key={i} className="flex gap-4">
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-indigo-100 dark:bg-indigo-900/40 flex items-center justify-center text-xs font-semibold text-indigo-600 dark:text-indigo-400 mt-0.5">
                {i + 1}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-800 dark:text-gray-200">{title}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 leading-relaxed">{desc}</p>
                <TechDetails>{tech}</TechDetails>
              </div>
            </div>
          ))}
        </div>
      </Accordion>

      <Accordion title={t("about.symbolsTitle")}>
        <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">{t("about.symbolsIntro")}</p>
        <div className="flex flex-col gap-4">
          {symbols.map(({ icon, label, desc }, i) => (
            <div key={i} className="flex gap-4">
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center mt-0.5">
                {icon}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-800 dark:text-gray-200">{label}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 leading-relaxed">{desc}</p>
              </div>
            </div>
          ))}

          <div className="flex gap-4">
            <div className="flex-shrink-0 w-6 h-6 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center mt-0.5 text-sm">
              📰
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-800 dark:text-gray-200">{t("about.symbolSourceIcons")}</p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 leading-relaxed">{t("about.symbolSourceIconsDesc")}</p>
            </div>
          </div>

          <div className="flex gap-4">
            <div className="flex-shrink-0 w-6 h-6 rounded-full bg-indigo-500 mt-0.5" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-800 dark:text-gray-200">{t("about.symbolCategoryPill")}</p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 leading-relaxed">{t("about.symbolCategoryPillDesc")}</p>
            </div>
          </div>
        </div>
      </Accordion>
    </div>
  );
}
