import { useState } from "react";
import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { ChevronDown } from "lucide-react";

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

  return (
    <div>
      <h2 className="font-semibold text-gray-900 dark:text-gray-100 mb-6">{t("about.title")}</h2>

      <section className="mb-8">
        <h3 className="font-medium text-sm text-gray-900 dark:text-gray-100 mb-2">{t("about.whatTitle")}</h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">{t("about.whatBody")}</p>
      </section>

      <section>
        <h3 className="font-medium text-sm text-gray-900 dark:text-gray-100 mb-4">{t("about.howTitle")}</h3>
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
      </section>
    </div>
  );
}
